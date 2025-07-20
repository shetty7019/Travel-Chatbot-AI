Travel Chatbot AI Assistant

## Overview

This is a full-stack AI-powered travel chatbot built with Django (Python) for the backend and React (JavaScript) for the frontend. The chatbot leverages LangChain and LangGraph to create an intelligent agent capable of understanding user intent and providing relevant travel information, including weather forecasts, points of interest, and dynamically generated itineraries. The frontend features a modern, responsive user interface.

### Key Features

* Intent Detection: Automatically identifies user intent (e.g., `weather`, `itinerary`, `poi`, `general_query`, `greeting`).
* Dynamic Itinerary Planning: Generates multi-day travel itineraries based on user-specified city and duration (e.g., "Plan a 3-day trip to Paris").
* Real-time Weather Information: Fetches current weather data for any specified city using the OpenWeatherMap API.
* Points of Interest (POI) Discovery: Finds interesting places and attractions near a given location using the OpenTripMap API and Nominatim for geocoding.
* Conversational AI: Provides natural and helpful responses to general travel queries.
* Session Management: Maintains chat history across sessions using a Django database.
* Modern User Interface: A clean, intuitive, and responsive chat interface built with React, mimicking the look and feel of popular chat applications.

### Technologies Used

**Backend (Django - Python)**
* External APIs:
    * [OpenWeatherMap API](https://openweathermap.org/api): For weather data.
    * [OpenTripMap API](https://opentripmap.com/en/developers): For points of interest.
    * [Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org/): For geocoding (converting city names to coordinates).

**Frontend (React - JavaScript)**
* React: JavaScript library for building user interfaces.
* CSS: For styling, including responsive design.


## Setup Instructions

Follow these steps to get the project up and running on your local machine.

### 1. Clone the Repository

### 2. Backend Setup (Django)

i. Create a Virtual Environment (Recommended) :  python -m venv venv 

ii. Activate a Virtual Environment :  macOS / Linux: source venv/bin/activate

iii. Install Python Dependencies :  pip install -r requirements.txt

iv. Set Up Environment Variables:  Create a .env file in the root of your TRAVEL-CHATBOT directory (where manage.py is located) and add your API keys.  Then, open .env and fill in your keys.

v. Run Database Migrations:

*** python manage.py makemigrations chatbot 

*** python manage.py migrate

vi. Start the Django Development Server:
*** python manage.py runserver 8000

### 3. Frontend Setup (React)

i. Navigate to the frontend directory

ii. Install Node.js Dependencies: npm install

iii. Configure Proxy : To allow the React development server to proxy API requests to your Django backend, ensure your frontend/package.json file contains a "proxy" entry:

{

  "name": "frontend",
  
  "version": "0.1.0",
  
  "private": true,
  
  "proxy": "[http://127.0.0.1:8000](http://127.0.0.1:8000)", # <--- Ensure this line exists
  
  "dependencies": {
  
    // ...
    
  }
  
}


iv. Start the React Development Server: npm start


### 4. Running the Chatbot
1. With both the Django backend (http://127.0.0.1:8000/) and the React frontend (http://localhost:3000/) running:

2. Open your browser to http://localhost:3000/

3. Type a message into the chat input.

## Example Queries:

1.  "Hello!" (Greeting)
2.  "What's the weather like in London?" (Weather)
