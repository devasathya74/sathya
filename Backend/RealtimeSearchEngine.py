from googlesearch import search
from groq import Groq
from json import load, dump
import datetime 
from dotenv import load_dotenv
import os

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

Username = os.getenv("Username")
AssistantName = os.getenv("AssistantName")
GroqAPIKey = os.getenv("GroqAPIKey")
if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in environment variables")

client = Groq(api_key=GroqAPIKey)

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Define data directory dynamically
data_dir = os.path.join(os.path.dirname(__file__), '../../Data')
os.makedirs(data_dir, exist_ok=True)  # Ensure Data directory exists
chatlog_path = os.path.join(data_dir, 'ChatLog.json')

try:
    with open(chatlog_path, "r", encoding='utf-8') as f:
        message = load(f)
except Exception:
    with open(chatlog_path, "w", encoding='utf-8') as f:
        dump([], f)
    message = []

def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))
    answer = f"The search result for '{query}' are:\n[start]\n"
    for i in results:
        answer += f"Title: {i.title}\nDescription: {i.description}\n\n"                            
    answer += "[end]"
    return answer

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-time information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    with open(chatlog_path, "r", encoding='utf-8') as f:
        messages = load(f)
    messages.append({"role": "user", "content": f"{prompt}"})

    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        temperature=0.7,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None
    )

    answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content

    Answer = answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    with open(chatlog_path, "w", encoding='utf-8') as f:
        dump(messages, f, indent=4)

    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)

if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))