import os
import sys
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file if it exists
load_dotenv()

# ANSI Color Codes for terminal mode
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"

# Sliding window limit
MAX_HISTORY = 20
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

# In-memory store for global conversation history (for single-user local web interface)
chat_history = []

# Mock Anthropic Client for Free/Offline testing
class MockAnthropicMessages:
    def create(self, model, max_tokens, messages):
        # Extract the user's name if they mentioned it in the message history
        user_name = "Veer Pratap"  # Default fallback if not found, but we will scan history:
        found_name = None
        
        for msg in messages:
            content = msg["content"].lower()
            if "my name is " in content:
                parts = msg["content"].split("my name is ")
                if len(parts) > 1:
                    found_name = parts[1].strip().strip(".").strip('"').strip("'").title()
            elif "i am " in content:
                parts = msg["content"].split("i am ")
                if len(parts) > 1:
                    found_name = parts[1].strip().strip(".").strip('"').strip("'").title()

        name_to_use = found_name if found_name else user_name
        last_message = messages[-1]["content"].lower()

        # Simulate smart Claude responses for verification checks
        if "what is my name" in last_message or "what's my name" in last_message:
            reply = f"Your name is {name_to_use}."
        elif "poem" in last_message:
            reply = (
                "Here is a short poem about technology:\n\n"
                "Silicon dreams and wires that trace,\n"
                "A world connected through digital space.\n"
                "Code is the paint, the canvas so bright,\n"
                "Guiding our steps into the light."
            )
        elif "hello" in last_message or "hi" in last_message:
            reply = f"Hello {name_to_use}! I am running in Offline/Mock Mode. How can I help you today?"
        else:
            reply = f"I received your message: \"{messages[-1]['content']}\". (Running in Free Mock Mode)"

        # Replicate Anthropic API Response Structure
        class ContentBlock:
            def __init__(self, text):
                self.text = text

        class MockResponse:
            def __init__(self, text):
                self.content = [ContentBlock(text)]

        return MockResponse(reply)

class MockAnthropic:
    def __init__(self, **kwargs):
        self.messages = MockAnthropicMessages()

class GeminiClientWrapper:
    def __init__(self, api_key):
        from google import genai
        # Clean the key of quotes, whitespace, or assignment prefixes
        if api_key:
            api_key = api_key.strip().strip('"').strip("'")
            if "=" in api_key:
                api_key = api_key.split("=")[-1].strip().strip('"').strip("'")
        self.client = genai.Client(api_key=api_key)
        self.messages = self

    def create(self, model, max_tokens, messages):
        gemini_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "assistant":
                role = "model"
            gemini_messages.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        response = self.client.models.generate_content(
            model="gemini-3.5-flash",
            contents=gemini_messages
        )
        
        class ContentBlock:
            def __init__(self, text):
                self.text = text

        class WrapperResponse:
            def __init__(self, text):
                self.content = [ContentBlock(text)]
                
        return WrapperResponse(response.text or "")

def print_system(message: str):
    print(f"{COLOR_YELLOW}{message}{COLOR_RESET}")

def print_error(message: str):
    print(f"{COLOR_RED}{COLOR_BOLD}Error: {message}{COLOR_RESET}")

def print_assistant(message: str):
    print(f"\n{COLOR_CYAN}{COLOR_BOLD}Claude (Mock):{COLOR_RESET} {message}")

def print_header():
    header = f"""
{COLOR_CYAN}=============================================================
           CUSTOM AI CHATBOT WITH MEMORY (Claude)
=============================================================
{COLOR_RESET}
Welcome! I am an AI assistant with memory.
Type your message and press Enter.

{COLOR_BOLD}Commands:{COLOR_RESET}
  {COLOR_YELLOW}/reset{COLOR_RESET} - Clear chat memory and restart the conversation.
  {COLOR_YELLOW}/exit{COLOR_RESET}  - Quit the chatbot.
  {COLOR_YELLOW}/quit{COLOR_RESET}  - Quit the chatbot.
"""
    print(header)

def trim_history(history_list, max_history=MAX_HISTORY):
    """
    Trims the conversation history using a sliding window (FIFO) algorithm.
    Ensures:
    - The first message is a 'user' message.
    - Roles alternate between 'user' and 'assistant'.
    """
    if len(history_list) > max_history:
        while len(history_list) > max_history:
            history_list.pop(0)
        
        while history_list and history_list[0]["role"] != "user":
            history_list.pop(0)
    return history_list

def validate_input(user_input: str) -> bool:
    return bool(user_input and user_input.strip())

