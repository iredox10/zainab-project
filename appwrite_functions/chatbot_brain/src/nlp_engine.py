import os
import json
import numpy as np
import nltk
import string
from nltk.stem.lancaster import LancasterStemmer
from huggingface_hub import InferenceClient

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
stemmer = LancasterStemmer()

# Ensure NLTK data is available
nltk.data.path.append("/tmp/nltk_data")
for resource in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource, download_dir="/tmp/nltk_data")

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
    results = []
    for doc in embeddings_data:
        try:
            pattern_vector = json.loads(doc['embedding'])
            similarity = cosine_similarity(query_vector, pattern_vector)
            results.append({'tag': doc['intent_tag'], 'score': similarity})
        except Exception:
            continue
    results.sort(key=lambda x: x['score'], reverse=True)
    if results and results[0]['score'] >= threshold:
        return results[0]['tag'], results[0]['score']
    return None, 0

# --- Fallback Bag of Words Logic ---

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words if word not in string.punctuation]
    return sentence_words

def bag_of_words(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)  
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s: 
                bag[i] = 1
    return np.array(bag)

def predict_intent_bow(sentence, patterns_data, threshold=0.7):
    """
    patterns_data: list of documents from Appwrite 'patterns' collection
    """
    # Create vocabulary
    vocabulary = []
    for p in patterns_data:
        vocabulary.extend(clean_up_sentence(p['text']))
    vocabulary = sorted(list(set(vocabulary)))

    input_vec = bag_of_words(sentence, vocabulary)
    
    results = []
    for p in patterns_data:
        p_vec = bag_of_words(p['text'], vocabulary)
        # Dot product for BoW
        score = np.dot(input_vec, p_vec)
        
        # Normalize
        input_len = len(clean_up_sentence(sentence))
        normalized_score = score / input_len if input_len > 0 else 0
        results.append((p['intent_tag'], normalized_score))

    results.sort(key=lambda x: x[1], reverse=True)
    if results and results[0][1] >= threshold:
        return results[0][0], results[0][1]
    return None, 0
