import os
import json
from appwrite.client import Client
from appwrite.services.functions import Functions
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query

# Appwrite Configuration from Netlify Env Vars
endpoint = os.getenv('APPWRITE_ENDPOINT', 'https://fra.cloud.appwrite.io/v1')
project_id = os.getenv('APPWRITE_PROJECT_ID', '6953d25b0006cc1ceea5')
api_key = os.getenv('APPWRITE_API_KEY')

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

functions_service = Functions(client)
databases = Databases(client)

DB_ID = 'nwu_chatbot_db'

def handler(event, context):
    path = event['path'].replace('/api/', '')
    method = event['httpMethod']
    
    # Enable CORS
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
    }

    if method == 'OPTIONS':
        return {"statusCode": 200, "headers": headers, "body": "OK"}

    try:
        body = json.loads(event.get('body', '{}'))
        
        # 1. Chat Proxy
        if path == 'chat' and method == 'POST':
            execution = functions_service.create_execution(
                function_id='chatbot_brain',
                body=json.dumps({"message": body.get('message')})
            )
            return {"statusCode": 200, "headers": headers, "body": execution['responseBody']}

        # 2. Login Proxy
        if path == 'login' and method == 'POST':
            user_client = Client().set_endpoint(endpoint).set_project(project_id)
            user_account = Account(user_client)
            session = user_account.create_email_password_session(body.get('email'), body.get('password'))
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "success", "session": session})}

        # 3. Stats Proxy
        if path == 'stats' and method == 'GET':
            logs = databases.list_documents(DB_ID, 'logs', [Query.limit(100), Query.order_desc('$createdAt')])
            intents = databases.list_documents(DB_ID, 'intents')
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"logs": logs, "intents": intents})}

        # 4. Data Proxy (Generic CRUD)
        if 'data/' in path:
            collection = path.split('/')[-1]
            params = event.get('queryStringParameters', {})
            
            if method == 'GET':
                queries = [Query.limit(100)]
                if params.get('tag'):
                    queries.append(Query.equal('intent_tag', params.get('tag')))
                result = databases.list_documents(DB_ID, collection, queries)
                return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
            
            if method == 'POST':
                result = databases.create_document(DB_ID, collection, 'unique()', body)
                return {"statusCode": 200, "headers": headers, "body": json.dumps(result)}
                
            if method == 'DELETE':
                doc_id = params.get('id')
                databases.delete_document(DB_ID, collection, doc_id)
                return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "deleted"})}

        return {"statusCode": 404, "headers": headers, "body": "Not Found"}

    except Exception as e:
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}
