import os
import asyncio
import subprocess
from AppOpener import close, open as appopen
from webbrowser import open as webopen
import pywhatkit
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import requests
import keyboard

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Fetch environment variables
GroqAPIKey = os.getenv("GroqAPIKey")
Username = os.getenv("Username", "User")  # Default to "User" if not set
if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in environment variables")

# Define data directory dynamically
data_dir = os.path.join(os.path.dirname(__file__), '../../Data')
os.makedirs(data_dir, exist_ok=True)  # Ensure Data directory exists

classes = ["zCubwf", "hgKElc", "LKToo sY7ric", "Z0LcW", "gsrt vk_bk FzvWSB YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "O5uR6d LTKOO", "vlzY6d", "webansers-webanswers_table__webanswers-table", "dDoNo ikb4Bb gsrt", "sXLaOe",
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesk", "SPZz6b"]

useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.117 Safari/537.36"

client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask."
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {Username}, You are a content writer. You have to write content like letter"}]

def check_internet():
    try:
        requests.get("https://google.com", timeout=5)
        return True
    except requests.ConnectionError:
        print("No internet connection. Please connect to the internet and try again.")
        return False

def GoogleSearch(Topic):
    if check_internet():
        pywhatkit.search(Topic)
        return True
    return False

def Content(Topic):
    def OpenNotepad(File):
        default_text_editor = "notepad.exe"
        subprocess.Popen([default_text_editor, File])
        
    def ContentWriteAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
       
        completion = client.chat.completions.create(
            model='llama3-70b-8192',
            messages=SystemChatBot + messages,
            max_tokens=2048,
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
        messages.append({"role": "assistant", "content": Answer})
        return Answer
    
    Topic = Topic.replace("content ", "")
    ContentByAI = ContentWriteAI(Topic)

    file_path = os.path.join(data_dir, f"{Topic.lower().replace(' ', '')}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(ContentByAI)
        file.close()

        OpenNotepad(file_path)
        return True

def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    if check_internet():
        pywhatkit.playonyt(query)
        return True
    return False

def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            return links

        def search_google(query):
            url = f'https://www.google.com/search?q={query}'
            headers = {"User-Agent": useragent}
            response = sess.get(url, headers=headers)

            if response.status_code == 200:
                return response.text
            else:
                print("Failed to retrieve search results.")
                return None
        
        html = search_google(app)

        if html:
            links = extract_links(html)
            if links:
                link = links[0]
                webopen(link.get('href'))

        return True

def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except:
            return False

def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True

def TranslateAndExecute(commands: list[str]):
    results = []

    for command in commands:
        if command.startswith("open "):
            if "open it" in command:
                pass
            if "open file" == command:
                pass
            else:
                result = OpenApp(command.removeprefix("open "))
                results.append(result)

        elif command.startswith("general "):
            pass

        elif command.startswith("realtime "):
            pass
        
        elif command.startswith("close "):
            result = CloseApp(command.removeprefix("close "))
            results.append(result)

        elif command.startswith("play "):
            result = PlayYoutube(command.removeprefix("play "))
            results.append(result)

        elif command.startswith("content "):
            result = Content(command.removeprefix("content "))
            results.append(result)
        
        elif command.startswith("write "):
            result = Content(command.removeprefix("write "))
            results.append(result)
        
        elif command.startswith("google search "):
            result = GoogleSearch(command.removeprefix("google search "))
            results.append(result)

        elif command.startswith("youtube search "):
            result = YouTubeSearch(command.removeprefix("youtube search "))
            results.append(result)

        elif command.startswith("system "):
            result = System(command.removeprefix("system "))
            results.append(result)

        else:
            print(f"No Function Found for {command}")

    return results

async def Automation(commands: list[str]):
    results = TranslateAndExecute(commands)
    return all(results)  # Return True if all tasks succeeded

if __name__ == "__main__":
    if check_internet():
        while True:
            commands = input("Enter command: ").split(",")
            print(asyncio.run(Automation(commands)))
    else:
        print("Script terminated due to no internet connection.")