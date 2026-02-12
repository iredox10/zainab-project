// NWU Chatbot Script
const body = document.body;
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const restartBtn = document.getElementById('restart-btn');
const suggestChips = document.querySelectorAll('.suggest-chip');

// Use /api if hosted on Netlify, otherwise use current hostname:5000
const isLocal = ['localhost', '127.0.0.1', '0.0.0.0', '', 'null'].includes(window.location.hostname) || 
                window.location.hostname.startsWith('192.168.') || 
                window.location.hostname.startsWith('10.') ||
                window.location.protocol === 'file:';

const PROXY_URL = isLocal 
    ? (window.location.hostname === '' || window.location.hostname === 'null' || window.location.protocol === 'file:' 
        ? 'http://127.0.0.1:5000/chat' 
        : `http://${window.location.hostname}:5000/chat`)
    : '/api/chat';

console.log('Using Proxy URL:', PROXY_URL);

let isChatStarted = false;

// Transition from Landing to Chat
function startChatTransition() {
    if (!isChatStarted) {
        body.classList.remove('state-landing');
        body.classList.add('state-chat');
        isChatStarted = true;
    }
}

// Send Message
async function sendMessage(customMessage = null) {
    const message = customMessage || userInput.value.trim();
    if (!message) return;

    // Trigger transition on first message
    startChatTransition();

    // Add user message to UI
    appendMessage('user', message);
    userInput.value = '';

    // Add typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(PROXY_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            const text = await response.text();
            let errorMsg = `Server error ${response.status}`;
            try {
                const errorData = JSON.parse(text);
                errorMsg = errorData.error || errorMsg;
            } catch (e) {
                // If not JSON, use the raw text if it's short, or just the status
                if (text.length < 100) errorMsg = text;
            }
            throw new Error(errorMsg);
        }

        const text = await response.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('Invalid JSON response:', text);
            throw new Error('Received invalid data from server. Check console for details.');
        }
        
        removeTypingIndicator(typingId);
        
        if (data.message) {
            appendMessage('bot', data.message);
        } else {
            appendMessage('bot', "I'm sorry, I'm having trouble connecting to my brain right now.");
        }
    } catch (error) {
        console.error('Error calling proxy:', error);
        removeTypingIndicator(typingId);
        appendMessage('bot', `Error: ${error.message}`);
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
    typingDiv.textContent = 'Assistant is typing...';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Event Listeners
sendBtn.addEventListener('click', () => sendMessage());

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Suggestion Chips
suggestChips.forEach(chip => {
    chip.addEventListener('click', () => {
        sendMessage(chip.textContent);
    });
});

// Restart Session
restartBtn.addEventListener('click', () => {
    chatMessages.innerHTML = '';
    body.classList.remove('state-chat');
    body.classList.add('state-landing');
    isChatStarted = false;
    userInput.value = '';
    userInput.focus();
});
