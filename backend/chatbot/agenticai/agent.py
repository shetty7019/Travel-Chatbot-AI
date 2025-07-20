from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import Runnable
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field # Add these imports for structured output
from typing import TypedDict, List
import requests
import os
import json
import random

# Ensure pydantic is installed: pip install pydantic

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")

# ----------- Initialize LLM -----------
llm = ChatOllama(model="llama3", temperature=0.1)

# ----------- Define Agent State -----------
class AgentState(TypedDict):
    messages: List[BaseMessage]
    intent: str

# ----------- Define Pydantic Model for Itinerary Parameter Extraction -----------
class ItineraryParams(BaseModel):
    """Parameters for planning a travel itinerary."""
    city: str = Field(description="The city or destination for the travel itinerary. If not found, use 'N/A'.")
    days: int = Field(description="The number of days for the itinerary. Default to 3 if not explicitly specified.")

# ----------- Node 1: Detect Intent -----------

intent_prompt = PromptTemplate.from_template(
    """Given the following chat history and the latest user message, determine the user's primary intent.
    Choose ONLY one of the following exact intent labels:
    - 'weather': If the user is asking about current weather, forecast, or temperature for a specific location.
    - 'itinerary': If the user is asking for trip planning, travel schedules, or multi-day plans.
    - 'poi': If the user is asking about points of interest, attractions, landmarks, or places to visit in a location.
    - 'greeting': If the user is simply saying hello or giving a salutation.
    - 'general_query': If the user's message does not fit any of the above specific categories and is a general question or statement.

    Do NOT invent new intents. If unsure, default to 'general_query'.

    Chat History:
    {history}

    Latest User Message: {latest_message}

    Intent:"""
)

intent_detector_chain = intent_prompt | llm

def detect_intent(state: AgentState) -> AgentState:
    print("--- Detecting Intent ---")
    messages = state['messages']
    last_msg_content = messages[-1].content.lower()
    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[:-1]])

    if any(greet_word in last_msg_content for greet_word in ["hi", "hello", "hey", "hola"]):
        state['intent'] = "greeting"
        print(f"Detected Intent (keyword): {state['intent']}")
        return state

    intent_response = intent_detector_chain.invoke({
        "history": history_str,
        "latest_message": last_msg_content
    }).content.strip().lower()

    print(f"Raw LLM Intent Output: '{intent_response}'")

    detected_label = "general_query"

    if "general_query" in intent_response:
        detected_label = "general_query"
    elif "weather" in intent_response:
        detected_label = "weather"
    elif "itinerary" in intent_response:
        detected_label = "itinerary"
    elif "poi" in intent_response:
        detected_label = "poi"
    elif "greeting" in intent_response:
        detected_label = "greeting"

    state['intent'] = detected_label

    print(f"Detected Intent (LLM): {state['intent']} with Raw LLM Intent Output: '{intent_response}'")
    return state

# --- Tool Functions (calling external APIs) ---
def get_current_weather(city: str) -> str:
    if not OPENWEATHER_API_KEY:
        return "Weather API key not set. Cannot fetch weather."

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["cod"] == 200:
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            return (f"The current weather in {city} is {weather_description}, "
                    f"with a temperature of {temperature}°C (feels like {feels_like}°C). "
                    f"Humidity is {humidity}%.")
        else:
            return f"Could not get weather for {city}. Error: {data.get('message', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather for {city}: {e}"
    except json.JSONDecodeError:
        return f"Error decoding JSON response for weather in {city}."
    except KeyError:
        return f"Unexpected data format from weather API for {city}."

def get_city_coordinates(city: str) -> dict:
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }
    headers = {
        'User-Agent': 'TravelChatbot/1.0 (your_email@example.com)'
    }
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            lat = data[0].get("lat")
            lon = data[0].get("lon")
            display_name = data[0].get("display_name")
            return {"lat": lat, "lon": lon, "display_name": display_name}
        else:
            return {"error": f"Could not find coordinates for {city}."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching coordinates for {city}: {e}"}
    except json.JSONDecodeError:
        return {"error": f"Error decoding JSON response for coordinates in {city}."}

def get_pois_nearby(lat: float, lon: float, radius_km: int = 1, limit: int = 5) -> str:
    if not OPENTRIPMAP_API_KEY:
        return "OpenTripMap API key not set. Cannot fetch POIs."

    radius_meters = radius_km * 1000

    base_url = "https://api.opentripmap.com/0.1/en/places/radius"
    params = {
        "radius": radius_meters,
        "lon": lon,
        "lat": lat,
        "rate": "3",
        "format": "json",
        "limit": limit,
        "apikey": OPENTRIPMAP_API_KEY
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            pois = []
            for item in data:
                name = item.get("name") or "Unnamed Place"
                kind = item.get("kinds", "N/A")
                pois.append(f"- {name} ({kind})")
            if pois:
                return "Some interesting places nearby:\n" + "\n".join(pois)
            else:
                return f"No interesting places found within {radius_km} km."
        else:
            return f"No data returned for POIs near ({lat}, {lon})."
    except requests.exceptions.RequestException as e:
        return f"Error fetching POIs: {e}"
    except json.JSONDecodeError:
        return f"Error decoding JSON response for POIs."

# --- Prompts for parameter extraction ---
extract_city_prompt = PromptTemplate.from_template(
    """Extract the city name from the following user message.
    If no city is explicitly mentioned, respond with "N/A".

    User message: {message}

    City:"""
)

# Prompt for extracting Itinerary parameters
extract_itinerary_params_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at extracting travel itinerary details from user queries. "
               "Extract the city and number of days for the itinerary. If days are not explicitly mentioned, default to 3."),
    ("human", "{message}")
])


