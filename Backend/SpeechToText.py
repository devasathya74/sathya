from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import mtranslate as mt
import speech_recognition as sr
import pyaudio

def SpeechRecognition():
    print("Initializing SpeechRecognition...")
    r = sr.Recognizer()
    try:
        # List available devices
        p = pyaudio.PyAudio()
        print(f"Found {p.get_device_count()} audio devices")
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            print(f"Device {i}: {device_info['name']}, Input Channels: {device_info['maxInputChannels']}")
        p.terminate()

        # Use the default microphone
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print("Processing audio...")
            text = r.recognize_google(audio)
            print(f"Recognized text: {text}")
            return text
    except sr.UnknownValueError:
        print("SpeechRecognition: Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"SpeechRecognition: Could not request results; {e}")
        return ""
    except Exception as e:
        print(f"Error in SpeechRecognition: {e}")
        return ""

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Fetch InputLanguage from environment variables
InputLanguage = os.getenv("InputLanguage", "hi")  # Default to English if not found

# Define data directory dynamically
data_dir = os.path.join(os.path.dirname(__file__), '../../Data')
os.makedirs(data_dir, exist_ok=True)  # Ensure Data directory exists

# Define temp directory dynamically
temp_dir = os.path.join(os.path.dirname(__file__), '../../Frontend/files')
os.makedirs(temp_dir, exist_ok=True)  # Ensure Frontend/files exists

# HTML code for speech recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# Replace language in HTML code
HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Write HTML to file dynamically
html_path = os.path.join(data_dir, 'voice.html')
with open(html_path, "w", encoding='utf-8') as f:
    f.write(HtmlCode)

# Set up Chrome driver
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def SetAssistantStatus(status):
    status_path = os.path.join(temp_dir, 'Status.data')
    with open(status_path, "w", encoding='utf-8') as file:
        file.write(status)

def QueryModifier(Query):
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

def UniversalTranslator(Text):
    english_translate = mt.translate(Text, "en", "auto")
    return english_translate.capitalize()

def SpeechRecognition():
    driver.get(f"file:///{html_path}")

    driver.find_element(by=By.ID, value="start").click()

    while True:
        try:
            Text = driver.find_element(by=By.ID, value="output").text

            if Text:
                driver.find_element(by=By.ID, value="end").click()

                if InputLanguage.lower() == "en" or "in" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception:
            pass

if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)