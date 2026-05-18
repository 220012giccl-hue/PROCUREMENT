/**
 * Assistant Core Logic
 * Handles chat, conversations, and UI state
 */

const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const fileInput = document.getElementById('fileInput');
const uploadPreview = document.getElementById('uploadPreview');
const fileNameSpan = document.getElementById('fileName');
const voiceBtn = document.getElementById('voiceBtn');
const convList = document.getElementById('convList');

let currentContext = null;
let currentConversationId = null;
let currentMode = 'procurement'; // Default to Procurement Assistant

function setMode(mode) {
    currentMode = mode;

    // Update UI
    const btnRFI = document.getElementById('btnRFIMode');
    const btnProc = document.getElementById('btnProcurementMode');
    const btnGen = document.getElementById('btnGeneralMode');
    const btnMarket = document.getElementById('btnMarketMode');

    if (btnProc) btnProc.classList.toggle('active', mode === 'procurement');
    if (btnGen) btnGen.classList.toggle('active', mode === 'general');
    if (btnMarket) btnMarket.classList.toggle('active', mode === 'market');

    // Visual cues
    const sendBtn = document.getElementById('sendBtn');
    if (mode === 'general') {
        if (sendBtn) sendBtn.style.background = '#6366f1';
        const wrapper = document.querySelector('.input-wrapper');
        if (wrapper) wrapper.style.focusWithinBorderColor = '#6366f1';
    } else if (mode === 'market') {
        if (sendBtn) sendBtn.style.background = 'var(--primary-orange)';
    } else {
        if (sendBtn) sendBtn.style.background = 'var(--primary-orange)';
    }

    // Update empty state if visible
    const emptyState = document.querySelector('.empty-state');
    if (emptyState) {
        if (mode === 'general') {
            emptyState.querySelector('h2').textContent = "General AI Assistant";
            emptyState.querySelector('p').textContent = "Ask me anything - I work like ChatGPT, Gemini, or Claude.";
        } else if (mode === 'market') {
            emptyState.querySelector('h2').textContent = "Market Intelligence Assistant";
            emptyState.querySelector('p').textContent = "Search supplier catalogues, compare products, and generate RFQs instantly.";
        } else {
            emptyState.querySelector('h2').textContent = "Procurement Executive Assistant";
            emptyState.querySelector('p').textContent = "I have full knowledge of your emails, documents, and database to answer structured procurement queries.";
        }
    }

    renderPromptChips(mode);

    console.log(`[Assistant] Mode switched to: ${mode}`);

    // Reload conversations for this mode
    currentConversationId = null;
    loadConversations(mode);
    startNewChat();
}

const PROMPT_CHIPS = {
    market: [
        "Compare cordless hammer drills from Bunnings and Sydney Tools",
        "Find safety boots for construction workers from Blackwoods",
        "Find wheelbarrows at Bunnings — 80L+ capacity",
        "Compare PPE starter kits for 20 workers",
        "Find fall protection equipment for roof work",
        "Compare concrete tools for slab preparation",
        "Find timber screws and structural fixings"
    ],
    procurement: [
        "Show me all open RFQs from my database",
        "What suppliers do we have on file?",
        "Summarise my recent procurement emails",
        "Which projects have pending quotes?",
        "Find previous orders for safety equipment",
        "Compare quotes received in the last month"
    ],
    general: [
        "What is a Bill of Quantities (BOQ)?",
        "Explain the RFQ vs RFI process",
        "What should I check before approving a supplier quote?",
        "What does lead time mean in procurement?",
        "Explain trade account pricing vs retail pricing"
    ]
};

function renderPromptChips(mode) {
    const container = document.getElementById('promptChips');
    if (!container) return;
    const chips = PROMPT_CHIPS[mode] || [];
    container.innerHTML = chips.map(chip => `
        <button onclick="usePromptChip(this.textContent)" style="
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 7px 14px;
            font-size: 0.78rem;
            color: #475569;
            cursor: pointer;
            transition: all 0.15s;
            font-family: inherit;
        " onmouseover="this.style.borderColor='var(--primary-orange)';this.style.color='var(--primary-orange)';"
           onmouseout="this.style.borderColor='#e2e8f0';this.style.color='#475569';">
            ${chip}
        </button>`).join('');
}

function usePromptChip(text) {
    const input = document.getElementById('chatInput');
    if (input) {
        input.value = text;
        input.focus();
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    }
}


