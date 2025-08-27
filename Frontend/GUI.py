from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat, QLinearGradient, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, QPoint
from dotenv import load_dotenv
import sys
import os
import json
import time
import keyboard
from datetime import datetime

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Fetch environment variables
AssistantName = os.getenv("AssistantName", "NatAI")
current_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of GUI.py: C:/Users/shree/Desktop/NatAI/Frontend
TempDirPath = os.path.join(current_dir, '..', 'Files')  # Adjusted to relative path
GraphicsDirPath = os.path.join(current_dir, 'Graphics')  # Corrected path: Points to Frontend/Graphics
DataDirPath = os.path.join(os.path.dirname(__file__), '../../Data')  # Dynamic Data path
os.makedirs(TempDirPath, exist_ok=True)  # Ensure TempDirPath exists
os.makedirs(DataDirPath, exist_ok=True)  # Ensure DataDirPath exists

old_chat_message = ""
last_modified_time = 0  # To track file changes

# Function to read JSON files from Data directory and append to Responses.data
def append_data_from_directory():
    global old_chat_message
    responses_file = os.path.join(TempDirPath, "Responses.data").replace('\\', '/')

    # Read existing content of Responses.data to avoid duplicates
    existing_content = ""
    try:
        with open(responses_file, "r", encoding='utf-8') as file:
            existing_content = file.read().strip()
    except:
        pass

    # Read all JSON files from Data directory
    chat_history = existing_content
    for filename in os.listdir(DataDirPath):
        if filename.endswith(".json"):
            file_path = os.path.join(DataDirPath, filename)
            try:
                with open(file_path, "r", encoding='utf-8') as file:
                    data = json.load(file)
                    for entry in data:
                        role = entry.get("role", "")
                        content = entry.get("content", "")
                        if role and content:
                            message = f"{role.capitalize()}: {content}"
                            # Avoid duplicating messages
                            if message not in chat_history:
                                chat_history += f"\n{message}" if chat_history else message
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Write the updated chat history to Responses.data
    with open(responses_file, "w", encoding='utf-8') as file:
        file.write(chat_history)

# Utility Functions
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

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

def SetMicrophoneStatus(Command):
    with open(os.path.join(TempDirPath, 'Mic.data'), "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(os.path.join(TempDirPath, 'Mic.data'), "r", encoding='utf-8') as file:
        Status = file.read()
    return Status

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    try:
        with open(os.path.join(TempDirPath, 'Status.data'), "r", encoding='utf-8') as file:
            Status = file.read().strip()
        return Status
    except:
        return "Available"

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicDirectoryPath(Filename):
    path = os.path.join(GraphicsDirPath, Filename).replace('\\', '/')
    print(f"Attempting to load image: {path}")  # Debug: Print the path
    if not os.path.exists(path):
        print(f"Error: File not found at {path}")  # Debug: Check if file exists
    return path

def TempDirectoryPath(Filename):
    Path = os.path.join(TempDirPath, Filename).replace('\\', '/')
    return Path

def ShowTextToScreen(Text):
    with open(os.path.join(TempDirPath, 'Response.data'), "w", encoding='utf-8') as file:
        file.write(Text)

# Function to load the custom user name from UserName.data
def load_user_name():
    user_name_file = os.path.join(TempDirPath, 'UserName.data')
    try:
        with open(user_name_file, "r", encoding='utf-8') as file:
            user_name = file.read().strip()
            return user_name if user_name else ""
    except:
        return ""

# Function to save the custom user name to UserName.data
def save_user_name(name):
    user_name_file = os.path.join(TempDirPath, 'UserName.data')
    with open(user_name_file, "w", encoding='utf-8') as file:
        file.write(name)

# Chat Section
class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Chat Text Area
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        font = QFont("Segoe UI", 14)
        self.chat_text_edit.setFont(font)
        self.chat_text_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 15px;
                padding: 15px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.2);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d4af37;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        layout.addWidget(self.chat_text_edit)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.start(100)  # Increased to 100ms to reduce CPU usage

        # Load previous chats on initialization
        self.loadPreviousChats()

    def loadPreviousChats(self):
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                messages = file.read().strip()
                if messages:
                    self.addMessage(messages, 'white')
                    global old_chat_message
                    old_chat_message = messages
                    global last_modified_time
                    last_modified_time = os.path.getmtime(TempDirectoryPath('Responses.data'))
        except:
            pass

    def loadMessages(self):
        global old_chat_message, last_modified_time
        responses_file = TempDirectoryPath('Responses.data')
        try:
            # Check if the file has been modified
            current_modified_time = os.path.getmtime(responses_file)
            if current_modified_time > last_modified_time:
                with open(responses_file, "r", encoding='utf-8') as file:
                    messages = file.read().strip()
                    if messages and messages != old_chat_message:
                        self.chat_text_edit.clear()  # Clear existing text to avoid duplicates
                        self.addMessage(messages, 'white')
                        old_chat_message = messages
                        last_modified_time = current_modified_time
        except Exception as e:
            print(f"Error loading messages: {e}")

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextCharFormat()
        formatm = QTextBlockFormat()
        formatm.setTopMargin(10)
        formatm.setLeftMargin(10)
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        cursor.setBlockFormat(formatm)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.ensureCursorVisible()  # Scroll to the bottom

