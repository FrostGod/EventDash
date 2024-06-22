import requests
from dotenv import load_dotenv
import os
import json
from langchain_community.utilities import YouSearchAPIWrapper
from langchain_community.retrievers.you import YouRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


sample_service = {
   
   "venues":[
   {
      "name": "venue_name",
      "features": [
        "venue_features..."
      ],
      "email<optional>": "venue_host email",
      "location": "Berkeley, CA",
      "pricing<optional>": "Starts at $200 per hour"
    },
    {
       ...
    }
    
    ]
}

sample_query = """
  I'm looking for detailed information on top-rated venues to host an event in Berkeley, CA, 94720. Please provide the following details for each venue:
  Name of the Venue
  Features: Key amenities and unique aspects of the venue.
  Additional Services: Any extra services provided such as tech support, equipment setup, catering, etc.
  Location: Full address of the venue.
  Contact Information: Phone number or email for inquiries.
  Pricing: Cost details if available.
  Capacity: Maximum number of guests the venue can accommodate.
  Format the information in JSON for easy reference. Thank you!
"""



def get_services(location, pincode, servicename, event_desc):
  YOUAPIKEY = os.getenv("YOUAPIKEY")
  os.environ["YDC_API_KEY"] = YOUAPIKEY
  utility = YouSearchAPIWrapper(num_web_results=1)
  query = f"Suggest me 4 venues to host an event at the following location: {location}, {pincode},\
    based on reviews online \
    output format: {sample_service}\
    "

  print(query)
  response = utility.raw_results(query=query)
  # API returns an object with a `hits` key containing a list of hits
  hits = response["hits"]
  # with `num_web_results=1`, `hits` should be len of 1
  print(len(hits))
  print(json.dumps(hits, indent=2))

def smart_search(location, pincode, servicename, event_desc):

  query = f"Suggest me 4 venues to host an event at the following location: {location}, {pincode},\
    based on reviews online\
      output_format: {sample_service}\
    "

  YOUAPIKEY = os.getenv("YOUAPIKEY")
  url = "https://chat-api.you.com/smart"

  payload = {
      "query": query,
      "chat_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a"
  }
  headers = {
      "X-API-Key":  YOUAPIKEY,
      "Content-Type": "application/json"
  }

  response = requests.request("POST", url, json=payload, headers=headers)

  print(response.text) 



def get_ai_snippets_for_query(query):
    YOUAPIKEY = os.getenv("YOUAPIKEY")
    headers = {"X-API-Key": YOUAPIKEY}
    params = {"query": query}
    return requests.get(
        f"https://api.ydc-index.io/search",
        params=params,
        headers=headers,
    ).json()
    
results = get_ai_snippets_for_query("reasons to smile")

# results = query_web_llm("who invented the kaleidoscope?")


def you_search():
  # Replace 'your_api_key' with your actual You.com API key
  api_key = os.getenv("YOUAPIKEY")
  api_url = 'https://api.you.com/gpt40'

  headers = {
      'Authorization': f'Bearer {api_key}',
      'Content-Type': 'application/json'
  }

  data = {
      'prompt': 'Write a short story about a brave knight.',
      'max_tokens': 100,
      'temperature': 0.7,
  }

  response = requests.post(api_url, headers=headers, json=data)
  print(response)

def buildservice():


  os.environ["YDC_API_KEY"] = os.getenv("YOUAPIKEY")
  # For use in Chaining section
  os.environ["OPENAI_API_KEY"] = os.getenv("OPENAIKEY")
  # set up runnable
  runnable = RunnablePassthrough

  # set up retriever, limit sources to one
  retriever = YouRetriever(num_web_results=1)

  # set up model
  model = ChatOpenAI(model="gpt-4o")

  # set up output parser
  output_parser = StrOutputParser()

  # set up prompt that expects one question
prompt = ChatPromptTemplate.from_template(
    """Answer the question based only on the context provided.

Context: {sample_query}

Question: {question}"""
)

# set up chain
chain = (
    runnable.assign(context=(lambda x: x["question"]) | retriever)
    | prompt
    | model
    | output_parser
)

output = chain.invoke({"question": "what is the weather in NY today"})

print(output)

if __name__ == "__main__":
  load_dotenv()
  print("DIVI: testing you.com")

  # you_search("Berkeley, CA", "94720", "event", "Hosting a hackathon")
  buildservice()
  # print(response)




