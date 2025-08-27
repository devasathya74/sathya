import sys
import os
import threading
import subprocess
import json
from time import sleep
from dotenv import load_dotenv
import asyncio
from queue import Queue  # Added for input queuing

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from Frontend.GUI import (
        GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen,
        TempDirectoryPath, SetMicrophoneStatus, AnswerModifier,
        GetMicrophoneStatus, GetAssistantStatus
    )
except ImportError as e:
    print(f"Error importing GUI modules: {e}")
    sys.exit(1)

try:
    from Backend.Model import FirstLayerDMM
    from Backend.RealtimeSearchEngine import RealtimeSearchEngine
    from Backend.Automation import Automation
    from Backend.SpeechToText import SpeechRecognition
    from Backend.ChatBot import ChatBot
    from Backend.TextToSpeech import ProcessTextToSpeech
except ImportError as e:
    print(f"Error importing Backend modules: {e}")
    sys.exit(1)

# Load environment variables using os.getenv
Username = os.getenv("Username", "User")
AssistantName = os.getenv("AssistantName", "NatAI")
DefaultMessages = f'''{Username}: Hello {AssistantName}, How are you?
{AssistantName}: Welcome {Username}. I am doing well. How may I help you?'''

# Define directories dynamically
data_dir = os.path.join(os.path.dirname(__file__), 'Data')
frontend_files_dir = os.path.join(os.path.dirname(__file__), 'Frontend', 'Files')

# List to store subprocesses
subprocesses = []

# List of functions for automation
functions = ["open", "close", "play", "system", "content", "googlesearch", "youtubesearch"]

# Queue to store user inputs
input_queue = Queue()

# Flag to track if the assistant is speaking
is_speaking = False

# Variable to track the last modified time of Query.data
last_query_modified_time = 0

def QueryModifier(Query):
    """Modify the query to ensure proper punctuation and capitalization."""
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    
    return new_query.capitalize()

def ShowDefaultChatIfNoChats():
    """Show default chat messages if no chat history exists."""
    chatlog_path = os.path.join(data_dir, 'ChatLog.json')
    os.makedirs(data_dir, exist_ok=True)  # Ensure Data directory exists
    try:
        with open(chatlog_path, "r", encoding='utf-8') as file:
            content = file.read().strip()
            if len(content) < 5:  # If file is empty or nearly empty
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                    file.write(DefaultMessages)
    except FileNotFoundError:
        with open(chatlog_path, "w", encoding='utf-8') as file:
            json.dump([], file)
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessages)
    except Exception as e:
        print(f"Error in ShowDefaultChatIfNoChats: {e}")

def ReadChatLogJson():
    """Read the chat log from ChatLog.json."""
    chatlog_path = os.path.join(data_dir, 'ChatLog.json')
    try:
        with open(chatlog_path, 'r', encoding='utf-8') as file:
            chatlog_data = json.load(file)
        return chatlog_data
    except FileNotFoundError:
        with open(chatlog_path, "w", encoding='utf-8') as file:
            json.dump([], file)
        return []
    except json.JSONDecodeError:
        print("Error: ChatLog.json is malformed. Resetting to empty.")
        with open(chatlog_path, "w", encoding='utf-8') as file:
            json.dump([], file)
        return []
    except Exception as e:
        print(f"Error reading ChatLog.json: {e}")
        return []

def AppendToChatLog(user_query, assistant_response):
    """Append the user query and assistant response to ChatLog.json."""
    chatlog_path = os.path.join(data_dir, 'ChatLog.json')
    try:
        # Read the existing chat log
        chatlog_data = ReadChatLogJson()
        
        # Append the user query
        chatlog_data.append({"role": "user", "content": user_query})
        # Append the assistant response
        chatlog_data.append({"role": "assistant", "content": assistant_response})
        
        # Write the updated chat log back to ChatLog.json
        with open(chatlog_path, 'w', encoding='utf-8') as file:
            json.dump(chatlog_data, file, indent=4)
    except Exception as e:
        print(f"Error in AppendToChatLog: {e}")

def ChatLogIntegration():
    """Integrate chat log data into the GUI's Database.data file."""
    try:
        json_data = ReadChatLogJson()
        formatted_chatlog = ""
        for entry in json_data:
            if entry["role"] == "user":
                formatted_chatlog += f"{Username}: {entry['content']}\n"
            elif entry["role"] == "assistant":
                formatted_chatlog += f"{AssistantName}: {entry['content']}\n"
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))
    except Exception as e:
        print(f"Error in ChatLogIntegration: {e}")

def ShowChatsOnGUI():
    """Display chats from Database.data in the GUI via Responses.data."""
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
            data = file.read()
        if len(data) > 0:
            lines = data.split('\n')
            result = '\n'.join(lines)
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(result)
                file.flush()  # Ensure the write is completed
    except Exception as e:
        print(f"Error in ShowChatsOnGUI: {e}")

