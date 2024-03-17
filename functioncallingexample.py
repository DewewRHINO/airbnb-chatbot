from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

client = OpenAI()
client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_airbnb(location, checkin, checkout, adults):
  url = "https://airbnb13.p.rapidapi.com/search-location"

  querystring = {"location":location, "checkin":checkin,"checkout":checkout,"adults":adults}

  headers = {
    "X-RapidAPI-Key": os.environ.get("X-RapidAPI-Key"),
    "X-RapidAPI-Host": "airbnb13.p.rapidapi.com"
  }

  response = requests.get(url, headers=headers, params=querystring)
  print(response.json()['results'][0])
  return response.json()['results'][0]['url']

def run_conversation():
    # Step 1: send the conversation and available functions to the model
    messages = [{"role": "user", "content": "Find me airbnbs in Whittier, CA that I can check in tomorrow 3/17/2024 and checkout the week after. Only one adult. I want to pay in USD, and show me the first page."}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_airbnb",
                "description": "Get information about airbnbs in that location with specified information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "checkin": {
                            "type": "string",
                            "description": "When the person wants to checkin, e.g. 2023-09-16",
                        },
                        "checkout": {
                            "type": "string",
                            "description": "When the person wants to checkout, e.g. 2023-09-17",
                        },
                        "adults": {
                            "type": "string",
                            "description": "how many adults there are, e.g. 1",
                        }, 
                        "children": {
                            "type": "string",
                            "description": "how many children there are, e.g. 1",
                        },
                        "infants": {
                            "type": "string",
                            "description": "how many infants there are, e.g. 1",
                        }, 
                        "pets": {
                            "type": "string",
                            "description": "how many pets there are, e.g. 1",
                        }, 
                        "page": {
                            "type": "string",
                            "description": "how many pages the user wants, e.g. 1",
                        },
                        "currency": {
                            "type": "string",
                            "description": "currency in which the user wants to pay in, e.g. USD",
                        }
                    },
                    "required": ["location"],
                },
            },
        }
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_airbnb": get_airbnb,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                location=function_args.get("location"),
                checkin=function_args.get("checkin"),
                checkout=function_args.get("checkout"),
                adults=function_args.get("adults")
            )
            
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response

        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response
    
print(run_conversation())