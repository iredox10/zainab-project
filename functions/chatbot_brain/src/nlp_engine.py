import os
import json
import numpy as np
from huggingface_hub import InferenceClient

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

def get_hf_client(token):
    return InferenceClient(model=MODEL_ID, token=token)

def get_query_embedding(text, hf_client):
    try:
        # returns a list or numpy array of floats
        vector = hf_client.feature_extraction(text)
        if hasattr(vector, 'tolist'):
            return vector.tolist()
        return vector
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0
    return dot_product / (norm_v1 * norm_v2)

def predict_intent_semantic(query_vector, embeddings_data, threshold=0.5):
    """
    query_vector: list of floats
    embeddings_data: list of documents from Appwrite 'embeddings' collection
    """
    results = []
    for doc in embeddings_data:
        try:
            pattern_vector = json.loads(doc['embedding'])
            similarity = cosine_similarity(query_vector, pattern_vector)
            results.append({
                'tag': doc['intent_tag'],
                'score': similarity
            })
        except Exception:
            continue
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    if results and results[0]['score'] >= threshold:
        return results[0]['tag'], results[0]['score']
    
    return None, 0
