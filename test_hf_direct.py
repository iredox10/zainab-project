import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv('HF_API_TOKEN')
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

print(f"Testing standard Inference API URL: {API_URL}")
try:
    response = requests.post(API_URL, headers=headers, json={"inputs": "Hello world"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
