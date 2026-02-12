// Use /api if hosted on Netlify, otherwise use localhost:5000
const isLocal = ['localhost', '127.0.0.1', '0.0.0.0'].includes(window.location.hostname) || 
                window.location.hostname.startsWith('192.168.') || 
                window.location.hostname.startsWith('10.') ||
                window.location.protocol === 'file:';

const PROXY_URL = isLocal 
    ? 'http://localhost:5000' 
    : '/api';

// State
let charts = {};
let currentIntents = [];

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

// Tab Switching
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const tabId = item.getAttribute('data-tab');
        
        document.querySelector('.nav-item.active').classList.remove('active');
        document.querySelector('.tab-pane.active').classList.remove('active');
        
        item.classList.add('active');
        document.getElementById(tabId).classList.add('active');
        document.getElementById('tab-title').textContent = item.textContent.trim();
        
        loadTabData(tabId);
    });
});

function loadTabData(tab) {
    if (tab === 'overview') loadOverview();
    if (tab === 'knowledge') loadKnowledgeBase();
    if (tab === 'unanswered') loadUnanswered();
    if (tab === 'logs') loadLogs();
    if (tab === 'settings') loadSettings();
}

// Analytics Logic
async function loadOverview() {
    try {
        const response = await fetch(`${PROXY_URL}/stats`);
        if (!response.ok) throw new Error(`Stats error: ${response.status}`);
        const data = await response.json();
        
        const logs = data.logs.documents || [];
        const total = data.logs.total || 0;
        const matched = logs.filter(l => l.matched).length;
        const successRate = total > 0 ? Math.round((matched / total) * 100) : 0;

        document.getElementById('total-queries').textContent = total;
        document.getElementById('success-rate').textContent = successRate + '%';

        const intentCounts = {};
        logs.forEach(l => {
            if (l.intent_tag && l.intent_tag !== 'unknown') {
                intentCounts[l.intent_tag] = (intentCounts[l.intent_tag] || 0) + 1;
            }
        });
        const topIntent = Object.keys(intentCounts).length > 0 
            ? Object.keys(intentCounts).reduce((a, b) => intentCounts[a] > intentCounts[b] ? a : b) 
            : 'N/A';
        document.getElementById('top-intent').textContent = topIntent;

        renderCharts(logs);
    } catch (err) {
        console.error('Overview error:', err);
    }
}

function renderCharts(logData) {
    const ctx1 = document.getElementById('volumeChart').getContext('2d');
    if (charts.volume) charts.volume.destroy();
    
    // Simple distribution for demo
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const data = [2, 5, 3, 8, 4, 6, logData.length]; 

    charts.volume = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Queries',
                data: data,
                borderColor: '#006837',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(0, 104, 55, 0.1)'
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });

    const ctx2 = document.getElementById('intentChart').getContext('2d');
    if (charts.intent) charts.intent.destroy();

    const intentCounts = {};
    logData.forEach(l => {
        const tag = l.intent_tag || 'unknown';
        intentCounts[tag] = (intentCounts[tag] || 0) + 1;
    });

    charts.intent = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: Object.keys(intentCounts),
            datasets: [{
                data: Object.values(intentCounts),
                backgroundColor: ['#006837', '#3b82f6', '#c5a059', '#64748b', '#ef4444', '#f59e0b']
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
}

// Knowledge Base Logic
async function loadKnowledgeBase() {
    const response = await fetch(`${PROXY_URL}/data/intents`);
    const data = await response.json();
    currentIntents = data.documents || [];
    renderIntentsTable(currentIntents);
}

function renderIntentsTable(intents) {
    const tbody = document.getElementById('intents-table-body');
    tbody.innerHTML = '';

    intents.forEach(intent => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${intent.tag}</strong></td>
            <td>Fetching...</td>
            <td>Fetching...</td>
            <td>
                <button class="btn-icon" onclick="editIntent('${intent.$id}', '${intent.tag}')"><i class="fas fa-edit"></i></button>
                <button class="btn-icon btn-delete" onclick="deleteIntent('${intent.$id}')"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
        updateCounts(intent.tag, tr);
    });
}

async function updateCounts(tag, row) {
    const pResp = await fetch(`${PROXY_URL}/data/patterns?tag=${tag}`);
    const patterns = await pResp.json();
    const rResp = await fetch(`${PROXY_URL}/data/responses?tag=${tag}`);
    const responses = await rResp.json();
    
    row.cells[1].textContent = `${patterns.total} phrases`;
    row.cells[2].textContent = `${responses.total} answers`;
}

