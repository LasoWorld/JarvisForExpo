import concurrent.futures
import pyttsx3
import speech_recognition as sr
import os
from openai import OpenAI
import random


openai_api_key = ""
client = OpenAI(api_key=openai_api_key)


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


def chat_with_openai(messages):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return completion.choices[0].message["content"]


def handle_request_async(user_input, messages):
    if user_input.lower() == "quit()":
        return "quit()"

    user_input = user_input.lower()

    if user_input:
        messages.append({"role": "user", "content": user_input})
        assistant_response = chat_with_openai(messages)

        if assistant_response:
            print("\n" + assistant_response + "\n")
            say(assistant_response)

        return assistant_response
    else:
        return ""


def process_requests():
    messages = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            user_input = recognize_speech()

            if user_input.lower() == "quit()":
                break

            if user_input:
                future = executor.submit(handle_request_async, user_input, messages.copy())
                future.result()


def say(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    process_requests()