# Reply Section
class ReplySection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Reply Text Area
        self.reply_text_edit = QTextEdit()
        self.reply_text_edit.setReadOnly(True)
        self.reply_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.reply_text_edit.setFrameStyle(QFrame.NoFrame)
        font = QFont("Segoe UI", 14)
        self.reply_text_edit.setFont(font)
        self.reply_text_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.3);
                color: #d4af37;
                border-radius: 15px;
                padding: 15px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.2);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d4af37;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        layout.addWidget(self.reply_text_edit)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadLatestReply)
        self.timer.start(50)  # Reduced to 50ms for faster updates

        # Initialize last content to avoid unnecessary updates
        self.last_content = ""

    def loadLatestReply(self):
        try:
            responses_file = TempDirectoryPath('Responses.data')
            if not os.path.exists(responses_file):
                print(f"Responses.data not found at {responses_file}")
                return

            with open(responses_file, "r", encoding='utf-8') as file:
                messages = file.read().strip()
                if messages and messages != self.last_content:
                    self.last_content = messages
                    # Split messages into lines and get the last assistant message
                    lines = messages.split('\n')
                    assistant_lines = [line for line in lines if line.startswith(f"{AssistantName}:") and line.strip()]
                    if assistant_lines:
                        latest_reply = assistant_lines[-1]  # Get the last assistant message
                        self.reply_text_edit.setText(latest_reply)
                    else:
                        self.reply_text_edit.setText("No reply available.")
        except Exception as e:
            print(f"Error loading latest reply: {e}")

