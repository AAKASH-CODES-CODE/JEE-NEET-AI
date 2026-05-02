from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import time
import random

app = Flask(__name__)
CORS(app)

# 1️⃣ Gemini API Keys (Aapki pehle wali 14 keys)
GEMINI_KEYS = [os.environ.get(f"GEMINI_KEY_{i}") for i in range(1, 15)]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k] 

OPENROUTER_KEYS = [os.environ.get("OPENROUTER_KEY_1"), os.environ.get("OPENROUTER_KEY_2")]
OPENROUTER_KEYS = [k for k in OPENROUTER_KEYS if k]

SYSTEM_PROMPT = "You are an Expert JEE/NEET tutor. Format math strictly with $$. Explain concepts clearly, accurately and step-by-step."

@app.route('/', methods=['GET'])
def home():
    return "🚀 Aakash's Master AI Backend is Live with Gemini Vision!"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    history = data.get('history', '') 
    engine = data.get('engine', 'gemini')
    image_data = data.get('image', None) # Base64 Image

    if not user_prompt and not image_data:
        return jsonify({"success": False, "error": "Sawal ya photo bhejein bhai!"}), 400

    full_prompt = history if history else f"{SYSTEM_PROMPT}\n\nStudent Query: {user_prompt}"

    # ==========================================
    # 📷 AGAR PHOTO AAYI HAI (New Gemini Vision Logic)
    # ==========================================
    if image_data:
        if not GEMINI_KEYS:
            return jsonify({"success": False, "error": "Gemini keys missing in Vercel!"}), 500

        # Random key select karega taaki limit cross na ho
        api_key = random.choice(GEMINI_KEYS)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # Text aur Photo dono ek sath Gemini ko bhejenge
        payload = {
            "contents": [{
                "parts": [
                    {"text": full_prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
                ]
            }],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "generationConfig": {
                "temperature": 0.2 # Kam temperature = zyada accurate math calculation
            }
        }
        
        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if res.status_code == 200:
                answer = res.json()['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"success": True, "answer": answer})
            else:
                return jsonify({"success": False, "error": f"Gemini Error: {res.text}"}), 500
        except Exception as e:
            return jsonify({"success": False, "error": f"Server Error: {str(e)}"}), 500

    # ==========================================
    # ✍️ NORMAL TEXT LOGIC (Pehle jaisa)
    # ==========================================
    if engine == 'gemini' and GEMINI_KEYS:
        api_key = random.choice(GEMINI_KEYS)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]}
        }
        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            if res.status_code == 200:
                answer = res.json()['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"success": True, "answer": answer})
        except:
            pass

    # Yahan aapka OpenRouter ka text logic aa jayega (agar aap use kar rahe ho)
    
    return jsonify({"success": False, "error": "Engine failed to respond"}), 500
