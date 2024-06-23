import boto3
import streamlit as st
from langchain.chains import ConversationChain
from langchain_aws import ChatBedrock
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool, create_react_agent
from langchain.agents import initialize_agent, Tool
from langchain_community.tools import DuckDuckGoSearchRun
import random
import time

st.title("EventDash")

# Setup bedrock
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


model = load_llm()


# Define the tool function
def generate_random_number(*args, **kwargs) -> int:
    """Generate a random number between 0 and 99."""
    number = random.randint(0, 99)
    print(number)
    return number


# Register the tool
generate_random_number_tool = Tool(
    name="generate_random_number",
    func=generate_random_number,
    description="Generate a random number between 0 and 99."
)


search = DuckDuckGoSearchRun()

# Initialize the agent with the custom tool
tools = [generate_random_number_tool,
         Tool(
             name="Search",
             func=search.run,
             description="useful for when you need to answer questions about current events",
         ),
         ]
agent = initialize_agent(
    tools, model.llm, agent_type="zero-shot-react-description")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        result = agent.run(input=prompt)

        # Simulate stream of response with milliseconds delay
        for chunk in result.split(' '):
            full_response += chunk + ' '
            if chunk.endswith('\n'):
                full_response += ' '
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
