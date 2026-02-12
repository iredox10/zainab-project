import os
import random
import json
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
from .nlp_engine import get_hf_client, get_query_embedding, predict_intent_semantic

def main(context):
    # Appwrite Setup
    client = Client()
    client.set_endpoint(os.environ.get('APPWRITE_ENDPOINT', 'https://fra.cloud.appwrite.io/v1'))
    client.set_project(os.environ.get('APPWRITE_PROJECT_ID', '6953d25b0006cc1ceea5'))
    client.set_key(os.environ.get('APPWRITE_API_KEY'))
    
    hf_token = os.environ.get('HF_API_TOKEN')
    hf_client = get_hf_client(hf_token)
    
    databases = Databases(client)
    
    db_id = os.environ.get('APPWRITE_DATABASE_ID', 'nwu_chatbot_db')
    coll_embeddings = 'embeddings'
    coll_responses = os.environ.get('APPWRITE_COLLECTION_RESPONSES', 'responses')
    coll_settings = 'settings'
    coll_logs = 'logs'

    try:
        # ... (Input parsing remains)
        if context.req.body:
            payload = json.loads(context.req.body)
            user_msg = payload.get('message', '')
        else:
            return context.res.json({"error": "No message provided"}, 400)

        if not user_msg:
            return context.res.json({"error": "Empty message"}, 400)

        # 2. Fetch Threshold from Settings
        # Semantic threshold is usually lower, default to 0.5
        threshold = 0.5
        try:
            settings_resp = databases.list_documents(db_id, coll_settings, [Query.equal('key', 'threshold')])
            if settings_resp['documents']:
                threshold = float(settings_resp['documents'][0]['value'])
        except Exception as e:
            context.error(f"Settings fetch error: {e}")

        # 3. Get User Query Embedding
        query_vector = get_query_embedding(user_msg, hf_client)
        if not query_vector:
            return context.res.json({"error": "Failed to generate query embedding"}, 500)

        # 4. Fetch Stored Embeddings from Appwrite
        embeddings_response = databases.list_documents(db_id, coll_embeddings, [
            Query.limit(5000) 
        ])
        embeddings_data = embeddings_response['documents']
        context.log(f"Fetched {len(embeddings_data)} embeddings for semantic matching.")

        # 5. Predict Intent Semantically
        intent_tag, confidence = predict_intent_semantic(query_vector, embeddings_data, threshold=threshold)
        context.log(f"Predicted intent: {intent_tag} with confidence {confidence}")

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