// Unanswered Logic
async function loadUnanswered() {
    const response = await fetch(`${PROXY_URL}/data/logs`);
    const allLogs = await response.json();
    const logs = (allLogs.documents || []).filter(l => !l.matched);
    
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
    const data = await response.json();
    const logs = data.documents || [];
    const tbody = document.getElementById('logs-table-body');
    tbody.innerHTML = '';

    logs.forEach(log => {
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

// Settings Logic
async function loadSettings() {
    try {
        const response = await fetch(`${PROXY_URL}/data/settings`);
        const data = await response.json();
        const threshold = data.documents.find(s => s.key === 'threshold');
        if (threshold) {
            document.querySelector('.slider').value = parseFloat(threshold.value) * 100;
        }
    } catch (err) {
        console.error('Settings load error:', err);
    }
}

// CRUD Actions
async function deleteIntent(id) {
    if (confirm('Are you sure? This will delete all patterns and responses for this intent.')) {
        await fetch(`${PROXY_URL}/data/intents?id=${id}`, { method: 'DELETE' });
        loadKnowledgeBase();
    }
}

let editingIntentId = null;

async function editIntent(id, tag) {
    editingIntentId = id;
    const pResp = await fetch(`${PROXY_URL}/data/patterns?tag=${tag}`);
    const patterns = await pResp.json();
    const rResp = await fetch(`${PROXY_URL}/data/responses?tag=${tag}`);
    const responses = await rResp.json();

    document.getElementById('modal-tag').value = tag;
    document.getElementById('modal-tag').disabled = true;
    document.getElementById('modal-patterns').value = patterns.documents.map(p => p.text).join('\n');
    document.getElementById('modal-responses').value = responses.documents.map(r => r.text).join('\n');
    
    document.querySelector('#intent-modal h3').textContent = 'Edit Intent';
    modal.style.display = 'flex';
}

function teachBot(query) {
    document.getElementById('intent-form').reset();
    document.getElementById('modal-tag').disabled = false;
    document.getElementById('modal-patterns').value = query;
    document.querySelector('#intent-modal h3').textContent = 'Teach Bot';
    modal.style.display = 'flex';
}

// Modal Logic
const modal = document.getElementById('intent-modal');
const addBtn = document.getElementById('add-intent-btn');
const closeBtn = document.querySelector('.close-modal');

addBtn.onclick = () => {
    editingIntentId = null;
    document.getElementById('intent-form').reset();
    document.getElementById('modal-tag').disabled = false;
    document.querySelector('#intent-modal h3').textContent = 'Add New Intent';
    modal.style.display = 'flex';
};

closeBtn.onclick = () => modal.style.display = 'none';

document.getElementById('intent-form').onsubmit = async (e) => {
    e.preventDefault();
    const tag = document.getElementById('modal-tag').value;
    const patterns = document.getElementById('modal-patterns').value.split('\n').filter(p => p.trim());
    const responses = document.getElementById('modal-responses').value.split('\n').filter(r => r.trim());

    try {
        if (!editingIntentId) {
            // Create New
            await fetch(`${PROXY_URL}/data/intents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag, description: `Queries about ${tag}` })
            });
        } else {
            // Update existing (Clear old patterns/responses first via a custom proxy logic or just overwrite)
            // For prototype simplicity, we delete the intent and recreate it if tag changed, 
            // but here tag is disabled, so we just clean up patterns/responses and recreate them.
            
            // Delete existing patterns
            const pDocs = await (await fetch(`${PROXY_URL}/data/patterns?tag=${tag}`)).json();
            for (let doc of pDocs.documents) await fetch(`${PROXY_URL}/data/patterns?id=${doc.$id}`, { method: 'DELETE' });
            
            // Delete existing responses
            const rDocs = await (await fetch(`${PROXY_URL}/data/responses?tag=${tag}`)).json();
            for (let doc of rDocs.documents) await fetch(`${PROXY_URL}/data/responses?id=${doc.$id}`, { method: 'DELETE' });
        }

        // Add Patterns
        for (let p of patterns) {
            await fetch(`${PROXY_URL}/data/patterns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: p, intent_tag: tag })
            });
        }

        // Add Responses
        for (let r of responses) {
            await fetch(`${PROXY_URL}/data/responses`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: r, intent_tag: tag })
            });
        }

        modal.style.display = 'none';
        loadKnowledgeBase();
        alert('Saved successfully!');
    } catch (err) {
        console.error(err);
        alert('Error saving.');
    }
};

// Search Filter
document.querySelector('.search-box input').oninput = (e) => {
    const val = e.target.value.toLowerCase();
    const filtered = currentIntents.filter(i => i.tag.toLowerCase().includes(val));
    renderIntentsTable(filtered);
};

// Settings Save
document.querySelector('.slider').onchange = async (e) => {
    const val = (e.target.value / 100).toString();
    const settings = await (await fetch(`${PROXY_URL}/data/settings`)).json();
    const thresholdDoc = settings.documents.find(s => s.key === 'threshold');
    
    if (thresholdDoc) {
        await fetch(`${PROXY_URL}/data/settings?id=${thresholdDoc.$id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: val })
        });
    } else {
        await fetch(`${PROXY_URL}/data/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'threshold', value: val })
        });
    }
    alert('Confidence threshold updated to ' + val);
};

function initDashboard() {
    loadOverview();
}

checkAuth();