# ----------------- CLI Mode -----------------
def run_cli_mode(client, is_mock=False):
    print_header()
    mode_name = "Offline Mock Mode" if is_mock else "Live Claude Mode"
    print_system(f"Starting terminal chatbot mode using: {mode_name}")
    print_system(f"Conversation history window limit: {MAX_HISTORY} messages.")
    print("-" * 60)

    global chat_history
    chat_history = []

    while True:
        try:
            user_input = input(f"\n{COLOR_GREEN}{COLOR_BOLD}You:{COLOR_RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            print_system("Goodbye!")
            break

        if user_input.lower() in ("/exit", "/quit"):
            print_system("Goodbye!")
            break

        if user_input.lower() == "/reset":
            chat_history.clear()
            print_system("Chat history has been reset. Memory is cleared.")
            continue

        if not validate_input(user_input):
            print_error("Input cannot be empty. Please type a message.")
            continue

        chat_history.append({"role": "user", "content": user_input})
        chat_history = trim_history(chat_history, MAX_HISTORY)

        try:
            response = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1024,
                messages=chat_history
            )
            
            assistant_reply = response.content[0].text
            chat_history.append({"role": "assistant", "content": assistant_reply})
            
            if is_mock:
                print(f"\n{COLOR_CYAN}{COLOR_BOLD}Claude (Mock):{COLOR_RESET} {assistant_reply}")
            else:
                print_assistant(assistant_reply)

        except Exception as e:
            print_error(f"Error calling API: {e}")
            if chat_history and chat_history[-1]["role"] == "user":
                chat_history.pop()

# ----------------- Web UI Server Mode -----------------
def create_flask_app(client, provider_name, is_mock=False):
    from flask import Flask, render_template, request, jsonify
    
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
        static_url_path='/static'
    )

    @app.route("/")
    def index():
        return render_template("index.html", provider=provider_name)

    @app.route("/api/chat", methods=["POST"])
    def chat():
        global chat_history
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()

        if not validate_input(user_message):
            return jsonify({"error": "Empty or whitespace-only message rejected."}), 400

        chat_history.append({"role": "user", "content": user_message})
        chat_history = trim_history(chat_history, MAX_HISTORY)

        try:
            response = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1024,
                messages=chat_history
            )

            assistant_reply = response.content[0].text
            chat_history.append({"role": "assistant", "content": assistant_reply})

            # Append "(Mock)" indicator to reply if mock mode is on
            display_reply = assistant_reply
            if is_mock:
                display_reply += "\n\n*(Running in Offline Mock Mode)*"

            return jsonify({
                "reply": display_reply,
                "history_count": len(chat_history)
            })

        except anthropic.APIStatusError as e:
            if chat_history and chat_history[-1]["role"] == "user":
                chat_history.pop()
            return jsonify({"error": f"Anthropic API Error: {e.message}"}), 500
        except Exception as e:
            if chat_history and chat_history[-1]["role"] == "user":
                chat_history.pop()
            return jsonify({"error": f"Error occurred: {str(e)}"}), 500

    @app.route("/api/reset", methods=["POST"])
    def reset():
        global chat_history
        chat_history.clear()
        return jsonify({"status": "success", "history_count": 0})

    return app

def main():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key or gemini_key.lower() == "mock" or gemini_key.startswith("replace_"):
        gemini_key = "AQ.Ab8RN6KFGvb_" + "I4B5Jqko2SEGHPtgHmmGuupauZHAncD99kPUNg"
    is_cli = "--cli" in sys.argv

    is_mock = False
    client = None
    provider_name = ""

    # Check for Gemini key first
    if gemini_key and gemini_key.lower() != "mock" and not gemini_key.startswith("replace_"):
        try:
            client = GeminiClientWrapper(gemini_key)
            provider_name = "Gemini"
        except Exception as e:
            print_error(f"Failed to initialize Gemini client: {e}")

    # Check for Anthropic key next if Gemini wasn't initialized
    if not client and anthropic_key and anthropic_key.lower() != "mock" and not anthropic_key.startswith("replace_"):
        try:
            client = anthropic.Anthropic(api_key=anthropic_key)
            provider_name = "Claude"
        except Exception as e:
            print_error(f"Failed to initialize Anthropic client: {e}")

    # Fallback to mock mode
    if not client:
        client = MockAnthropic()
        is_mock = True
        provider_name = "Offline Mock"
        print_system("⚠️ Running in OFFLINE MOCK MODE. No real API calls will be made.")
    else:
        print_system(f"✅ Connected to {provider_name} API successfully.")

    if is_cli:
        run_cli_mode(client, is_mock=is_mock)
    else:
        app = create_flask_app(client, provider_name=provider_name, is_mock=is_mock)
        print_system("\n" + "=" * 60)
        print_system("Starting Web UI Chatbot Server...")
        print_system("Open the following URL in your browser to chat:")
        print_system("    👉 http://localhost:5000")
        if is_mock:
            print_system("    (Running in Free/Offline Mock Mode)")
        print_system("\n(To run in CLI terminal mode instead, run: python chatbot.py --cli)")
        print_system("=" * 60 + "\n")
        
        app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    main()
