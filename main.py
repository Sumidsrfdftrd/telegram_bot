#!/usr/bin/env python3
import os
import json
import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Load environment variables
TOKEN = os.getenv("TOKEN")  # Set this in Railway's environment variables
DATA_FILE = "user_modes.txt"
PORT = int(os.environ.get("PORT", 8080))  # Railway assigns this dynamically

# Function to set the Telegram bot webhook
def set_webhook():
    railway_url = os.getenv("RAILWAY_URL")  # Set this in Railway's environment variables
    if not railway_url:
        print("RAILWAY_URL is not set. Exiting...")
        exit(1)
    webhook_url = f"{railway_url}/webhook"
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    if response.status_code == 200:
        print("Webhook set successfully!")
    else:
        print(f"Failed to set webhook: {response.text}")

# Handle incoming webhook requests
class TelegramWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        
        update = json.loads(post_data)
        chat_id = update["message"]["chat"]["id"]
        message_text = update["message"]["text"]
        print(f"Received message: {message_text} from Chat ID: {chat_id}")
        
        response_text = handle_message(message_text)
        send_message(chat_id, response_text)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

# Load and save user mode data
def load_user_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"mode": None, "start_time": None, "total_time": {"hacker": 0, "money": 0, "playboy": 0}}

def save_user_data(user_data):
    with open(DATA_FILE, "w") as file:
        json.dump(user_data, file)

# Handle user messages
def handle_message(text):
    user_data = load_user_data()
    current_time = time.time()
    
    if user_data["mode"]:
        elapsed_time = current_time - user_data["start_time"]
        user_data["total_time"][user_data["mode"]] += elapsed_time
    
    user_data["start_time"] = current_time
    save_user_data(user_data)
    user_data = load_user_data()
    if text in ["/hacker", "/money", "/playboy"]:
        user_data["mode"] = text[1:]
        save_user_data(user_data)
        return f"Switched to {text[1:]} mode!"
    
    elif text == "/summary":
        total_time = user_data.get("total_time", {})
        hacker = int(total_time.get("hacker", 0))
        money = int(total_time.get("money", 0))
        playboy = int(total_time.get("playboy", 0))

        hacker_print = money_print = playboy_print = 0

        if 2 * hacker >= money and hacker >= playboy:
            money_print = 2 * hacker - money
            playboy_print = hacker - playboy
        elif money >= 2 * hacker and money >= 2 * playboy:
            hacker_print = int(money / 2 - hacker)
            playboy_print = int(money / 2 - playboy)
        elif playboy >= hacker and 2 * playboy >= money:
            money_print = 2 * playboy - money
            hacker_print = playboy - hacker

        sorted_values = dict(sorted({
            "hacker_print": hacker_print,
            "money_print": money_print,
            "playboy_print": playboy_print
        }.items(), key=lambda x: x[1], reverse=True))
        
        current_mode = user_data.get("mode", "Unknown").capitalize()
        message_lines = [f"{key.replace('_print', '').capitalize()} => {format_time(value)}" for key, value in sorted_values.items()]
        return f"Current Mode: {current_mode}\n\n" + "\n\n".join(message_lines)
    
    return "/hacker\n/money\n/playboy\n/summary"

# Format time display
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours:02}:{minutes:02}"

# Send a message to Telegram
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# Start the webhook server
def start_server():
    server = HTTPServer(("0.0.0.0", PORT), TelegramWebhookHandler)
    print(f"Listening on port {PORT}...")
    server.serve_forever()

# Main function
if __name__ == "__main__":
    set_webhook()
    start_server()
