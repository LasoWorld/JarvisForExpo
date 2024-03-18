import concurrent.futures
import datetime
import requests
import json
import subprocess
import pyttsx3
import speech_recognition as sr
import os
import pickle
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from openai import ChatCompletion, ChatCompletionMessage
import random
import re


openai_api_key = "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"


openweathermap_api_key = ""


newsapi_api_key = ""

credentials_file_path = 'path/to/credentials.json'
token_file_path = 'path/to/token.pickle'

def chat(messages):
    messages_input = [ChatCompletionMessage(role=msg["role"], content=msg["content"]) for msg in messages]
    response = ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_input, api_key=openai_api_key)
    reply = response["choices"][0]["message"]["content"]
    return reply

def generate_image_using_ig(prompt):
    subprocess.run(["python", "ig.py", "--no-listen", prompt])

def say(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.pause_threshold = 1.5
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=5)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language='en-US')
            print(f"User said: {query}\n")
            return query
        except sr.WaitTimeoutError:
            print("Listening timed out. Please try again.")
            return ""
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio.")
            return ""
        except Exception as e:
            print(f"Recognition Error: {e}")
            return ""

def get_starting_phrase():
    phrases = ["Hello! I am Jarvis.", "Hi there! This is Jarvis speaking.", "Greetings! Jarvis here."]
    return random.choice(phrases)

def get_ending_phrase():
    return ["Goodbye!", "See you later!", "Farewell!"]

def get_wikipedia_summary(query):
    url = f"https://en.wikipedia.org/wiki/{query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    first_paragraph = soup.find("p").get_text()
    return first_paragraph

def get_weather(city="your_city"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweathermap_api_key}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        main = data['main']
        weather_desc = data['weather'][0]['description']
        temperature = main['temp']
        return f"Weather in {city}: {weather_desc}, temperature: {temperature}K"
    else:
        return "Unable to fetch weather information."

def get_top_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi_api_key}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and data.get('articles'):
        top_news = data['articles'][0]['title']
        return f"Top news: {top_news}"
    else:
        return "Unable to fetch top news."

def schedule_appointment(user_input):
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    creds = None
    if os.path.exists(token_file_path):
        with open(token_file_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file_path, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Parse user_input to get appointment details (date, time, summary, etc.)
    # Replace the hardcoded values below with the parsed user input
    start_time = '2024-02-15T09:00:00-07:00'
    end_time = '2024-02-15T17:00:00-07:00'
    event_summary = 'Appointment'

    event = {
        'summary': event_summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/Los_Angeles',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return f"Event created: {event.get('htmlLink')}"

def handle_request_async(user_input, messages):
    if user_input.lower() == "quit()":
        return "quit()"

    user_input = user_input.lower()

    if user_input.startswith("wikipedia"):
        query = re.findall(r"wikipedia\s(.+)", user_input)[0]
        summary = get_wikipedia_summary(query)
        assistant_response = f"According to Wikipedia, {summary}"

    elif "image" in user_input:
        prompt = re.findall(r"image\s(.+)", user_input)[0]
        generate_image_using_ig(prompt)
        assistant_response = "I also generated an image for you."

    elif "weather" in user_input:
        weather_info = get_weather()
        assistant_response = f"Weather information: {weather_info}"

    elif "top news" in user_input:
        top_news = get_top_news()
        assistant_response = f"Top news: {top_news}"

    elif "schedule appointment" in user_input:
        response = schedule_appointment(user_input)
        assistant_response = f"I have scheduled an appointment for you. {response}"

    else:
        messages.append({"role": "user", "content": user_input})
        assistant_response = chat(messages)

        if "generate image" in assistant_response.lower():
            image_prompt = user_input
            generate_image_using_ig(image_prompt)
            assistant_response += f" I also generated an image for you."

    if assistant_response:
        print("\n" + assistant_response + "\n")
        say(assistant_response)

    return assistant_response

def process_requests():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            user_input = recognize_speech()

            if user_input.lower() == "quit()":
                break

            if user_input:
                future = executor.submit(handle_request_async, user_input, messages.copy())
                futures.append(future)

        for completed_future in concurrent.futures.as_completed(futures):
            completed_future.result()

# Start processing requests
messages = []
futures = []
process_requests()
