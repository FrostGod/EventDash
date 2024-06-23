import boto3
from langchain import hub
from langchain.agents import Tool, create_react_agent
from langchain_aws import ChatBedrock
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import GoogleSerperAPIWrapper
import os
from typing import TypedDict, Annotated, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
import operator
from langchain_core.agents import AgentFinish
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt import ToolInvocation
from langgraph.graph import END, StateGraph
from langchain_core.agents import AgentActionMessageLog
import streamlit as st

from langchain_community.tools import DuckDuckGoSearchRun

st.set_page_config(page_title="EventDash")

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)


@st.cache_resource
def load_llm():
    llm = ChatBedrock(client=bedrock_runtime,
                      model_id="anthropic.claude-3-5-sonnet-20240620-v1:0")
    model = ConversationChain(llm=llm, verbose=True,
                              memory=ConversationBufferMemory())
    return model


# Define the process_input function before main
def process_input():
    user_input = st.session_state.user_input

    # Add user message to session state and display it immediately
    st.session_state.messages.append(
        {"role": "user", "content": user_input})

    search = DuckDuckGoSearchRun()

    def toggle_case(word):
        toggled_word = ""
        for char in word:
            if char.islower():
                toggled_word += char.upper()
            elif char.isupper():
                toggled_word += char.lower()
            else:
                toggled_word += char
        return toggled_word

    def sort_string(string):
        return ''.join(sorted(string))

    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="useful for when you need to answer questions about current events",
        ),
        Tool(
            name="Toggle_Case",
            func=lambda word: toggle_case(word),
            description="use when you want covert the letter to uppercase or lowercase",
        ),
        Tool(
            name="Sort String",
            func=lambda string: sort_string(string),
            description="use when you want sort a string alphabetically",
        ),
    ]

    prompt = hub.pull("hwchase17/react")

    llm = load_llm().llm
    agent_runnable = create_react_agent(llm, tools, prompt)

    # To maintain internal state, to be used in LangGraph
    class AgentState(TypedDict):
        input: str
        chat_history: list[BaseMessage]
        agent_outcome: Union[AgentAction, AgentFinish, None]
        return_direct: bool
        intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

    tool_executor = ToolExecutor(tools)

    def run_agent(state):
        agent_outcome = agent_runnable.invoke(state)
        return {"agent_outcome": agent_outcome}

    def execute_tools(state):
        messages = [state['agent_outcome']]
        last_message = messages[-1]
        state_action = state['agent_outcome']
        human_key = st.text_input(f"Continue with: {state_action}? [y/n]")
        if human_key == "n":
            raise ValueError

        tool_name = last_message.tool
        arguments = last_message
        if tool_name == "Search" or tool_name == "Sort" or tool_name == "Toggle_Case":
            if "return_direct" in arguments:
                del arguments["return_direct"]
        action = ToolInvocation(
            tool=tool_name,
            tool_input=last_message.tool_input,
        )
        response = tool_executor.invoke(action)
        return {"intermediate_steps": [(state['agent_outcome'], response)]}

    def should_continue(state):
        messages = [state['agent_outcome']]
        last_message = messages[-1]
        if "Action" not in last_message.log:
            return "end"
        else:
            arguments = state["return_direct"]
            if arguments is True:
                return "final"
            else:
                return "continue"

    def first_agent(inputs):
        action = AgentActionMessageLog(
            tool="Search",
            tool_input=inputs["input"],
            log="",
            message_log=[]
        )
        return {"agent_outcome": action}

    # Define Langgraph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", run_agent)
    workflow.add_node("action", execute_tools)
    workflow.add_node("final", execute_tools)
    workflow.set_entry_point("agent")

    workflow.add_conditional_edges("agent",
                                   should_continue,
                                   {
                                       "continue": "action",
                                       "final": "final",
                                       "end": END
                                   })

    workflow.add_edge('action', 'agent')
    workflow.add_edge('final', END)
    app = workflow.compile()

    inputs = {"input": user_input,
              "chat_history": [], "return_direct": False}
    results = []
    for s in app.stream(inputs, {"recursion_limit": 150}):
        result = list(s.values())[0]
        results.append(result)

    # Add assistant message to session state
    full_response = results[-1]['agent_outcome'].return_values['output']
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})

    # Clear the input box after processing
    st.session_state.user_input = ""

    # Rerun to update the chat interface
    st.experimental_rerun()


def main():
    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Streamlit UI elements
    st.title("EventDash")

    # Input from user
    user_input = st.text_area(
        "You:", key="user_input", on_change=process_input)

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])


if __name__ == "__main__":
    main()
