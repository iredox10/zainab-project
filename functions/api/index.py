import os
import json
from appwrite.client import Client
from appwrite.services.functions import Functions
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query
from huggingface_hub import InferenceClient

DB_ID = 'nwu_chatbot_db'
COLL_INTENTS = 'intents'
COLL_PATTERNS = 'patterns'
COLL_RESPONSES = 'responses'
COLL_LOGS = 'logs'
COLL_EMBEDDINGS = 'embeddings'

def get_clients():
    endpoint = os.getenv('APPWRITE_ENDPOINT', 'https://fra.cloud.appwrite.io/v1')
    project_id = os.getenv('APPWRITE_PROJECT_ID', '6953d25b0006cc1ceea5')
    api_key = os.getenv('APPWRITE_API_KEY')
    hf_token = os.getenv('HF_API_TOKEN')
    
    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)
    
    functions_service = Functions(client)
    databases = Databases(client)
    hf_client = InferenceClient(model="sentence-transformers/all-MiniLM-L6-v2", token=hf_token)
    
    return functions_service, databases, hf_client, endpoint, project_id

def handler(event, context):
    full_path = event['path']
    path = full_path
    prefixes = ['/.netlify/functions/api', '/api', '/.netlify/functions/index']
    for p in prefixes:
        path = path.replace(p, '')
    path = path.strip('/')
    
    method = event['httpMethod']
    print(f"DEBUG: original={full_path} normalized={path} method={method}")
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
    }

    if method == 'OPTIONS':
        return {"statusCode": 200, "headers": headers, "body": "OK"}

    if path == 'ping':
        return {"statusCode": 200, "headers": headers, "body": "pong-v5"}

    try:
        functions_service, databases, hf_client, endpoint, project_id = get_clients()
        body = json.loads(event.get('body', '{}') or '{}')
        
        if path == 'chat' and method == 'POST':
            execution = functions_service.create_execution(
                function_id='chatbot_brain',
                body=json.dumps({"message": body.get('message')})
            )
            return {"statusCode": 200, "headers": headers, "body": execution['responseBody']}

        if path == 'login' and method == 'POST':
            user_client = Client().set_endpoint(endpoint).set_project(project_id)
            user_account = Account(user_client)
            session = user_account.create_email_password_session(body.get('email'), body.get('password'))
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "success", "session": session})}

        if path == 'stats' and method == 'GET':
            logs = databases.list_documents(DB_ID, 'logs', [Query.limit(100), Query.order_desc('$createdAt')])
            intents = databases.list_documents(DB_ID, 'intents')
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"logs": logs, "intents": intents})}

        if path.startswith('data/'):
            collection = path.replace('data/', '').split('/')[0]
            params = event.get('queryStringParameters', {}) or {}
            
            if method == 'GET':
                queries = [Query.limit(100)]
                if params.get('tag'):
                    queries.append(Query.equal('intent_tag', params.get('tag')))
                result = databases.list_documents(DB_ID, collection, queries)
                return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
            
            if method == 'POST':
                result = databases.create_document(DB_ID, collection, 'unique()', body)
                if collection == COLL_PATTERNS:
                    try:
                        vector = hf_client.feature_extraction(body.get('text'))
                        if hasattr(vector, 'tolist'):
                            vector = vector.tolist()
                        databases.create_document(DB_ID, COLL_EMBEDDINGS, 'unique()', {
                            'intent_tag': body.get('intent_tag'),
                            'pattern_text': body.get('text'),
                            'embedding': json.dumps(vector),
                            'model': "sentence-transformers/all-MiniLM-L6-v2"
                        })
                    except Exception as e:
                        print(f"Embedding error: {e}")
                return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
                
            if method == 'DELETE':
                doc_id = params.get('id')
                if collection == COLL_INTENTS:
                    intent = databases.get_document(DB_ID, COLL_INTENTS, doc_id)
                    tag = intent['tag']
                    p_docs = databases.list_documents(DB_ID, COLL_PATTERNS, [Query.equal('intent_tag', tag)])
                    for doc in p_docs['documents']: 
                        databases.delete_document(DB_ID, COLL_PATTERNS, doc['$id'])
                    r_docs = databases.list_documents(DB_ID, COLL_RESPONSES, [Query.equal('intent_tag', tag)])
                    for doc in r_docs['documents']: 
                        databases.delete_document(DB_ID, COLL_RESPONSES, doc['$id'])
                    e_docs = databases.list_documents(DB_ID, COLL_EMBEDDINGS, [Query.equal('intent_tag', tag)])
                    for doc in e_docs['documents']: 
                        databases.delete_document(DB_ID, COLL_EMBEDDINGS, doc['$id'])
                
                if collection == COLL_PATTERNS:
                    pattern = databases.get_document(DB_ID, COLL_PATTERNS, doc_id)
                    e_docs = databases.list_documents(DB_ID, COLL_EMBEDDINGS, [
                        Query.equal('intent_tag', pattern['intent_tag']),
                        Query.equal('pattern_text', pattern['text'])
                    ])
                    for doc in e_docs['documents']: 
                        databases.delete_document(DB_ID, COLL_EMBEDDINGS, doc['$id'])

                databases.delete_document(DB_ID, collection, doc_id)
                return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "deleted"})}

            if method == 'PUT':
                doc_id = params.get('id')
                result = databases.update_document(DB_ID, collection, doc_id, body)
                return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}

        return {"statusCode": 404, "headers": headers, "body": json.dumps({"error": "Not Found", "path": path})}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}
