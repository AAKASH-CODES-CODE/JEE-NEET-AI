from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Vercel locker se keys nikalna
GEMINI_KEYS = [os.environ.get(f"GEMINI_KEY_{i}") for i in range(1, 15)]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k] 

OPENROUTER_KEYS = [os.environ.get("OPENROUTER_KEY_1"), os.environ.get("OPENROUTER_KEY_2")]
OPENROUTER_KEYS = [k for k in OPENROUTER_KEYS if k]

SYSTEM_PROMPT = "You are an Expert JEE/NEET tutor. Format math strictly with $$. Explain concepts clearly and concisely."

@app.route('/', methods=['GET'])
def home():
    return "🚀 Aakash's Secure Multi-Engine Backend is Live!"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    engine = data.get('engine', 'openrouter') 

    if not user_prompt:
        return jsonify({"success": False, "error": "Prompt khali hai bhai!"}), 400

    last_error = ""
    full_prompt = f"{SYSTEM_PROMPT}\n\nStudent Query: {user_prompt}"

    # 🤖 AGAR GEMINI BUTTON DABAYA HAI
    if engine == 'gemini':
        if not GEMINI_KEYS:
            return jsonify({"success": False, "error": "Vercel mein Gemini keys nahi mili!"}), 500
        
        for key in GEMINI_KEYS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }
            try:
                res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
                if res.status_code == 200:
                    answer = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return jsonify({"success": True, "answer": answer})
                else:
                    last_error = res.text
                    continue 
            except Exception as e:
                last_error = str(e)
                continue
        
        return jsonify({"success": False, "error": f"Saari Gemini keys busy hain. Last Error: {last_error}"}), 500

    # 🌐 AGAR OPENROUTER BUTTON DABAYA HAI
    elif engine == 'openrouter':
        if not OPENROUTER_KEYS:
            return jsonify({"success": False, "error": "Vercel mein OpenRouter keys nahi mili!"}), 500
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # 🔥 Master Auto-Fallback List: 3 Sabse Stable Free Models
        free_models = [
            "meta-llama/llama-3-8b-instruct:free",  # Model 1
            "mistralai/mistral-7b-instruct:free",   # Model 2
            "huggingfaceh4/zephyr-7b-beta:free"     # Model 3
        ]

        # Pehle Key 1 try hogi, phir saare models. Agar fail, toh Key 2 try hogi.
        for key in OPENROUTER_KEYS:
            for model_name in free_models:
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jee-neet-ai.vercel.app", 
                    "X-Title": "JEE NEET AI Tutor"
                }
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ]
                }
                try:
                    res = requests.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        answer = res.json()['choices'][0]['message']['content']
                        return jsonify({"success": True, "answer": answer})
                    else:
                        last_error = res.text
                        continue # Agar error aaya toh agla model try karo
                except Exception as e:
                    last_error = str(e)
                    continue
        
        return jsonify({"success": False, "error": f"OpenRouter API busy hai. Last Error: {last_error}"}), 500

    else:
        return jsonify({"success": False, "error": "Invalid engine selected."}), 400