# Initial Screen
class InitialScreen(QWidget):
    def __init__(self, parent=None, flags=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header Layout (Welcome, User Name, Mic Button, Status, DateTime)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(20)

        # Welcome Label
        welcome_label = QLabel(f"Welcome to {AssistantName} AI")
        welcome_label.setStyleSheet("""
            font-size: 36px;
            font-family: 'Segoe UI';
            font-weight: bold;
            background: transparent;
            color: #d4af37;
            padding: 20px;
        """)
        welcome_label.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(welcome_label)

        # Custom User Name Label (Right Corner)
        user_name = load_user_name()
        self.user_name_label = QLabel(user_name)
        self.user_name_label.setStyleSheet("""
            font-size: 36px;
            font-family: 'Segoe UI';
            font-weight: bold;
            background: transparent;
            color: #d4af37;
            padding: 20px;
        """)
        self.user_name_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.user_name_label)

        # Microphone Toggle Button
        self.mic_button = QPushButton()
        self.mic_on_icon = QIcon(GraphicDirectoryPath('Mic_on.png'))
        if self.mic_on_icon.isNull():
            print("Warning: Mic_on.png not found for mic button")
        self.mic_off_icon = QIcon(GraphicDirectoryPath('Mic_off.png'))
        if self.mic_off_icon.isNull():
            print("Warning: Mic_off.png not found for mic button")
        self.mic_toggled = False  # Start with mic off
        self.mic_button.setIcon(self.mic_off_icon)  # Initialize as Mic Off
        self.mic_button.setIconSize(QSize(60, 60))
        self.mic_button.setFixedSize(100, 100)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, stop:0 #d4af37, stop:1 transparent);
                border-radius: 50px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, stop:0 #b8860b, stop:1 transparent);
            }
        """)
        self.mic_button.clicked.connect(self.toggle_mic)
        header_layout.addWidget(self.mic_button)

        # Status Label
        self.status_label = QLabel("Available")
        self.status_label.setStyleSheet("""
            color: #d4af37;
            font-size: 18px;
            font-family: 'Segoe UI';
            background: transparent;
            padding: 10px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.status_label)

        # Date, Day, Time Label (End of the Line, Creative Style)
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-family: 'Segoe Script', 'Comic Sans MS', cursive;
            font-weight: bold;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 215, 0, 0.3), stop:1 rgba(255, 255, 255, 0.1));
            border-radius: 10px;
            padding: 10px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        """)
        self.datetime_label.setAlignment(Qt.AlignRight)
        self.update_datetime()
        header_layout.addWidget(self.datetime_label)

        layout.addLayout(header_layout)

        # Content Area (Below Header) - Split Side by Side
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 10)
        content_layout.setSpacing(10)

        # Left Half: GIF Placeholder
        gif_container = QWidget()
        gif_layout = QVBoxLayout(gif_container)
        gif_layout.setContentsMargins(0, 0, 0, 0)

        gif_label = QLabel()
        movie_path = GraphicDirectoryPath('NatAI.gif')
        movie = QMovie(movie_path)
        if movie.isValid():
            gif_width = screen_width // 2  # Half the screen width
            gif_height = int(gif_width * 9 / 16)  # Maintain aspect ratio (16:9)
            movie.setScaledSize(QSize(gif_width, gif_height))
            gif_label.setAlignment(Qt.AlignCenter)
            gif_label.setMovie(movie)
            movie.start()
        else:
            print(f"Warning: Failed to load GIF at {movie_path}")
        gif_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        gif_layout.addWidget(gif_label)

        content_layout.addWidget(gif_container)

        # Right Half: Reply Section and Message Input (Vertically Stacked, Reply Above Message)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Top Part: Reply Section
        reply_container = QWidget()
        reply_layout = QVBoxLayout(reply_container)
        reply_layout.setContentsMargins(0, 0, 0, 0)
        reply_layout.setSpacing(10)

        # Add a label for the reply section
        reply_label = QLabel("Latest Reply")
        reply_label.setStyleSheet("""
            font-size: 18px;
            font-family: 'Segoe UI';
            color: #d4af37;
            background: transparent;
            padding: 5px;
        """)
        reply_label.setAlignment(Qt.AlignCenter)
        reply_layout.addWidget(reply_label)

        self.reply_section = ReplySection()
        self.reply_section.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        reply_layout.addWidget(self.reply_section)

        right_layout.addWidget(reply_container)
        right_layout.setStretch(0, 1)  # Reply section takes 50% of the space

        # Bottom Part: Message Input
        message_container = QWidget()
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(10)

        # Add a label for the message section
        message_label = QLabel("Message")
        message_label.setStyleSheet("""
            font-size: 18px;
            font-family: 'Segoe UI';
            color: #d4af37;
            background: transparent;
            padding: 5px;
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_layout.addWidget(message_label)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Segoe UI';
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        message_layout.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)
        send_button.clicked.connect(self.send_message)
        message_layout.addWidget(send_button)

        right_layout.addWidget(message_container)
        right_layout.setStretch(1, 1)  # Message section takes 50% of the space

        content_layout.addWidget(right_container)

        layout.addLayout(content_layout)

        self.setLayout(layout)
        self.setStyleSheet("background: #1e3a8a;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(100)

    def SpeechRecogText(self):
        status = GetAssistantStatus()
        if status.lower() == "listening":
            self.status_label.setText("Listening...")
        elif status.lower() == "answering":
            self.status_label.setText("Answering...")
        else:
            self.status_label.setText("Available")

    def toggle_mic(self):
        if self.mic_toggled:
            self.mic_button.setIcon(self.mic_off_icon)
            MicButtonInitialed()  # Sets Mic.data to "False"
        else:
            self.mic_button.setIcon(self.mic_on_icon)
            MicButtonClosed()  # Sets Mic.data to "True"
        self.mic_toggled = not self.mic_toggled

    def update_datetime(self):
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d, %A, %H:%M:%S")
        self.datetime_label.setText(formatted_time)

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            query_file = os.path.join(TempDirPath, 'Query.data')
            try:
                with open(query_file, "w", encoding='utf-8') as file:
                    file.write(QueryModifier(message))
                    file.flush()  # Ensure the write is completed
                print(f"Message written to Query.data: {message}")
                self.message_input.clear()
                SetAssistantStatus("listening")
            except Exception as e:
                print(f"Error writing to Query.data: {e}")

# Settings Screen
class SettingsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Settings")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-family: 'Segoe UI';
            font-weight: bold;
            color: #d4af37;
            background: transparent;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Custom Name Input Section
        name_layout = QHBoxLayout()
        name_label = QLabel("Custom Name")
        name_label.setStyleSheet("""
            font-size: 18px;
            font-family: 'Segoe UI';
            color: #d4af37;
            background: transparent;
        """)
        name_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name...")
        self.name_input.setText(load_user_name())
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Segoe UI';
            }
        """)
        self.name_input.returnPressed.connect(self.save_name)
        name_layout.addWidget(self.name_input)

        save_name_button = QPushButton("Save")
        save_name_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)
        save_name_button.clicked.connect(self.save_name)
        name_layout.addWidget(save_name_button)

        layout.addLayout(name_layout)

        # Volume Control Section
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Speaker Volume")
        volume_label.setStyleSheet("""
            font-size: 18px;
            font-family: 'Segoe UI';
            color: #d4af37;
            background: transparent;
        """)
        volume_layout.addWidget(volume_label)

        decrease_button = QPushButton("-")
        decrease_button.setStyleSheet("""
            QPushButton {
                background: #8b4513;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #5a2e0b;
            }
        """)
        decrease_button.clicked.connect(self.decrease_volume)
        volume_layout.addWidget(decrease_button)

        increase_button = QPushButton("+")
        increase_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)
        increase_button.clicked.connect(self.increase_volume)
        volume_layout.addWidget(increase_button)

        layout.addLayout(volume_layout)
        layout.addStretch(1)
        self.setLayout(layout)
        self.setStyleSheet("background: #1e3a8a;")

    def save_name(self):
        name = self.name_input.text().strip()
        save_user_name(name)
        initial_screen = self.parent().widget(0)
        initial_screen.user_name_label.setText(name)

    def increase_volume(self):
        keyboard.press_and_release("volume up")

    def decrease_volume(self):
        keyboard.press_and_release("volume down")

# Message Screen (Restored with Chat Section)
class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Chat Section
        self.chat_section = ChatSection()
        self.chat_section.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        layout.addWidget(self.chat_section)

        # Message Input at the Bottom
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(50, 10, 50, 20)
        message_layout.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Segoe UI';
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        message_layout.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)
        send_button.clicked.connect(self.send_message)
        message_layout.addWidget(send_button)

        layout.addLayout(message_layout)
        self.setLayout(layout)
        self.setStyleSheet("background: #1e3a8a;")

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            query_file = os.path.join(TempDirPath, 'Query.data')
            try:
                with open(query_file, "w", encoding='utf-8') as file:
                    file.write(QueryModifier(message))
                    file.flush()  # Ensure the write is completed
                print(f"Message written to Query.data: {message}")
                self.message_input.clear()
                SetAssistantStatus("listening")
            except Exception as e:
                print(f"Error writing to Query.data: {e}")

# Custom Topbar
class CustomTopbar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        layout.setContentsMargins(10, 5, 10, 5)

        # Title Label
        title_label = QLabel(f" {AssistantName.capitalize()} AI ")
        title_label.setStyleSheet("""
            color: #d4af37;
            font-size: 20px;
            font-family: 'Segoe UI';
            font-weight: bold;
            background: transparent;
            padding: 5px 15px;
            border-radius: 10px;
        """)

        # Buttons
        home_button = QPushButton()
        home_icon = QIcon(GraphicDirectoryPath("Home.png"))
        if home_icon.isNull():
            print("Warning: Home.png not found for home button")
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)

        message_button = QPushButton()
        message_icon = QIcon(GraphicDirectoryPath("Chat.png"))
        if message_icon.isNull():
            print("Warning: Chat.png not found for message button")
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)

        settings_button = QPushButton()
        settings_icon = QIcon(GraphicDirectoryPath("Settings.png"))
        if settings_icon.isNull():
            print("Warning: Settings.png not found for settings button")
        settings_button.setIcon(settings_icon)
        settings_button.setText(" Settings")
        settings_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)

        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicDirectoryPath('Minimize2.png'))
        if minimize_icon.isNull():
            print("Warning: Minimize2.png not found for minimize button")
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)
        minimize_button.clicked.connect(self.minimizeWindow)

        self.half_minimize_button = QPushButton()
        half_minimize_icon = QIcon(GraphicDirectoryPath('Maximize.png'))
        if half_minimize_icon.isNull():
            print("Warning: Maximize.png not found for half minimize button")
        self.half_minimize_button.setIcon(half_minimize_icon)
        self.half_minimize_button.setStyleSheet("""
            QPushButton {
                background: #d4af37;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #b8860b;
            }
        """)
        self.half_minimize_button.clicked.connect(self.halfMinimizeWindow)

        close_button = QPushButton()
        close_icon = QIcon(GraphicDirectoryPath('Close.png'))
        if close_icon.isNull():
            print("Warning: Close.png not found for close button")
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("""
            QPushButton {
                background: #8b4513;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #5a2e0b;
            }
        """)
        close_button.clicked.connect(self.closeWindow)

        # Connect buttons to screens
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addWidget(settings_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.half_minimize_button)
        layout.addWidget(close_button)

        self.draggable = True
        self.offset = None
        self.setStyleSheet("background: rgba(0, 0, 0, 0.5); border-radius: 10px;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()  # Fully minimize to taskbar

    def halfMinimizeWindow(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        half_width = screen_width // 2
        half_height = screen_height // 2
        self.parent().showNormal()  # Ensure the window is not maximized
        self.parent().setGeometry(0, 0, half_width, half_height)
        # Center the window on the screen
        self.parent().move((screen_width - half_width) // 2, (screen_height - half_height) // 2)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

        # Variables for resizing
        self.resizing = False
        self.resize_direction = None
        self.resize_pos = None
        self.resize_rect = None
        self.resize_margin = 5  # Margin for detecting edges

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        # Main stacked widget
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        settings_screen = SettingsScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        stacked_widget.addWidget(settings_screen)

        # Set geometry and background
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setMinimumSize(800, 600)  # Minimum size constraint
        self.setStyleSheet("background: #1e3a8a;")

        # Set top bar and central widget
        top_bar = CustomTopbar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

    def mousePressEvent(self, event):
        pos = event.pos()
        self.resize_pos = pos
        self.resize_rect = self.geometry()

        # Determine resize direction based on mouse position
        left = pos.x() < self.resize_margin
        right = pos.x() > self.width() - self.resize_margin
        top = pos.y() < self.resize_margin
        bottom = pos.y() > self.height() - self.resize_margin

        if left and top:
            self.resize_direction = "top-left"
            self.setCursor(Qt.SizeFDiagCursor)
        elif right and top:
            self.resize_direction = "top-right"
            self.setCursor(Qt.SizeBDiagCursor)
        elif left and bottom:
            self.resize_direction = "bottom-left"
            self.setCursor(Qt.SizeBDiagCursor)
        elif right and bottom:
            self.resize_direction = "bottom-right"
            self.setCursor(Qt.SizeFDiagCursor)
        elif left:
            self.resize_direction = "left"
            self.setCursor(Qt.SizeHorCursor)
        elif right:
            self.resize_direction = "right"
            self.setCursor(Qt.SizeHorCursor)
        elif top:
            self.resize_direction = "top"
            self.setCursor(Qt.SizeVerCursor)
        elif bottom:
            self.resize_direction = "bottom"
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)

        if self.resize_direction:
            self.resizing = True

    def mouseMoveEvent(self, event):
        if self.resizing:
            pos = event.pos()
            new_rect = QRect(self.resize_rect)

            if "left" in self.resize_direction:
                delta_x = pos.x() - self.resize_pos.x()
                new_rect.setLeft(self.resize_rect.left() + delta_x)
            if "right" in self.resize_direction:
                delta_x = pos.x() - self.resize_pos.x()
                new_rect.setRight(self.resize_rect.right() + delta_x)
            if "top" in self.resize_direction:
                delta_y = pos.y() - self.resize_pos.y()
                new_rect.setTop(self.resize_rect.top() + delta_y)
            if "bottom" in self.resize_direction:
                delta_y = pos.y() - self.resize_pos.y()
                new_rect.setBottom(self.resize_rect.bottom() + delta_y)

            # Enforce minimum size
            min_width = 800
            min_height = 600
            if new_rect.width() < min_width:
                if "left" in self.resize_direction:
                    new_rect.setLeft(new_rect.right() - min_width)
                else:
                    new_rect.setRight(new_rect.left() + min_width)
            if new_rect.height() < min_height:
                if "top" in self.resize_direction:
                    new_rect.setTop(new_rect.bottom() - min_height)
                else:
                    new_rect.setBottom(new_rect.top() + min_height)

            self.setGeometry(new_rect)

        else:
            # Update cursor based on mouse position
            pos = event.pos()
            left = pos.x() < self.resize_margin
            right = pos.x() > self.width() - self.resize_margin
            top = pos.y() < self.resize_margin
            bottom = pos.y() > self.height() - self.resize_margin

            if (left and top) or (right and bottom):
                self.setCursor(Qt.SizeFDiagCursor)
            elif (right and top) or (left and bottom):
                self.setCursor(Qt.SizeBDiagCursor)
            elif left or right:
                self.setCursor(Qt.SizeHorCursor)
            elif top or bottom:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.resize_direction = None
        self.setCursor(Qt.ArrowCursor)

def GraphicalUserInterface():
    append_data_from_directory()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()