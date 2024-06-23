import boto3
import streamlit as st
from langchain.chains import ConversationChain
from langchain_aws import ChatBedrock
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
from langchain_community.tools import DuckDuckGoSearchRun
from outbound_call import call_phone_number
from contacts import get_all_contacts
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
import random
import time
import json
from duckduckgo_search import DDGS
from langchain_community.tools.you import YouSearchTool
from langchain_community.utilities.you import YouSearchAPIWrapper
from dotenv import load_dotenv
import os

st.title("EventDash")

# Setup bedrock
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)


os.environ["YDC_API_KEY"] = os.getenv("YOUAPIKEY")


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

you_tool = YouSearchTool(api_wrapper=YouSearchAPIWrapper(num_web_results=5))


def generate_final_prompt(prompt, num_results=5):
    system_template = """You are a helpful customer service assistant that aids customers with event-related activities such as finding venues and catering services. Provide accurate and up-to-date information."""

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template)

    agent_prompt = f"""
    {prompt}

    For each service, provide the following details in JSON format:
    - name: string
    - address: string
    - rating: float (1-5 stars)
    - phone: string
    - website: string
    - email: string
    - images: array of strings (up to 2 image URLs)
    - description: string (small description about the service)
    
    Return the top {num_results} results as a list of JSON objects.
    If certain information is not available, use null for that field.
    Nothing other than json should be given
    """

    human_message_prompt = HumanMessagePromptTemplate.from_template(
        agent_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])

    return chat_prompt


def Present(values):
    print(values)
    venues = json.loads(values)
    # Display the results in a formatted way
    st.title("EventDash - Venue Suggestions")

    for venue in venues:
        st.header(venue['name'])
        col1, col2 = st.columns([1, 3])

        with col1:
            # Display the first image (or a placeholder if images are not available)
            if venue['images']:
                st.image(venue['images'][0], width=150)
            else:
                st.image("https://via.placeholder.com/150", width=150)

        with col2:
            st.markdown(f"**Address:** {venue['address']}")
            st.markdown(f"**Rating:** {venue['rating']} ⭐")
            st.markdown(f"**Phone:** {venue['phone']}")
            st.markdown(
                f"**Website:** [{venue['website']}]({venue['website']})")
            st.markdown(f"**Email:** {venue['email']}")
            st.markdown(f"**Description:** {venue['description']}")

            if len(venue['images']) > 1:
                with st.expander("More images"):
                    for image in venue['images'][1:]:
                        st.image(image, width=150)


# Initialize the agent with the custom tool
tools = [generate_random_number_tool,
         get_all_contacts,
         call_phone_number,
         you_tool,
         ]

agent = initialize_agent(
    tools, model.llm, agent_type="zero-shot-react-description", verbose=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # if user_input.lower() in ['exit', 'quit', 'bye']:
    #     print("Customer Service Assistant: Thank you for contacting us. Have a great day!")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        chat_prompt = generate_final_prompt(prompt)
        print(chat_prompt)
        result = agent.run(input=chat_prompt)

        Present(result)

        # # Simulate stream of response with milliseconds delay
        # for chunk in result.split(' '):
        #     full_response += chunk + ' '
        #     if chunk.endswith('\n'):
        #         full_response += ' '
        #     # time.sleep(0.05)
        #     message_placeholder.markdown(full_response + "▌")

        # message_placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})


# NOT USED
# function to get the services list


# def get_services(service_type, city="Berkeley"):
#     """Gives a json about some list of services which are
#     requested, services can be venues, anything in general"""
#     print(service_type, city)
#     results = DDGS().maps(service_type, city=city, max_results=5)
#     # print(results[0])
#     # assert 27 <= len(results) <= 30
#     formatted_results = []
#     for result in results:
#         temp_image = get_image(result.get("title"))
#         formatted_result = {
#             "name": result.get("title"),
#             "address": result.get("address"),
#             "rating": result.get("rating"),
#             "phone": result.get("phone"),
#             "website": result.get("website"),
#             "email": result.get("email"),
#             "images": temp_image
#         }
#         formatted_results.append(formatted_result)

#     # Convert the formatted results to JSON format
#     json_results = json.dumps(formatted_results, indent=4)
#     print(json_results)
#     return json_results


# function to get images
# def get_image(name):
#     results = DDGS().images(name, max_results=2)
#     images = []
#     for result in results:
#         images.append(result["image"])
#     # print(results)
#     return images
