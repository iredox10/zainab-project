from flask import Flask, request, jsonify
from flask_cors import CORS
from appwrite.client import Client
from appwrite.services.functions import Functions
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Appwrite Configuration
endpoint = os.getenv('APPWRITE_ENDPOINT')
project_id = os.getenv('APPWRITE_PROJECT_ID')
api_key = os.getenv('APPWRITE_API_KEY')

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

functions = Functions(client)
account = Account(client)
databases = Databases(client)

DB_ID = 'nwu_chatbot_db'

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    if not message:
        return jsonify({"error": "No message provided"}), 400
    try:
        execution = functions.create_execution(
            function_id='chatbot_brain',
            body=json.dumps({"message": message})
        )
        return jsonify(json.loads(execution['responseBody']))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    try:
        # Verify credentials by creating a session on a clean client
        user_client = Client().set_endpoint(endpoint).set_project(project_id)
        user_account = Account(user_client)
        session = user_account.create_email_password_session(email, password)
        return jsonify({"status": "success", "session": session})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        logs = databases.list_documents(DB_ID, 'logs', [Query.limit(100), Query.order_desc('$createdAt')])
        intents = databases.list_documents(DB_ID, 'intents')
        return jsonify({"logs": logs, "intents": intents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<collection>', methods=['GET', 'POST', 'DELETE'])
def handle_data(collection):
    coll_id = collection
    try:
        if request.method == 'GET':
            query_tag = request.args.get('tag')
            queries = [Query.limit(100)]
            if query_tag:
                queries.append(Query.equal('intent_tag', query_tag))
            result = databases.list_documents(DB_ID, coll_id, queries)
            return jsonify(result)
        
        if request.method == 'POST':
            result = databases.create_document(DB_ID, coll_id, 'unique()', request.json)
            return jsonify(result)
            
        if request.method == 'DELETE':
            doc_id = request.args.get('id')
            databases.delete_document(DB_ID, coll_id, doc_id)
            return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("NWU Chatbot Advanced Proxy starting on http://localhost:5000")
    app.run(port=5000)
