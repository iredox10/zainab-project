const APPWRITE_ENDPOINT = process.env.APPWRITE_ENDPOINT || 'https://fra.cloud.appwrite.io/v1';
const APPWRITE_PROJECT_ID = process.env.APPWRITE_PROJECT_ID || '6953d25b0006cc1ceea5';
const APPWRITE_API_KEY = process.env.APPWRITE_API_KEY;

const DB_ID = 'nwu_chatbot_db';

async function appwriteRequest(path, options = {}) {
    const url = `${APPWRITE_ENDPOINT}${path}`;
    const headers = {
        'Content-Type': 'application/json',
        'X-Appwrite-Project': APPWRITE_PROJECT_ID,
        'X-Appwrite-Key': APPWRITE_API_KEY,
        ...options.headers
    };
    
    const response = await fetch(url, { ...options, headers });
    return response.json();
}

exports.handler = async (event, context) => {
    const full_path = event.path;
    let path = full_path;
    const prefixes = ['/.netlify/functions/api', '/api', '/.netlify/functions/index'];
    for (const p of prefixes) {
        path = path.replace(p, '');
    }
    path = path.replace(/^\//, '');
    
    const method = event.httpMethod;
    console.log(`DEBUG: original=${full_path} normalized=${path} method=${method}`);
    
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Content-Type': 'application/json'
    };

    if (method === 'OPTIONS') {
        return { statusCode: 200, headers, body: 'OK' };
    }

    if (path === 'ping') {
        return { statusCode: 200, headers, body: 'pong-netlify-js' };
    }

    try {
        const body = event.body ? JSON.parse(event.body) : {};
        const params = event.queryStringParameters || {};
        
        if (path === 'chat' && method === 'POST') {
            const response = await fetch(`${APPWRITE_ENDPOINT}/functions/chatbot_brain/executions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Appwrite-Project': APPWRITE_PROJECT_ID,
                    'X-Appwrite-Key': APPWRITE_API_KEY
                },
                body: JSON.stringify({
                    body: JSON.stringify({ message: body.message })
                })
            });
            const result = await response.json();
            
            if (result.responseBody) {
                return { statusCode: 200, headers, body: result.responseBody };
            } else {
                return { statusCode: 500, headers, body: JSON.stringify({ error: 'No response from function', details: result }) };
            }
        }

        if (path === 'login' && method === 'POST') {
            const response = await fetch(`${APPWRITE_ENDPOINT}/account/sessions/email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Appwrite-Project': APPWRITE_PROJECT_ID
                },
                body: JSON.stringify({
                    email: body.email,
                    password: body.password
                })
            });
            const result = await response.json();
            return { statusCode: 200, headers, body: JSON.stringify({ status: 'success', session: result }) };
        }

        if (path === 'stats' && method === 'GET') {
            const [logs, intents] = await Promise.all([
                appwriteRequest(`/databases/${DB_ID}/collections/logs/documents?queries[]=${encodeURIComponent(JSON.stringify({"limit": 100}))}&queries[]=${encodeURIComponent(JSON.stringify({"orderDesc": "$createdAt"}))}`),
                appwriteRequest(`/databases/${DB_ID}/collections/intents/documents`)
            ]);
            return { statusCode: 200, headers, body: JSON.stringify({ logs, intents }) };
        }

        if (path.startsWith('data/')) {
            const collection = path.replace('data/', '');
            
            if (method === 'GET') {
                let queryStr = `?queries[]=${encodeURIComponent(JSON.stringify({"limit": 100}))}`;
                if (params.tag) {
                    queryStr += `&queries[]=${encodeURIComponent(JSON.stringify({"equal": ["intent_tag", params.tag]}))}`;
                }
                const result = await appwriteRequest(`/databases/${DB_ID}/collections/${collection}/documents${queryStr}`);
                return { statusCode: 200, headers, body: JSON.stringify(result) };
            }
            
            if (method === 'POST') {
                const result = await appwriteRequest(`/databases/${DB_ID}/collections/${collection}/documents`, {
                    method: 'POST',
                    body: JSON.stringify({
                        documentId: 'unique()',
                        data: body
                    })
                });
                return { statusCode: 200, headers, body: JSON.stringify(result) };
            }
            
            if (method === 'DELETE') {
                const docId = params.id;
                
                if (collection === 'intents') {
                    const intent = await appwriteRequest(`/databases/${DB_ID}/collections/intents/documents/${docId}`);
                    const tag = intent.tag;
                    
                    const [patterns, responses, embeddings] = await Promise.all([
                        appwriteRequest(`/databases/${DB_ID}/collections/patterns/documents?queries[]=${encodeURIComponent(JSON.stringify({"equal": ["intent_tag", tag]}))}`),
                        appwriteRequest(`/databases/${DB_ID}/collections/responses/documents?queries[]=${encodeURIComponent(JSON.stringify({"equal": ["intent_tag", tag]}))}`),
                        appwriteRequest(`/databases/${DB_ID}/collections/embeddings/documents?queries[]=${encodeURIComponent(JSON.stringify({"equal": ["intent_tag", tag]}))}`)
                    ]);
                    
                    for (const doc of patterns.documents || []) {
                        await appwriteRequest(`/databases/${DB_ID}/collections/patterns/documents/${doc.$id}`, { method: 'DELETE' });
                    }
                    for (const doc of responses.documents || []) {
                        await appwriteRequest(`/databases/${DB_ID}/collections/responses/documents/${doc.$id}`, { method: 'DELETE' });
                    }
                    for (const doc of embeddings.documents || []) {
                        await appwriteRequest(`/databases/${DB_ID}/collections/embeddings/documents/${doc.$id}`, { method: 'DELETE' });
                    }
                }
                
                const result = await appwriteRequest(`/databases/${DB_ID}/collections/${collection}/documents/${docId}`, { method: 'DELETE' });
                return { statusCode: 200, headers, body: JSON.stringify({ status: 'deleted' }) };
            }
            
            if (method === 'PUT') {
                const docId = params.id;
                const result = await appwriteRequest(`/databases/${DB_ID}/collections/${collection}/documents/${docId}`, {
                    method: 'PATCH',
                    body: JSON.stringify({
                        data: body
                    })
                });
                return { statusCode: 200, headers, body: JSON.stringify(result) };
            }
        }

        return { statusCode: 404, headers, body: JSON.stringify({ error: 'Not Found', path }) };

    } catch (error) {
        console.error('Error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
