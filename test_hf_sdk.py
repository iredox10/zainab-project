import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv('HF_API_TOKEN')
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

client = InferenceClient(model=MODEL_ID, token=HF_API_TOKEN)

print(f"Testing with InferenceClient and model: {MODEL_ID}")
try:
    # Feature extraction returns the embedding
    embedding = client.feature_extraction("Hello world")
    print(f"Success! Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
except Exception as e:
    print(f"Error: {e}")
