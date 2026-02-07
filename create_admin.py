import os
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

def create_admin():
    email = "admin@nwu.edu.ng"
    password = "AdminPassword123"
    name = "NWU Admin"
    
    print(f"Creating admin user: {email}...")
    try:
        result = users.create('unique()', email, None, password, name)
        print(f"Admin user created successfully! ID: {result['$id']}")
        print(f"Login at: http://localhost:8000/login.html")
        print(f"Email: {email}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    create_admin()
