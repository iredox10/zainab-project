import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from appwrite.client import Client
from appwrite.services.functions import Functions
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Appwrite Configuration
endpoint = os.getenv('APPWRITE_ENDPOINT')
project_id = os.getenv('APPWRITE_PROJECT_ID')
api_key = os.getenv('APPWRITE_API_KEY')
function_id = 'chatbot_brain'

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

functions = Functions(client)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Call the Appwrite Function from the server-side
        # This bypasses browser CORS issues
        execution = functions.create_execution(
            function_id=function_id,
            body=json.dumps({"message": message})
        )
        
        # Parse the response from the function
        response_data = json.loads(execution['responseBody'])
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Proxy Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("NWU Chatbot Proxy starting on http://localhost:5000")
    app.run(port=5000)
