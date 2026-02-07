// NWU Chatbot Script
const chatToggle = document.getElementById('chat-toggle');
const chatWindow = document.getElementById('chat-window');
const closeChat = document.getElementById('close-chat');
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');

// Using a local proxy to bypass browser CORS restrictions
const PROXY_URL = 'http://localhost:5000/chat';

// Toggle Chat Window
chatToggle.addEventListener('click', () => {
    chatWindow.classList.toggle('hidden');
    if (!chatWindow.classList.contains('hidden')) {
        userInput.focus();
    }
});

closeChat.addEventListener('click', () => {
    chatWindow.classList.add('hidden');
});

// Send Message
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to UI
    appendMessage('user', message);
    userInput.value = '';

    // Add typing indicator
    const typingId = addTypingIndicator();

    try {
        // Call our local proxy instead of Appwrite directly
        const response = await fetch(PROXY_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        removeTypingIndicator(typingId);
        
        if (data.message) {
            appendMessage('bot', data.message);
        } else {
            appendMessage('bot', "I'm sorry, I'm having trouble connecting to my brain right now.");
        }
    } catch (error) {
        console.error('Error calling proxy:', error);
        removeTypingIndicator(typingId);
        appendMessage('bot', "Error: Could not connect to the proxy server. Make sure proxy.py is running.");
    }
}

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    msgDiv.textContent = text;
    chatMessages.appendChild(msgDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.classList.add('typing');
    typingDiv.textContent = 'NWU Bot is typing...';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
