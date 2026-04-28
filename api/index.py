from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import time

app = Flask(__name__)
CORS(app)

# 1️⃣ Vercel locker se Keys nikalna (14 keys tak support karega)
GEMINI_KEYS = [os.environ.get(f"GEMINI_KEY_{i}") for i in range(1, 15)]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k] 

OPENROUTER_KEYS = [os.environ.get("OPENROUTER_KEY_1"), os.environ.get("OPENROUTER_KEY_2")]
OPENROUTER_KEYS = [k for k in OPENROUTER_KEYS if k]

SYSTEM_PROMPT = "You are an Expert JEE/NEET tutor. Format math strictly with $$. Explain concepts clearly and concisely."

# 2️⃣ Smart Timeout Tracker (Keys ko limit hit hone par block karne ke liye)
BLOCKED_KEYS = {}
COOLDOWN_TIME = 4 * 60 * 60  # 4 hours in seconds

@app.route('/', methods=['GET'])
def home():
    return "🚀 Aakash's Secure Multi-Engine Backend is Live!"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    history = data.get('history', '') # Frontend se poori history aayegi
    engine = data.get('engine', 'gemini') # Default Gemini

    if not user_prompt:
        return jsonify({"success": False, "error": "Prompt khali hai bhai!"}), 400

    # 🧠 AI Context Builder (History + Naya Sawal)
    if history:
        full_prompt = history # Agar frontend ne pichli chat history bheji hai
    else:
        full_prompt = f"{SYSTEM_PROMPT}\n\nStudent Query: {user_prompt}"

    last_error = ""
    current_time = time.time()

    # 🤖 AGAR GEMINI BUTTON DABAYA HAI
    if engine == 'gemini':
        # Sirf wahi keys lo jo Blocked nahi hain
        healthy_keys = [k for k in GEMINI_KEYS if BLOCKED_KEYS.get(k, 0) < current_time]
        
        if not healthy_keys:
            return jsonify({"success": False, "error": "Saari Gemini keys abhi limit me hain (Cooldown). Thodi der baad try karein."}), 503

        # Fast loop: Ek fail hui toh turant doosri healthy key
        for key in healthy_keys:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }
            try:
                res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
                
                if res.status_code == 200:
                    answer = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return jsonify({"success": True, "answer": answer})
                
                elif res.status_code in [429, 503]: # Agar Limit cross ho gayi
                    BLOCKED_KEYS[key] = current_time + COOLDOWN_TIME # Key 4 ghante ke liye Block
                    last_error = "Rate limit hit, switched to next key."
                    continue 
                else:
                    last_error = res.text
                    continue 
            except Exception as e:
                last_error = str(e)
                continue

        return jsonify({"success": False, "error": f"API issue. Last Error: {last_error}"}), 500

    # 🌐 AGAR OPENROUTER BUTTON DABAYA HAI
    elif engine == 'openrouter':
        healthy_or_keys = [k for k in OPENROUTER_KEYS if BLOCKED_KEYS.get(k, 0) < current_time]

        if not healthy_or_keys:
            return jsonify({"success": False, "error": "OpenRouter keys abhi cooldown mein hain."}), 503

        url = "https://openrouter.ai/api/v1/chat/completions"
        free_models = [
            "google/gemini-2.0-flash-exp:free",
            "mistralai/mistral-7b-instruct:free",
            "cognitivecomputations/dolphin3.0-r1-mistral-24b:free"
        ]

        for key in healthy_or_keys:
            for model_name in free_models:
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jee-neet-ai.vercel.app", 
                    "X-Title": "JEE NEET AI Tutor"
                }
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": full_prompt}]
                }
                try:
                    res = requests.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        answer = res.json()['choices'][0]['message']['content']
                        return jsonify({"success": True, "answer": answer})
                    elif res.status_code in [429, 503]: 
                        BLOCKED_KEYS[key] = current_time + (1 * 60 * 60) # OR limit hit, 1 ghante block
                        last_error = "OpenRouter Limit hit."
                        break # Sidha next key par jao
                    else:
                        last_error = res.text
                        continue
                except Exception as e:
                    last_error = str(e)
                    continue
        
        return jsonify({"success": False, "error": f"OpenRouter fail ho gaya. Last Error: {last_error}"}), 500

    else:
        return jsonify({"success": False, "error": "Invalid engine selected."}), 400
