# WhatsApp Medical Chatbot (Dr. Sahayak) - Twilio + Flask + Hugging Face Gradio API + .env + Retry

# Step 1: Prerequisites
# pip install flask twilio requests python-dotenv

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Step 2: Initialize Flask app
app = Flask(__name__)

# Step 3: Gradio-hosted Hugging Face Space API
HF_API_URL = "https://siegfred-aaditya-llama3-openbiollm-70b.hf.space/run/predict"
HEADERS = {"Content-Type": "application/json"}  # No Bearer token needed

# Step 4: Generate response using Space's API
def generate_response(user_id, user_input):
    prompt = f"""
You are Dr. Sahayak, an AI medical assistant for India. Follow a 5-step process:
1. Clarification (ask for symptom details)
2. Virtual Physical Examination (ask about vitals)
3. Suggest home-based tests (like SpO2, sugar, etc.)
4. Risk-based Diagnosis: LOW / MEDIUM / HIGH
5. Treatment advice only for LOW risk (OTC or home care)

ALWAYS say: "I am not a doctor, please consult a professional for serious issues."

User: {user_input}
Dr. Sahayak:
"""

    payload = {
        "data": [prompt]
    }

    for attempt in range(3):
        try:
            response = requests.post(HF_API_URL, headers=HEADERS, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["data"][0].strip()
            elif response.status_code == 503:
                time.sleep(2 ** attempt)
                continue
            else:
                return f"HF Space error: {response.status_code}"
        except Exception as e:
            time.sleep(2 ** attempt)
            last_error = str(e)

    return f"Error generating response: {last_error}"

# Step 5: Twilio webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "").strip()
    user_number = request.values.get("From", "")

    if not incoming_msg:
        return str(MessagingResponse().message("Sorry, I didn’t understand that."))

    reply_text = generate_response(user_number, incoming_msg)
    response = MessagingResponse()
    response.message(reply_text)
    return str(response)

# Optional homepage
@app.route("/", methods=["GET"])
def home():
    return "✅ Dr. Sahayak is running. Use WhatsApp to chat."

# Step 6: Run app
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    except SystemExit:
        print("Flask exited cleanly in restricted environment.")

# ---
# Twilio Setup:
# 1. Join WhatsApp sandbox on Twilio
# 2. Set webhook to: https://<your-render-app>.onrender.com/whatsapp
# 3. Send a message to test it
