import os
import random
import json
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
from .nlp_engine import predict_class

def main(context):
    # Appwrite Setup
    client = Client()
    client.set_endpoint(os.environ.get('APPWRITE_ENDPOINT', 'https://fra.cloud.appwrite.io/v1'))
    client.set_project(os.environ.get('APPWRITE_PROJECT_ID', '6953d25b0006cc1ceea5'))
    client.set_key(os.environ.get('APPWRITE_API_KEY'))
    
    databases = Databases(client)
    
    db_id = os.environ.get('APPWRITE_DATABASE_ID', 'nwu_chatbot_db')
    coll_patterns = os.environ.get('APPWRITE_COLLECTION_PATTERNS', 'patterns')
    coll_responses = os.environ.get('APPWRITE_COLLECTION_RESPONSES', 'responses')
    coll_logs = 'logs'

    try:
        # ... (Parsing Input logic remains same)
        if context.req.body:
            payload = json.loads(context.req.body)
            user_msg = payload.get('message', '')
        else:
            return context.res.json({"error": "No message provided"}, 400)

        if not user_msg:
            return context.res.json({"error": "Empty message"}, 400)

        # 2. Fetch Patterns from Appwrite
        patterns_response = databases.list_documents(db_id, coll_patterns, [
            Query.limit(100) 
        ])
        patterns_data = patterns_response['documents']

        # 3. Predict Intent
        intent_tag = predict_class(user_msg, patterns_data)

        matched = False
        if intent_tag:
            # 4. Fetch Responses for this intent
            responses_response = databases.list_documents(db_id, coll_responses, [
                Query.equal('intent_tag', intent_tag)
            ])
            responses = [r['text'] for r in responses_response['documents']]
            
            if responses:
                final_response = random.choice(responses)
                matched = True
            else:
                final_response = "I found the intent but have no response configured."
        else:
            # Fallback
            final_response = "I'm sorry, I didn't quite understand that. Could you please rephrase your question about NWU?"

        # 5. Log the Query
        try:
            databases.create_document(db_id, coll_logs, 'unique()', {
                'query': user_msg,
                'response': final_response,
                'intent_tag': intent_tag or 'unknown',
                'matched': matched
            })
        except Exception as log_err:
            context.error(f"Logging error: {log_err}")

        return context.res.json({
            "message": final_response,
            "intent": intent_tag
        })

    except Exception as e:
        context.error(str(e))
        return context.res.json({"error": str(e)}, 500)