# --- Prompts for response generation after tool call ---

weather_response_prompt = PromptTemplate.from_template(
    """You are a helpful travel assistant.
    The user asked: "{query}"
    Here is the weather information retrieved: {weather_info}

    Please summarize this weather information concisely and in a friendly way for the user.
    Do not add any outside information or make assumptions.
    Response:"""
)

poi_response_prompt = PromptTemplate.from_template(
    """You are a helpful travel assistant.
    The user asked: "{query}"
    Here are the points of interest retrieved: {poi_info}

    Please list the interesting places found concisely and in a friendly way for the user.
    List only the top 3-5 places if many are provided. Do not add any outside information or make assumptions.
    Response:"""
)

# NEW: Prompt for Itinerary Generation
itinerary_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful and creative travel planner. "
               "Generate a detailed and engaging {days}-day itinerary for {city}. "
               "Include popular attractions, local experiences, and practical tips for each day. "
               "Format the itinerary day by day, clearly labeling each day with bold text (e.g., **Day 1:**). "
               "Start the itinerary directly, without an introductory sentence like 'Here is your itinerary...'. "
               "If the city is large, focus on a reasonable area per day. Conclude with a friendly closing remark."),
    ("human", "Generate a {days}-day itinerary for {city}.")
])

# ----------- Node 2: Call Tool / Generate Response -----------

def call_tool(state: AgentState) -> AgentState:
    print("--- Calling Tool / Generating Response ---")
    intent = state['intent']
    messages = state['messages']
    user_msg_content = messages[-1].content
    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[:-1]])

    reply = ""
    tool_output = "" # Initialize tool_output

    if intent == "weather":
        city_extractor = extract_city_prompt | llm
        city_response = city_extractor.invoke({"message": user_msg_content}).content.strip()
        city = city_response if city_response != "N/A" else None

        if city:
            tool_output = get_current_weather(city)
            weather_prompt_input = weather_response_prompt.format(
                query=user_msg_content,
                weather_info=tool_output
            )
            reply = llm.invoke(weather_prompt_input).content
        else:
            reply = "Please tell me which city you'd like the weather for!"

    elif intent == "poi":
        city_extractor = extract_city_prompt | llm
        city_response = city_extractor.invoke({"message": user_msg_content}).content.strip()
        city = city_response if city_response != "N/A" else None

        if city:
            coords = get_city_coordinates(city)
            if "error" not in coords:
                tool_output = get_pois_nearby(float(coords["lat"]), float(coords["lon"]))
                poi_prompt_input = poi_response_prompt.format(
                    query=user_msg_content,
                    poi_info=tool_output
                )
                reply = llm.invoke(poi_prompt_input).content
            else:
                reply = coords["error"]
        else:
            reply = "Please tell me the city where you want to find points of interest!"

    elif intent == "itinerary":
        print("--- Itinerary Planning Flow ---")
        try:
            # Use structured output to parse city and days
            param_extractor = extract_itinerary_params_prompt | llm.with_structured_output(ItineraryParams)
            extracted_params = param_extractor.invoke({"message": user_msg_content})

            city = extracted_params.city
            days = extracted_params.days # This will default to 3 if not specified by LLM due to Pydantic model

            print(f"Extracted Itinerary Params: City='{city}', Days={days}")

            if city and city.lower() != "n/a":
                # Generate itinerary using LLM
                itinerary_response = itinerary_generation_prompt.invoke({
                    "city": city,
                    "days": days
                }).content
                reply = itinerary_response
            else:
                reply = "I can help with an itinerary! Which city are you planning to visit and for how many days?"
        except Exception as e:
            print(f"Error during itinerary planning: {e}")
            reply = "I had a bit of trouble planning that itinerary. Could you please specify the city and number of days clearly? For example: 'Plan a 5-day trip to Rome.'"

    elif intent == "greeting":
        reply = llm.invoke(f"Generate a friendly greeting from a travel assistant based on this message: {user_msg_content}").content
    elif intent == "general_query":
        messages_for_llm = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful travel assistant. Answer the user's general question concisely and clearly."),
            ("user", f"Chat History:\n{history_str}\n\nLatest User Message: {user_msg_content}")
        ]).format_messages()
        reply = llm.invoke(messages_for_llm).content
    else:
        reply = llm.invoke(f"As a travel assistant, I'm not sure how to handle '{user_msg_content}'. How can I assist you with your travel plans?").content

    state['messages'].append(AIMessage(content=reply))
    print(f"Final Generated Reply: {reply}")
    return state

# ----------- Build LangGraph -----------

def build_agent():
    builder = StateGraph(AgentState)

    builder.add_node("detect_intent", detect_intent)
    builder.add_node("call_tool", call_tool)

    builder.set_entry_point("detect_intent")
    builder.add_edge("detect_intent", "call_tool")
    builder.add_edge("call_tool", END)

    graph = builder.compile()
    return graph