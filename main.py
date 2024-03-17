import streamlit as st
import openai
import requests
import json

# Set OpenAI API key, in this case we store things in the streamlit environment variables. 
openai.api_key = st.secrets["OPENAI_API_KEY"]

def get_airbnb(location, checkin, checkout, adults):
    """
    Fetches the first Airbnb listing URL based on the provided parameters.

    Parameters:
    - location: The city and state, e.g., "San Francisco, CA".
    - checkin: Check-in date in the format "YYYY-MM-DD".
    - checkout: Check-out date in the format "YYYY-MM-DD".
    - adults: Number of adults.

    Returns:
    - A string containing the first result's URL.
    """

    # Endpoint for API. 
    url = "https://airbnb13.p.rapidapi.com/search-location"
    
    # Query Strings for the API, based on user input. 
    querystring = {"location": location, "checkin": checkin, "checkout": checkout, "adults": adults}
    
    # Headers for the API call, need to set your own Access Key here. 
    headers = {
        "X-RapidAPI-Key": st.secrets["X-RapidAPI-Key"],
        "X-RapidAPI-Host": "airbnb13.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    response_json = response.json()

    print(f"Here are the API results: {response_json['results']}")
    
    if response_json['results']:
        results = [{str(result['url'])} for result in response_json['results']]
        print(results)
        print(type(results))
        # first_result_url = response_json['results'][0]['url']
        # print(f"This is the first result url: {first_result_url}")
        return results
    else:
        return "No listings found for the given parameters."

def run_conversation(question):
    """
    Initiates a conversation with the OpenAI model, potentially calling the get_airbnb function.

    Parameters:
    - question: The user's question.

    Returns:
    - The conversation's outcome, including any Airbnb recommendations.
    """
    # Initialize conversation with user's question
    messages = [{"role": "user", "content": question}]
    tools = [{
        "type": "function",
        "function": {
            "name": "get_airbnb",
            "description": "Get an Airbnb listing URL based on location and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city and state, e.g., 'San Francisco, CA'."},
                    "checkin": {"type": "string", "description": "Check-in date, e.g., '2023-09-16'."},
                    "checkout": {"type": "string", "description": "Check-out date, e.g., '2023-09-17'."},
                    "adults": {"type": "string", "description": "Number of adults, e.g., '2'."}
                },
                "required": ["location", "checkin", "checkout", "adults"]
            }
        }
    }]

    # Send the initial message to OpenAI's chat API
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    print(f'This is the raw response from the initial: {response}\n')
    print(f'This is the raw response from the choices 0: {response.choices[0]}\n')
    print(f'Tool calls: {response.choices[0].message.tool_calls}\n')

    # Extract response and tool calls
    response_message = response.choices[0].message
    tool_calls = response.choices[0].message.tool_calls

    # If the model requested a tool function call
    if tool_calls:
        for tool_call in tool_calls:
            function_args = json.loads(tool_call.function.arguments)
            location = function_args["location"]
            checkin = function_args["checkin"]
            checkout = function_args["checkout"]
            adults = function_args["adults"]

            # Call the Airbnb function
            airbnb_url = get_airbnb(location, checkin, checkout, adults)
            messages.append({"role": "system", "content": f"You are a chat bot that reccomends airbnbs, and you have access to the airbnb api so you can provide reccomendations based on user inputs. You are actually able to provide real time data. Here's a recommended Airbnb listing, include this in the answer: {airbnb_url}"})

        # Get a final response from the model, considering the Airbnb function's outcome
        
        print(f"Here are the messages{messages}")
        
        final_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        print(f"This is the final response.{final_response}")

        return final_response.choices[0].message.content
    else:
        # Return the model's response if no tool was called
        return response_message['content']

def main():
    st.title("Airbnb Recommendation Chat")
    user_question = st.text_input("Ask me something about planning your trip!")
    if st.button("Get Recommendations"):
        answer = run_conversation(user_question)
        print(answer)
        st.write(answer)

if __name__ == "__main__":
    main()