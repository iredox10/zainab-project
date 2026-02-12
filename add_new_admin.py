import os
import sys
from appwrite.client import Client
from appwrite.services.users import Users
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

users = Users(client)

def add_admin(email, password, name):
    print(f"Creating new admin user: {email}...")
    try:
        result = users.create('unique()', email, None, password, name)
        print(f"✅ Success! Admin created.")
        print(f"ID: {result['$id']}")
        print(f"Email: {email}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 add_new_admin.py <email> <password> [name]")
        print("Example: python3 add_new_admin.py staff@nwu.edu.ng MySecretPass 'Staff User'")
    else:
        email = sys.argv[1]
        password = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else "New Admin"
        add_admin(email, password, name)
