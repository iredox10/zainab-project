from flask import Flask, request, jsonify
from flask_cors import CORS
from appwrite.client import Client
from appwrite.services.functions import Functions
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query
from huggingface_hub import InferenceClient
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["*"])

# Appwrite Connection
endpoint = os.getenv('APPWRITE_ENDPOINT')
project_id = os.getenv('APPWRITE_PROJECT_ID')
api_key = os.getenv('APPWRITE_API_KEY')
hf_token = os.getenv('HF_API_TOKEN')

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

functions = Functions(client)
databases = Databases(client)
hf_client = InferenceClient(model="sentence-transformers/all-MiniLM-L6-v2", token=hf_token)

DB_ID = 'nwu_chatbot_db'
COLL_INTENTS = 'intents'
COLL_PATTERNS = 'patterns'
COLL_RESPONSES = 'responses'
COLL_LOGS = 'logs'
COLL_EMBEDDINGS = 'embeddings'

def generate_and_store_embedding(text, tag):
    try:
        vector = hf_client.feature_extraction(text)
        if hasattr(vector, 'tolist'):
            vector = vector.tolist()
        
        databases.create_document(DB_ID, COLL_EMBEDDINGS, 'unique()', {
            'intent_tag': tag,
            'pattern_text': text,
            'embedding': json.dumps(vector),
            'model': "sentence-transformers/all-MiniLM-L6-v2"
        })
        print(f"Stored semantic embedding for: {text}")
    except Exception as e:
        print(f"Embedding generation error: {e}")

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
        user_client = Client().set_endpoint(endpoint).set_project(project_id)
        user_account = Account(user_client)
        session = user_account.create_email_password_session(email, password)
        return jsonify({"status": "success", "session": session})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        logs = databases.list_documents(DB_ID, COLL_LOGS, [Query.limit(100), Query.order_desc('$createdAt')])
        intents = databases.list_documents(DB_ID, COLL_INTENTS)
        return jsonify({"logs": logs, "intents": intents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<collection>', methods=['GET', 'POST', 'DELETE', 'PUT'])
def handle_data(collection):
    try:
        if request.method == 'GET':
            query_tag = request.args.get('tag')
            queries = [Query.limit(100)]
            if query_tag:
                queries.append(Query.equal('intent_tag', query_tag))
            result = databases.list_documents(DB_ID, collection, queries)
            return jsonify(result)
        
        if request.method == 'POST':
            data = request.json
            result = databases.create_document(DB_ID, collection, 'unique()', data)
            
            # If adding a new pattern, also generate embedding
            if collection == COLL_PATTERNS:
                generate_and_store_embedding(data.get('text'), data.get('intent_tag'))
                
            return jsonify(result)
            
        if request.method == 'DELETE':
            doc_id = request.args.get('id')
            # If deleting an intent, also delete its patterns, responses, and embeddings
            if collection == COLL_INTENTS:
                intent = databases.get_document(DB_ID, COLL_INTENTS, doc_id)
                tag = intent['tag']
                # Delete patterns
                p_docs = databases.list_documents(DB_ID, COLL_PATTERNS, [Query.equal('intent_tag', tag)])
                for doc in p_docs['documents']:
                    databases.delete_document(DB_ID, COLL_PATTERNS, doc['$id'])
                # Delete responses
                r_docs = databases.list_documents(DB_ID, COLL_RESPONSES, [Query.equal('intent_tag', tag)])
                for doc in r_docs['documents']:
                    databases.delete_document(DB_ID, COLL_RESPONSES, doc['$id'])
                # Delete embeddings
                e_docs = databases.list_documents(DB_ID, COLL_EMBEDDINGS, [Query.equal('intent_tag', tag)])
                for doc in e_docs['documents']:
                    databases.delete_document(DB_ID, COLL_EMBEDDINGS, doc['$id'])
            
            # If deleting a specific pattern, delete its embedding too
            if collection == COLL_PATTERNS:
                pattern = databases.get_document(DB_ID, COLL_PATTERNS, doc_id)
                e_docs = databases.list_documents(DB_ID, COLL_EMBEDDINGS, [
                    Query.equal('intent_tag', pattern['intent_tag']),
                    Query.equal('pattern_text', pattern['text'])
                ])
                for doc in e_docs['documents']:
                    databases.delete_document(DB_ID, COLL_EMBEDDINGS, doc['$id'])

            databases.delete_document(DB_ID, collection, doc_id)
            return jsonify({"status": "deleted"})

        if request.method == 'PUT':
            doc_id = request.args.get('id')
            result = databases.update_document(DB_ID, collection, doc_id, request.json)
            return jsonify(result)

    except Exception as e:
        print(f"Data Error ({collection}): {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("NWU Chatbot Proxy v3 (Semantic) starting on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
