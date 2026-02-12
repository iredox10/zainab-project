import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv('HF_API_TOKEN')
# MODEL_ID = "BAAI/bge-small-en-v1.5"
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
API_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

print(f"Testing Router URL: {API_URL}")
try:
    response = requests.post(API_URL, headers=headers, json={"inputs": "Hello world"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
