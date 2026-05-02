from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import random

app = Flask(__name__)
CORS(app)

# 1️⃣ Gemini API Keys (Aapki Vercel wali keys)
GEMINI_KEYS = [os.environ.get(f"GEMINI_KEY_{i}") for i in range(1, 15)]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k] 

OPENROUTER_KEYS = [os.environ.get("OPENROUTER_KEY_1"), os.environ.get("OPENROUTER_KEY_2")]
OPENROUTER_KEYS = [k for k in OPENROUTER_KEYS if k]

SYSTEM_PROMPT = "You are an Expert JEE/NEET tutor. Format math strictly with $$. Explain concepts clearly, accurately and step-by-step."

@app.route('/', methods=['GET'])
def home():
    return "🚀 Aakash's Master AI Backend is Live with Gemini 2.5!"

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

    # 🔥 UPDATE: Gemini 2.5 Version
    MODEL_NAME = "gemini-2.5-flash"

    # ==========================================
    # 📷 AGAR PHOTO AAYI HAI
    # ==========================================
    if image_data:
        if not GEMINI_KEYS:
            return jsonify({"success": False, "error": "Gemini keys missing in Vercel!"}), 500

        api_key = random.choice(GEMINI_KEYS)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
        
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
                "temperature": 0.2
            }
        }
        
        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if res.status_code == 200:
                answer = res.json()['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"success": True, "answer": answer})
            else:
                return jsonify({"success": False, "error": f"Gemini 2.5 Error: {res.text}"}), 500
        except Exception as e:
            return jsonify({"success": False, "error": f"Server Error: {str(e)}"}), 500

    # ==========================================
    # ✍️ NORMAL TEXT LOGIC
    # ==========================================
    if engine == 'gemini' and GEMINI_KEYS:
        api_key = random.choice(GEMINI_KEYS)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]}
        }
        
        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            if res.status_code == 200:
                answer = res.json()['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"success": True, "answer": answer})
            else:
                # 🛡️ Fallback: Agar 2.5 kisi wajah se busy ho, toh stable 'gemini-pro' answer dega
                fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
                fallback_payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                res_fallback = requests.post(fallback_url, json=fallback_payload, headers={"Content-Type": "application/json"}, timeout=20)
                
                if res_fallback.status_code == 200:
                    answer = res_fallback.json()['candidates'][0]['content']['parts'][0]['text']
                    return jsonify({"success": True, "answer": answer})
                else:
                    return jsonify({"success": False, "error": f"Fallback Error: {res_fallback.text}"}), 500
        except Exception as e:
            return jsonify({"success": False, "error": f"Engine failed: {str(e)}"}), 500

    # OpenRouter Logic (agar select kiya ho)
    return jsonify({"success": False, "error": "Koi engine select nahi hua ya fail ho gaya"}), 500
