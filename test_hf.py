import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv('HF_API_TOKEN')
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

urls = [
    f"https://api-inference.huggingface.co/models/{MODEL_ID}",
    f"https://router.huggingface.co/models/{MODEL_ID}",
    f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}",
    f"https://router.huggingface.co/{MODEL_ID}"
]

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

for url in urls:
    print(f"Testing URL: {url}")
    try:
        response = requests.post(url, headers=headers, json={"inputs": "Hello world"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
