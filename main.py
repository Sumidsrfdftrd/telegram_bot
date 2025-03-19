#!/usr/bin/env python3
import os
import json
import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

mode_times = {"hacker": 0, "money": 0, "playboy": 0}
current_mode = None
start_time = None
# Load environment variables
TOKEN = os.getenv("TOKEN")  # Set this in Railway's environment variables
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

# Handle user messages
def handle_message(text):
    global current_mode, mode_times, start_time
    current_time = time.time()
    if current_mode is not None:
            elapsed_time = current_time - start_time
            mode_times[current_mode] += elapsed_time
    start_time = current_time
    if text in ["/hacker", "/money", "/playboy"]:
        current_mode = text[1:]
        return f"Switched to {text[1:]} mode!"
    elif text == "/summary":
        hacker = int(mode_times["hacker"])
        money = int(mode_times["money"])
        playboy = int(mode_times["playboy"])

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
