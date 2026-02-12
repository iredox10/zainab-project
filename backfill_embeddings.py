import os
import json
import time
from huggingface_hub import InferenceClient
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
from dotenv import load_dotenv

load_dotenv()

# Configuration
HF_API_TOKEN = os.getenv('HF_API_TOKEN')
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

endpoint = os.getenv('APPWRITE_ENDPOINT')
project_id = os.getenv('APPWRITE_PROJECT_ID')
api_key = os.getenv('APPWRITE_API_KEY')
database_id = os.getenv('APPWRITE_DATABASE_ID', 'nwu_chatbot_db')

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

databases = Databases(client)
hf_client = InferenceClient(model=MODEL_ID, token=HF_API_TOKEN)

def get_embedding(text):
    try:
        # returns a list or numpy array of floats
        vector = hf_client.feature_extraction(text)
        # convert to list if it's a numpy array for json serialization
        if hasattr(vector, 'tolist'):
            return vector.tolist()
        return vector
    except Exception as e:
        print(f"Error from HF SDK: {e}")
        return None

def backfill_embeddings():
    print("Fetching all patterns...")
    # List patterns
    patterns_resp = databases.list_documents(database_id, 'patterns', [Query.limit(5000)])
    patterns = patterns_resp['documents']
    print(f"Found {len(patterns)} patterns.")

    # List existing embeddings to avoid duplicates
    existing_resp = databases.list_documents(database_id, 'embeddings', [Query.limit(5000)])
    existing_texts = {e['pattern_text'] for e in existing_resp['documents']}
    print(f"Found {len(existing_texts)} existing embeddings.")

    for p in patterns:
        text = p['text']
        tag = p['intent_tag']
        
        if text in existing_texts:
            print(f"Skipping existing: {text}")
            continue

        print(f"Generating embedding for: {text}")
        vector = get_embedding(text)
        
        if vector:
            try:
                databases.create_document(database_id, 'embeddings', 'unique()', {
                    'intent_tag': tag,
                    'pattern_text': text,
                    'embedding': json.dumps(vector),
                    'model': MODEL_ID
                })
                print(f"Stored embedding for: {text}")
            except Exception as e:
                print(f"Error storing embedding: {e}")
            
            # Rate limiting for free tier
            time.sleep(0.5)

if __name__ == "__main__":
    if not HF_API_TOKEN:
        print("HF_API_TOKEN not found in environment.")
    else:
        backfill_embeddings()
