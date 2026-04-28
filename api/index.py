from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app) 

# Abhi testing ke liye purani AI Studio key
GOOGLE_API_KEY = "AIzaSyDBst6e5UgWrCsItjEJhuFT1SXNgrvBq8c"
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/', methods=['GET'])
def home():
    return "🚀 Aakash's Vercel Backend is Live!"

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        if not user_prompt:
            return jsonify({"success": False, "error": "Prompt empty!"}), 400

        response = model.generate_content(user_prompt)
        return jsonify({"success": True, "answer": response.text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