document.addEventListener('DOMContentLoaded', async () => {
    console.log('RFI page loaded...');

    // Auto-resize textarea
    if (chatInput) {
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = chatInput.scrollHeight + 'px';
        });

        // Handle Enter key
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    // Init Assistant
    await initAssistant();
});

async function initAssistant() {
    renderPromptChips(currentMode);
    await loadConversations();
    // Load latest conversation by default if none selected
    if (convList && convList.querySelector('.conv-item')) {
        const latest = convList.querySelector('.conv-item');
        selectConversation(latest.dataset.id);
    }
}


async function loadConversations(mode = currentMode) {
    if (!convList) return;
    try {
        const response = await window.RFQAgentAPI.getConversations(mode);
        if (response.success) {
            convList.innerHTML = '';
            if (response.data.length === 0) {
                convList.innerHTML = '<div class="p-4 text-center text-muted">No history yet</div>';
                return;
            }
            response.data.forEach(conv => {
                const div = document.createElement('div');
                div.className = `conv-item ${currentConversationId == conv.id ? 'active' : ''}`;
                div.dataset.id = conv.id;
                div.onclick = () => selectConversation(conv.id);
                div.innerHTML = `
                    <span class="conv-title" title="${conv.title}">${conv.title}</span>
                    <button class="btn-del-conv" onclick="event.stopPropagation(); deleteConversation(${conv.id})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                `;
                convList.appendChild(div);
            });
        } else {
            convList.innerHTML = '<div class="p-4 text-center text-muted">Error loading history</div>';
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        convList.innerHTML = '<div class="p-4 text-center text-muted">Connection error</div>';
    }
}

async function selectConversation(id) {
    currentConversationId = id;
    // Update UI
    document.querySelectorAll('.conv-item').forEach(el => {
        el.classList.toggle('active', el.dataset.id == id);
    });
    await loadHistory(id);
}

async function startNewChat() {
    currentConversationId = null;
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon"><svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></div>
                <h2>New Conversation</h2>
                <p>Start typing to begin a new chat thread.</p>
            </div>
        `;
    }
    document.querySelectorAll('.conv-item').forEach(el => el.classList.remove('active'));
    if (chatInput) chatInput.focus();
}

async function deleteConversation(id) {
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    try {
        const response = await window.RFQAgentAPI.deleteConversation(id);
        if (response.success) {
            if (currentConversationId == id) {
                startNewChat();
            }
            await loadConversations();
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
    }
}

async function loadHistory(id = null) {
    try {
        const response = await window.RFQAgentAPI.getChatHistory(id);
        if (response.success) {
            if (chatMessages) {
                chatMessages.innerHTML = '';
                if (response.data.length === 0) {
                    chatMessages.innerHTML = '<div class="empty-state"><h2>Empty chat</h2></div>';
                    return;
                }
                response.data.forEach(msg => {
                    appendMessage(msg.role, msg.content, false);
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

async function sendMessage() {
    if (!chatInput) return;
    const text = chatInput.value.trim();
    if (!text && !currentContext) return;

    // Clear empty state
    if (chatMessages && chatMessages.querySelector('.empty-state')) {
        chatMessages.innerHTML = '';
    }

    // Append user message immediately
    appendMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Show typing indicator
    const indicatorId = showTypingStatus();

    try {
        const response = await window.RFQAgentAPI.askAssistant(text, currentContext, currentConversationId, currentMode);

        // Remove indicator using ID
        removeTypingStatus(indicatorId);

        if (response.success) {
            appendMessage('assistant', response.response);
            // Update current thread if it's new
            if (!currentConversationId) {
                currentConversationId = response.conversation_id;
                await loadConversations();
            }
        } else {
            let errorMsg = response.error || "Could not connect to AI.";
            if (errorMsg.includes("Read timed out")) {
                errorMsg = "The request timed out. This often happens with large documents. Please try a simpler question or a smaller document.";
            }
            appendMessage('assistant', "Error: " + errorMsg);
        }
    } catch (error) {
        removeTypingStatus(indicatorId);
        let msg = "Connection error. Please ensure the backend is running.";
        if (error.message && error.message.includes("timeout")) {
            msg = "The request timed out while processing your document. I've increased the processing limit, but please try again.";
        }
        appendMessage('assistant', msg);
    }
}

function appendMessage(role, text, shouldScroll = true) {
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = `message ${role}`;

    if (role === 'assistant' && currentMode === 'market') {
        div.className += ' procurement';
        if (typeof renderProcurementCard === 'function') {
            renderProcurementCard(div, text);
        } else {
            div.innerText = text;
        }
    } else {
        // Simple text or structured text for Procurement/General
        div.innerText = text;
    }

    chatMessages.appendChild(div);
    if (shouldScroll) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function showTypingStatus() {
    if (!chatMessages) return null;
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message assistant typing-indicator';
    div.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeTypingStatus(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
}

// --- UI UTILITIES ---
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '';
    if (type === 'success') icon = '<svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    else if (type === 'error') icon = '<svg viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
    else icon = '<svg viewBox="0 0 24 24" fill="none" stroke="var(--primary-orange)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';

    toast.innerHTML = `
        ${icon}
        <div class="toast-message">${message}</div>
        <div class="toast-close" onclick="this.parentElement.remove()">×</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'fadeOut 0.4s ease-in forwards';
            setTimeout(() => toast.remove(), 400);
        }
    }, 4000);
}