def InitialExecution():
    """Perform initial setup for the application."""
    try:
        os.makedirs(frontend_files_dir, exist_ok=True)  # Ensure Frontend/Files exists
        # Initialize required files in Frontend/Files using TempDirectoryPath
        mic_path = TempDirectoryPath('Mic.data')
        status_path = TempDirectoryPath('Status.data')
        response_path = TempDirectoryPath('Response.data')
        database_path = TempDirectoryPath('Database.data')
        responses_path = TempDirectoryPath('Responses.data')
        query_path = TempDirectoryPath('Query.data')

        if not os.path.exists(mic_path):
            with open(mic_path, 'w', encoding='utf-8') as file:
                file.write("False")
        if not os.path.exists(status_path):
            with open(status_path, 'w', encoding='utf-8') as file:
                file.write("Available...")
        if not os.path.exists(response_path):
            with open(response_path, 'w', encoding='utf-8') as file:
                file.write("")
        if not os.path.exists(database_path):
            with open(database_path, 'w', encoding='utf-8') as file:
                file.write("")
        if not os.path.exists(responses_path):
            with open(responses_path, 'w', encoding='utf-8') as file:
                file.write("")
        if not os.path.exists(query_path):
            with open(query_path, 'w', encoding='utf-8') as file:
                file.write("")

        SetMicrophoneStatus("False")
        ShowTextToScreen("")
        ShowDefaultChatIfNoChats()
        ChatLogIntegration()
        ShowChatsOnGUI()

        # Initialize last modified time for Query.data
        global last_query_modified_time
        last_query_modified_time = os.path.getmtime(query_path)
    except Exception as e:
        print(f"Error in InitialExecution: {e}")

def SpeakInThread(text):
    """Run ProcessTextToSpeech in a separate thread to avoid blocking."""
    global is_speaking
    def speak():
        try:
            is_speaking = True
            ProcessTextToSpeech(text)
        except Exception as e:
            print(f"Error in SpeakInThread: {e}")
        finally:
            is_speaking = False
    threading.Thread(target=speak, daemon=True).start()

async def MainExecution(Query):
    """Main execution logic for processing user queries."""
    try:
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        ShowTextToScreen(f"{Username}: {Query}")
        SetAssistantStatus("Thinking...")
        Decision = FirstLayerDMM(Query)

        print(f"\nDecision: {Decision}\n")

        G = any(i for i in Decision if i.startswith("general"))
        R = any(i for i in Decision if i.startswith("realtime"))

        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for query in Decision:
            if "generate" in query:
                ImageGenerationQuery = str(query)
                ImageExecution = True

        for query in Decision:
            if not TaskExecution:
                if any(query.startswith(func) for func in functions):
                    success = await Automation(Decision)
                    if success:
                        TaskExecution = True
                    else:
                        print("Automation task failed.")
                        SetAssistantStatus("Available...")
                        return False

        if ImageExecution:
            try:
                image_data_path = os.path.join(frontend_files_dir, 'ImageGeneration.data')
                with open(image_data_path, "w", encoding='utf-8') as file:
                    file.write(f"{ImageGenerationQuery},True")
                p = subprocess.Popen(
                    ['python', os.path.join(os.path.dirname(__file__), 'Backend', 'ImageGeneration.py')],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE, shell=False
                )
                subprocesses.append(p)
                ChatLogIntegration()
                ShowChatsOnGUI()
                return True
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")
                SetAssistantStatus("Available...")
                return False

        if G and R or R:
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{AssistantName}: {Answer}")
            # Append the user query and assistant response to ChatLog.json
            AppendToChatLog(Query, Answer)
            SetAssistantStatus("Answering...")
            SpeakInThread(Answer)
            ChatLogIntegration()
            ShowChatsOnGUI()
            return True
        else:
            for query in Decision:
                if "general" in query:
                    SetAssistantStatus("Thinking...")
                    QueryFinal = query.replace("general", "").strip()
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{AssistantName}: {Answer}")
                    # Append the user query and assistant response to ChatLog.json
                    AppendToChatLog(Query, Answer)
                    SetAssistantStatus("Answering...")
                    SpeakInThread(Answer)
                    ChatLogIntegration()
                    ShowChatsOnGUI()
                    return True
                elif "realtime" in query:
                    SetAssistantStatus("Searching...")
                    QueryFinal = query.replace("realtime", "").strip()
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{AssistantName}: {Answer}")
                    # Append the user query and assistant response to ChatLog.json
                    AppendToChatLog(Query, Answer)
                    SetAssistantStatus("Answering...")
                    SpeakInThread(Answer)
                    ChatLogIntegration()
                    ShowChatsOnGUI()
                    return True
                elif "exit" in query:
                    QueryFinal = "Okay, Bye!"
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{AssistantName}: {Answer}")
                    # Append the user query and assistant response to ChatLog.json
                    AppendToChatLog("exit", Answer)
                    SetAssistantStatus("Answering...")
                    SpeakInThread(Answer)
                    ChatLogIntegration()
                    ShowChatsOnGUI()
                    for p in subprocesses:
                        p.terminate()
                    sys.exit(0)
                # Add a condition to stop continuous listening
                elif "stop listening" in query.lower():
                    SetAssistantStatus("Available...")
                    SetMicrophoneStatus("False")
                    return False

    except Exception as e:
        print(f"Error in MainExecution: {e}")
        SetAssistantStatus("Available...")
        return False

