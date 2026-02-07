import os
import json
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.permission import Permission
from appwrite.role import Role
from dotenv import load_dotenv

load_dotenv()

# Appwrite Connection
endpoint = os.getenv('APPWRITE_ENDPOINT')
project_id = os.getenv('APPWRITE_PROJECT_ID')
api_key = os.getenv('APPWRITE_API_KEY')

database_id = os.getenv('APPWRITE_DATABASE_ID', 'nwu_chatbot_db')
collection_intents = os.getenv('APPWRITE_COLLECTION_INTENTS', 'intents')
collection_patterns = os.getenv('APPWRITE_COLLECTION_PATTERNS', 'patterns')
collection_responses = os.getenv('APPWRITE_COLLECTION_RESPONSES', 'responses')

client = Client()
client.set_endpoint(endpoint)
client.set_project(project_id)
client.set_key(api_key)

databases = Databases(client)

def setup_database():
    print(f"Checking/Creating database: {database_id}...")
    try:
        databases.get(database_id)
        print("Database already exists.")
    except Exception:
        try:
            databases.create(database_id, database_id)
            print("Database created.")
        except Exception as e:
            print(f"Database creation failed: {e}")

    # 1. Intents Collection
    print(f"Checking collection: {collection_intents}...")
    try:
        databases.get_collection(database_id, collection_intents)
        print("Collection already exists.")
    except Exception:
        try:
            databases.create_collection(database_id, collection_intents, collection_intents, permissions=[
                Permission.read(Role.any()),
                Permission.write(Role.users()),
            ])
            databases.create_string_attribute(database_id, collection_intents, 'tag', 50, True)
            databases.create_string_attribute(database_id, collection_intents, 'description', 255, False)
            print("Collection created.")
        except Exception as e:
            print(f"Collection {collection_intents} error: {e}")

    # 2. Patterns Collection
    print(f"Checking collection: {collection_patterns}...")
    try:
        databases.get_collection(database_id, collection_patterns)
        print("Collection already exists.")
    except Exception:
        try:
            databases.create_collection(database_id, collection_patterns, collection_patterns, permissions=[
                Permission.read(Role.any()),
                Permission.write(Role.users()),
            ])
            databases.create_string_attribute(database_id, collection_patterns, 'text', 255, True)
            databases.create_string_attribute(database_id, collection_patterns, 'intent_tag', 50, True)
            print("Collection created.")
        except Exception as e:
            print(f"Collection {collection_patterns} error: {e}")

    # 3. Responses Collection
    print(f"Checking collection: {collection_responses}...")
    try:
        databases.get_collection(database_id, collection_responses)
        print("Collection already exists.")
    except Exception:
        try:
            databases.create_collection(database_id, collection_responses, collection_responses, permissions=[
                Permission.read(Role.any()),
                Permission.write(Role.users()),
            ])
            databases.create_string_attribute(database_id, collection_responses, 'text', 1000, True)
            databases.create_string_attribute(database_id, collection_responses, 'intent_tag', 50, True)
            print("Collection created.")
        except Exception as e:
            print(f"Collection {collection_responses} error: {e}")

def migrate_data():
    with open('data/intents.json', 'r') as f:
        data = json.load(f)

    for item in data['intents']:
        tag = item['tag']
        print(f"Migrating tag: {tag}...")
        
        # Add Intent
        try:
            databases.create_document(database_id, collection_intents, 'unique()', {
                'tag': tag,
                'description': f"Queries related to {tag}"
            })
        except Exception as e:
            print(f"Error adding intent {tag}: {e}")

        # Add Patterns
        for p in item['patterns']:
            try:
                databases.create_document(database_id, collection_patterns, 'unique()', {
                    'text': p,
                    'intent_tag': tag
                })
            except Exception as e:
                print(f"Error adding pattern '{p}': {e}")

        # Add Responses
        for r in item['responses']:
            try:
                databases.create_document(database_id, collection_responses, 'unique()', {
                    'text': r,
                    'intent_tag': tag
                })
            except Exception as e:
                print(f"Error adding response: {e}")

if __name__ == "__main__":
    setup_database()
    print("Wait 15 seconds for attributes to be indexed...")
    import time
    time.sleep(15) 
    migrate_data()
    print("Data migration complete.")
