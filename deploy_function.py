import os
import tarfile
import io
from appwrite.client import Client
from appwrite.services.functions import Functions
from appwrite.input_file import InputFile
from dotenv import load_dotenv

load_dotenv()

# Appwrite Connection
endpoint = os.getenv('APPWRITE_ENDPOINT')
project_id = os.getenv('APPWRITE_PROJECT_ID')
api_key = os.getenv('APPWRITE_API_KEY')

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

functions = Functions(client)

function_id = 'chatbot_brain'
path = 'functions/chatbot_brain'

def create_tar_gz():
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as tar:
        tar.add(path, arcname='.')
    return out.getvalue()

def deploy():
    print(f"Deploying function {function_id}...")
    
    # We need to write the tar.gz to a file because the SDK might expect a file path or InputFile
    tar_data = create_tar_gz()
    with open('code.tar.gz', 'wb') as f:
        f.write(tar_data)
    
    try:
        # The SDK create_deployment usually takes an InputFile
        result = functions.create_deployment(
            function_id = function_id,
            code = InputFile.from_path('code.tar.gz'),
            activate = True
        )
        print(f"Deployment successful: {result['$id']}")
    except Exception as e:
        print(f"Deployment failed: {e}")

if __name__ == "__main__":
    deploy()