async def MonitorQueryFile():
    """Monitor Query.data for new user messages and add them to the input queue."""
    global last_query_modified_time
    query_file = TempDirectoryPath('Query.data')
    try:
        while True:
            if os.path.exists(query_file):
                current_modified_time = os.path.getmtime(query_file)
                if current_modified_time > last_query_modified_time:
                    with open(query_file, "r", encoding='utf-8') as file:
                        query = file.read().strip()
                        if query:
                            print(f"New query detected in Query.data: {query}")
                            input_queue.put(query)  # Add the query to the queue
                            last_query_modified_time = current_modified_time
                            # Clear the Query.data file to avoid re-processing
                            with open(query_file, "w", encoding='utf-8') as file:
                                file.write("")
            await asyncio.sleep(0.1)  # Check every 100ms
    except Exception as e:
        print(f"Error in MonitorQueryFile: {e}")

async def FirstThread():
    """Async loop to handle the main execution with continuous mic checking and query processing."""
    try:
        # Start the query file monitoring task
        query_monitor_task = asyncio.create_task(MonitorQueryFile())

        while True:
            MicStatus = GetMicrophoneStatus()
            if MicStatus.lower() == "true":
                # Continuously listen while MicStatus is "true"
                while MicStatus.lower() == "true":
                    # Only capture input if the assistant is not speaking
                    if not is_speaking:
                        SetAssistantStatus("Listening...")
                        try:
                            Query = SpeechRecognition()
                            if Query:
                                input_queue.put(Query)  # Add the query to the queue
                        except Exception as e:
                            print(f"SpeechRecognition failed: {e}")
                            SetAssistantStatus("Available...")
                            await asyncio.sleep(0.05)
                            continue

                    # Process queries from the queue
                    while not input_queue.empty():
                        query = input_queue.get()  # Get the next query from the queue
                        success = await MainExecution(query)
                        if not success:
                            SetAssistantStatus("Listening...")
                        # Wait until the assistant is done speaking before capturing the next input
                        while is_speaking:
                            await asyncio.sleep(0.1)  # Check frequently to avoid long delays

                    MicStatus = GetMicrophoneStatus()
                    if MicStatus.lower() == "true" and not is_speaking:
                        SetAssistantStatus("Listening...")
                    await asyncio.sleep(0.1)  # Small delay to avoid CPU overload
            else:
                # Process any queries from the queue even when mic is off
                while not input_queue.empty():
                    query = input_queue.get()
                    success = await MainExecution(query)
                    if not success:
                        SetAssistantStatus("Available...")
                    while is_speaking:
                        await asyncio.sleep(0.1)

                AIStatus = GetAssistantStatus()
                if "Available..." not in AIStatus:
                    SetAssistantStatus("Available...")
            await asyncio.sleep(0.1)  # Small delay to avoid CPU overload
    except KeyboardInterrupt:
        print("FirstThread interrupted. Shutting down...")
        for p in subprocesses:
            p.terminate()
        sys.exit(0)
    finally:
        query_monitor_task.cancel()

def SecondThread():
    """Thread to run the GUI."""
    try:
        GraphicalUserInterface()
    except KeyboardInterrupt:
        print("GUI thread interrupted. Shutting down...")
        for p in subprocesses:
            p.terminate()
        sys.exit(1)
    except Exception as e:
        print(f"Error in GUI thread: {e}")
        sys.exit(1)

if __name__ == "__main__":
    os.makedirs(data_dir, exist_ok=True)  # Ensure Data directory exists
    os.makedirs(frontend_files_dir, exist_ok=True)  # Ensure Frontend/Files exists
    InitialExecution()

    try:
        gui_thread = threading.Thread(target=SecondThread, daemon=True)
        gui_thread.start()
        asyncio.run(FirstThread())
    except KeyboardInterrupt:
        print("Main thread interrupted. Shutting down...")
        for p in subprocesses:
            p.terminate()
        sys.exit(0)