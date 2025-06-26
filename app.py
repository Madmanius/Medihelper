# WhatsApp Medical Chatbot (Dr. Sahayak) - Using Twilio + Flask + Hugging Face API + .env + Retry (Sandbox-Safe)

# Step 1: Prerequisites
# Install required libraries:
# pip install flask twilio requests python-dotenv

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env
load_dotenv()

# Step 2: Initialize Flask
app = Flask(__name__)

# Step 3: Hugging Face Inference API Setup
HUGGINGFACE_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "aaditya/Llama3-OpenBioLLM-70B"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

# Step 4: Chat State (temporary in-memory; use DB/Redis for production)
chat_history = {}

# Step 5: Helper - Generate Response via Hugging Face Inference API (with retries)
def generate_response(user_id, user_input):
    if not HUGGINGFACE_API_TOKEN:
        return "Hugging Face API token not set. Please contact admin."

    prompt = f"""
You are Dr. Sahayak, an AI medical assistant for India. Follow a 5-step process:
1. Clarification (ask for symptom details)
2. Virtual Physical Examination (ask about vitals)
3. Suggest home-based tests (like SpO2, sugar, etc.)
4. Risk-based Diagnosis: LOW / MEDIUM / HIGH
5. Treatment advice only for LOW risk (OTC or home care)

ALWAYS say: \"I am not a doctor, please consult a professional for serious issues.\"

User: {user_input}
Dr. Sahayak:
"""

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 150, "do_sample": True}
    }

    for attempt in range(3):  # Retry logic
        try:
            response = requests.post(HF_API_URL, headers=HEADERS, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result[0]["generated_text"].split("Dr. Sahayak:")[-1].strip()
            elif response.status_code == 503:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                return f"Hugging Face API error: {response.status_code}"
        except Exception as e:
            time.sleep(2 ** attempt)
            last_error = str(e)

    return f"Error generating response: {last_error}"

# Step 6: Webhook for Twilio
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

# Step 7: Run App (Only if running outside sandboxed environments)
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        port=int(os.environ.get("PORT", 5000)))
    except SystemExit:
        print("Flask exited cleanly in restricted environment.")

# ---
# Twilio Setup:
# 1. Buy a WhatsApp sandbox number on Twilio.
# 2. Set the webhook to: https://<your-server>/whatsapp
# 3. Test using WhatsApp: send a message to your Twilio number.

# For Production:
# - Use a DB instead of in-memory chat history
# - Enable logging, multilingual support, and secure API error handling
# - Store HF_API_TOKEN securely and avoid hardcoding in production
