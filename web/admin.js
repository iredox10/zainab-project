const { Client, Account, Databases, Query } = Appwrite;

const PROXY_URL = 'http://localhost:5000';

// Auth Protection
async function checkAuth() {
    const session = localStorage.getItem('admin_session');
    if (!session) {
        window.location.href = 'login.html';
        return;
    }
    const sessionData = JSON.parse(session);
    document.getElementById('admin-email').textContent = sessionData.providerEmail || 'Admin';
    initDashboard();
}

// ... Tab Switching logic remains ...

// Analytics Logic
async function loadOverview() {
    const response = await fetch(`${PROXY_URL}/stats`);
    const data = await response.json();
    
    const logs = data.logs;
    const intents = data.intents;

    const total = logs.total;
    const matched = logs.documents.filter(l => l.matched).length;
    const successRate = total > 0 ? Math.round((matched / total) * 100) : 0;

    document.getElementById('total-queries').textContent = total;
    document.getElementById('success-rate').textContent = successRate + '%';

    // Top Intent
    const intentCounts = {};
    logs.documents.forEach(l => {
        if (l.intent_tag && l.intent_tag !== 'unknown') {
            intentCounts[l.intent_tag] = (intentCounts[l.intent_tag] || 0) + 1;
        }
    });
    const topIntent = Object.keys(intentCounts).length > 0 
        ? Object.keys(intentCounts).reduce((a, b) => intentCounts[a] > intentCounts[b] ? a : b) 
        : 'N/A';
    document.getElementById('top-intent').textContent = topIntent;

    renderCharts(logs.documents);
}

// ... renderCharts remains ...

// Knowledge Base Logic
async function loadKnowledgeBase() {
    const response = await fetch(`${PROXY_URL}/data/intents`);
    const intents = await response.json();
    const tbody = document.getElementById('intents-table-body');
    tbody.innerHTML = '';

    for (const intent of intents.documents) {
        const pResp = await fetch(`${PROXY_URL}/data/patterns?tag=${intent.tag}`);
        const patterns = await pResp.json();
        
        const rResp = await fetch(`${PROXY_URL}/data/responses?tag=${intent.tag}`);
        const responses = await rResp.json();

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${intent.tag}</strong></td>
            <td>${patterns.total} phrases</td>
            <td>${responses.total} answers</td>
            <td>
                <button class="btn-icon btn-delete" onclick="deleteIntent('${intent.$id}')"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    }
}

// Unanswered Logic
async function loadUnanswered() {
    const response = await fetch(`${PROXY_URL}/data/logs`);
    const allLogs = await response.json();
    const logs = allLogs.documents.filter(l => !l.matched);
    
    const tbody = document.getElementById('unanswered-table-body');
    tbody.innerHTML = '';

    logs.forEach(log => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${log.query}</td>
            <td>${new Date(log.$createdAt).toLocaleString()}</td>
            <td>
                <button class="btn-primary" onclick="teachBot('${log.query.replace(/'/g, "\\'")}')">Teach Bot</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Logs Logic
async function loadLogs() {
    const response = await fetch(`${PROXY_URL}/data/logs`);
    const logs = await response.json();
    const tbody = document.getElementById('logs-table-body');
    tbody.innerHTML = '';

    logs.documents.forEach(log => {
        const tr = document.createElement('tr');
        const statusClass = log.matched ? 'badge-success' : 'badge-error';
        tr.innerHTML = `
            <td>${log.query}</td>
            <td>${log.response.substring(0, 50)}...</td>
            <td>${log.intent_tag}</td>
            <td><span class="badge ${statusClass}">${log.matched ? 'Matched' : 'Fallback'}</span></td>
            <td>${new Date(log.$createdAt).toLocaleTimeString()}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Modal Logic
// ... (Open/Close remains same) ...

document.getElementById('intent-form').onsubmit = async (e) => {
    e.preventDefault();
    const tag = document.getElementById('modal-tag').value;
    const patterns = document.getElementById('modal-patterns').value.split('\n').filter(p => p.trim());
    const responses = document.getElementById('modal-responses').value.split('\n').filter(r => r.trim());

    try {
        // 1. Create Intent
        await fetch(`${PROXY_URL}/data/intents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag, description: `Queries about ${tag}` })
        });
        
        // 2. Create Patterns
        for (let p of patterns) {
            await fetch(`${PROXY_URL}/data/patterns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: p, intent_tag: tag })
            });
        }

        // 3. Create Responses
        for (let r of responses) {
            await fetch(`${PROXY_URL}/data/responses`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: r, intent_tag: tag })
            });
        }

        modal.style.display = 'none';
        loadKnowledgeBase();
        alert('Intent saved successfully!');
    } catch (err) {
        console.error(err);
        alert('Error saving intent.');
    }
};

async function deleteIntent(id) {
    if (confirm('Delete this intent?')) {
        await fetch(`${PROXY_URL}/data/intents?id=${id}`, { method: 'DELETE' });
        loadKnowledgeBase();
    }
}

// Logout
document.getElementById('logout-btn').onclick = async () => {
    localStorage.removeItem('admin_session');
    window.location.href = 'login.html';
};
