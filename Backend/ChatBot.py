from groq import Groq
from json import load, dump
import datetime
from dotenv import load_dotenv  # Changed from dotenv_values
import os

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))  # Replaced dotenv_values(".env")

# Fetch environment variables
Username = os.getenv("Username")  # Changed from env_vars.get("Username")
AssistantName = os.getenv("AssistantName")  # Changed from env_vars.get("Assistantname"), corrected case
GroqAPIKey = os.getenv("GroqAPIKey")  # Changed from env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

message = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

# Define data directory dynamically
data_dir = os.path.join(os.path.dirname(__file__), '../../Data')
os.makedirs(data_dir, exist_ok=True)  # Ensure Data directory exists
chatlog_path = os.path.join(data_dir, "ChatLog.json")  # Dynamic path

try:
    with open(chatlog_path, "r") as f:  # Replaced hardcoded r"Data\ChatLog.json"
        message = load(f)
except FileNotFoundError:
    with open(chatlog_path, "w") as f:  # Replaced hardcoded r"Data\ChatLog.json"
        dump([], f)

def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed,\n"
    data += f"Today: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours {minute} minutes {second} seconds.\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    try:
        with open(chatlog_path, "r") as f:  # Replaced hardcoded r"Data\ChatLog.json"
            message = load(f)

        message.append({"role": "user", "content": f"{Query}"})

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + message,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")

        message.append({"role": "assistant", "content": Answer})

        with open(chatlog_path, "w") as f:  # Replaced hardcoded r"Data\ChatLog.json"
            dump(message, f, indent=4)

        return AnswerModifier(Answer=Answer)  # Fixed keyword argument syntax
    
    except Exception as e:
        print(f"Error: {e}")
        with open(chatlog_path, "w") as f:  # Replaced hardcoded r"Data\ChatLog.json"
            dump([], f, indent=4)
        return ChatBot(Query)

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))