function showLoading(message = 'Loading...') {
    const loader = `
        <div id="loading-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 9999;">
            <div style="background: white; padding: 2rem 3rem; border-radius: 12px; text-align: center; box-shadow: var(--shadow-xl);">
                <div class="spinner-small" style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid var(--primary-orange); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                <div style="font-weight: 600; color: var(--text-primary);">${message}</div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loader);
}

function hideLoading() {
    const loader = document.getElementById('loading-overlay');
    if (loader) loader.remove();
}

async function handleFile(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        if (fileNameSpan) fileNameSpan.innerText = "Extracting text: " + file.name + "...";
        if (uploadPreview) {
            uploadPreview.style.display = 'flex';
            uploadPreview.classList.add('loading');
        }

        try {
            const result = await window.RFQAgentAPI.extractTextAssistant(file);
            if (result && result.success) {
                currentContext = result.text;
                if (fileNameSpan) fileNameSpan.innerText = "Context attached: " + file.name;
                if (uploadPreview) uploadPreview.classList.remove('loading');
            } else {
                if (fileNameSpan) fileNameSpan.innerText = "Error: " + (result ? result.error : "Unknown error");
                if (uploadPreview) uploadPreview.style.borderColor = 'var(--accent-red)';
            }
        } catch (error) {
            console.error('File extraction error:', error);
            if (fileNameSpan) fileNameSpan.innerText = "Error: Could not read file.";
        }
    }
}

function clearUpload() {
    if (fileInput) fileInput.value = '';
    if (uploadPreview) uploadPreview.style.display = 'none';
    currentContext = null;
}

function exportChat() {
    if (!chatMessages) return;
    const content = Array.from(chatMessages.querySelectorAll('.message'))
        .map(m => `${m.classList.contains('user') ? 'User' : 'Assistant'}: ${m.innerText}`)
        .join('\n\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-history-${currentConversationId || 'new'}.txt`;
    a.click();
}

// Voice Input Logic
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        if (voiceBtn) voiceBtn.classList.add('active');
        if (chatInput) chatInput.placeholder = "Listening...";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (chatInput) {
            chatInput.value = transcript;
            chatInput.style.height = 'auto';
            chatInput.style.height = (chatInput.scrollHeight) + 'px';
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (voiceBtn) voiceBtn.classList.remove('active');
        if (chatInput) chatInput.placeholder = "Error: " + event.error;
    };

    recognition.onend = () => {
        if (voiceBtn) voiceBtn.classList.remove('active');
        if (chatInput) chatInput.placeholder = "Write your message here...";
    };
} else {
    if (voiceBtn) voiceBtn.style.display = 'none';
}

voiceBtn?.addEventListener('click', () => {
    if (recognition) {
        if (voiceBtn.classList.contains('active')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    }
});

// --- RESPONSIVE UI HANDLERS ---
function toggleSidebar() {
    const sidebar = document.getElementById('mainSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar) sidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
}

function toggleConvSidebar() {
    const convSidebar = document.getElementById('convSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (convSidebar) convSidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
}

// Close everything on overlay click
document.getElementById('sidebarOverlay')?.addEventListener('click', () => {
    document.getElementById('mainSidebar')?.classList.remove('active');
    document.getElementById('convSidebar')?.classList.remove('active');
    document.getElementById('sidebarOverlay')?.classList.remove('active');
});

// Handle Mobile Menu Toggle
document.getElementById('mobileMenuToggle')?.addEventListener('click', toggleSidebar);
