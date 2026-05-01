from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import time
import base64

app = Flask(__name__)
CORS(app)

# 1️⃣ Vercel locker se Keys nikalna
GEMINI_KEYS = [os.environ.get(f"GEMINI_KEY_{i}") for i in range(1, 15)]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k] 

OPENROUTER_KEYS = [os.environ.get("OPENROUTER_KEY_1"), os.environ.get("OPENROUTER_KEY_2")]
OPENROUTER_KEYS = [k for k in OPENROUTER_KEYS if k]

# 📷 Vision API Keys
HF_KEY = os.environ.get("HF_KEY")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_KEY = os.environ.get("CF_KEY")

SYSTEM_PROMPT = "You are an Expert JEE/NEET tutor. Format math strictly with $$. Explain concepts clearly and concisely."

# 2️⃣ Smart Timeout Tracker
BLOCKED_KEYS = {}
COOLDOWN_TIME = 4 * 60 * 60  # 4 hours in seconds

@app.route('/', methods=['GET'])
def home():
    return "🚀 Aakash's Secure Multi-Engine Backend is Live!"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    history = data.get('history', '') 
    engine = data.get('engine', 'gemini')
    image_data = data.get('image', None)

    if not user_prompt and not image_data:
        return jsonify({"success": False, "error": "Sawal ya photo toh bhejo bhai!"}), 400

    if history:
        full_prompt = history
    else:
        full_prompt = f"{SYSTEM_PROMPT}\n\nStudent Query: {user_prompt}"

    last_error = ""
    current_time = time.time()

    # ==========================================
    # 📷 AGAR PHOTO AAYI HAI (Vision Logic)
    # ==========================================
    if image_data:
        
        # STEP 1: Cloudflare Vision (Sabse Fast, Ab Unlock Ho Chuka Hai)
        if CF_KEY and CF_ACCOUNT_ID:
            try:
                # 🔥 FIX: Base64 ko array of bytes (numbers) mein convert karna
                img_bytes = base64.b64decode(image_data)
                img_array = list(img_bytes)

                cf_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"
                cf_headers = {"Authorization": f"Bearer {CF_KEY}", "Content-Type": "application/json"}
                
                # Naya Cloudflare REST API Payload format
                cf_payload = {
                    "prompt": full_prompt,
                    "image": img_array
                }
                
                res = requests.post(cf_url, headers=cf_headers, json=cf_payload, timeout=20)
                
                if res.status_code == 200:
                    response_json = res.json()
                    result_data = response_json.get('result', {})
                    if isinstance(result_data, dict):
                        answer = result_data.get('response', '')
                    else:
                        answer = str(result_data)
                    return jsonify({"success": True, "answer": answer})
                else:
                    last_error += f"CF Error: {res.text} | "
            except Exception as e:
                last_error += f"CF Exception: {str(e)} | "

        # STEP 2: Hugging Face Fallback (Agar CF by chance busy ho)
        if HF_KEY:
            try:
                # 🔥 FIX: HF ka naya URL aur format update kar diya hai
                hf_url = "https://api-inference.huggingface.co/v1/chat/completions"
                hf_headers = {"Authorization": f"Bearer {HF_KEY}", "Content-Type": "application/json"}
                hf_payload = {
                    "model": "meta-llama/Llama-3.2-11B-Vision-Instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": full_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
                res = requests.post(hf_url, headers=hf_headers, json=hf_payload, timeout=20)
                
                if res.status_code == 200:
                    answer = res.json()['choices'][0]['message']['content']
                    return jsonify({"success": True, "answer": answer})
                else:
                    last_error += f"HF Error: {res.text}"
            except Exception as e:
                last_error += f"HF Exception: {str(e)}"

        return jsonify({"success": False, "error": f"Dono Vision AI fail ho gaye. Errors: {last_error}"}), 500


    # ==========================================
    # ✍️ AGAR SIRF TEXT HAI (Gemini / OpenRouter)
    # ==========================================
    if engine == 'gemini':
        healthy_keys = [k for k in GEMINI_KEYS if BLOCKED_KEYS.get(k, 0) < current_time]

        if not healthy_keys:
            return jsonify({"success": False, "error": "Saari Gemini keys abhi cooldown me hain. Thodi der baad try karein."}), 503

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

                elif res.status_code in [429, 503]: 
                    BLOCKED_KEYS[key] = current_time + COOLDOWN_TIME 
                    last_error = "Rate limit hit, switched to next key."
                    continue 
                else:
                    last_error = res.text
                    continue 
            except Exception as e:
                last_error = str(e)
                continue

        return jsonify({"success": False, "error": f"API issue. Last Error: {last_error}"}), 500

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
                        BLOCKED_KEYS[key] = current_time + (1 * 60 * 60) 
                        last_error = "OpenRouter Limit hit."
                        break 
                    else:
                        last_error = res.text
                        continue
                except Exception as e:
                    last_error = str(e)
                    continue

        return jsonify({"success": False, "error": f"OpenRouter fail ho gaya. Last Error: {last_error}"}), 500

    else:
        return jsonify({"success": False, "error": "Invalid engine selected."}), 400
