# NWU Intelligent Chatbot (Serverless with Appwrite)

This is an automated enquiry system for Northwest University, Kano, built using Python (NLTK) and Appwrite.

## Features
- **Serverless Architecture:** Uses Appwrite Functions for NLP processing.
- **NLP Engine:** Utilizes NLTK's Bag of Words and Cosine Similarity for intent matching.
- **NWU Branding:** Custom UI with official university colors (Green & White).
- **Scalable Knowledge Base:** Admin can update fees, dates, and requirements via the Appwrite Console.

## Prerequisites
- Appwrite instance (Cloud or Self-hosted)
- Python 3.8+

## Setup Instructions

### 1. Appwrite Configuration
1. Create a project in Appwrite.
2. Create an API Key with `databases.read`, `databases.write`, `collections.read`, `collections.write`, `attributes.read`, `attributes.write`, `documents.read`, and `documents.write` scopes.
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your Endpoint, Project ID, and API Key
   ```

### 2. Database & Data Migration
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the setup script to create the database and migrate the initial FAQ data:
   ```bash
   python setup_appwrite.py
   ```

### 3. Deploy the Appwrite Function
1. In the Appwrite Console, go to **Functions** -> **Create Function**.
2. Select **Python 3.10** (or similar).
3. Connect your repository or upload the `functions/chatbot_brain` folder.
4. Set the **Entrypoint** to `src/main.py`.
5. Add the following **Environment Variables** in the function settings:
   - `APPWRITE_DATABASE_ID`: `nwu_chatbot_db`
   - `APPWRITE_COLLECTION_PATTERNS`: `patterns`
   - `APPWRITE_COLLECTION_RESPONSES`: `responses`
   - `APPWRITE_API_KEY`: (Your API Key)
6. Deploy the function.

### 4. Running the Application
1. Start the local CORS proxy (required to bypass browser security):
   ```bash
   python proxy.py
   ```
2. Serve the `web` folder:
   ```bash
   cd web
   python -m http.server 8000
   ```
3. Open `http://localhost:8000` in your browser.

## Folder Structure
- `data/`: Contains `intents.json` (raw training data).
- `functions/`: Appwrite serverless function source code.
- `web/`: Frontend files (HTML, CSS, JS).
- `setup_appwrite.py`: Automation script for database setup.
