// ---------- CHATBOT LOGIC ----------
(function() {
    const KNOWLEDGE = {
        "agent_config": {
            "name": "Abdex Industries Assistant",
            "greeting": "Welcome to Abdex Industries. I'm your fluid transfer specialist. I can help you find the right hose, fitting, coupling, or service for your application. How can I help you today?",
            "fallback": "I don't have specific details on that product right now. Please contact our team at sales@abdex.com.au or call +61 (0) 39796 3044 for expert assistance."
        },
        "company": {
            "name": "Abdex Industries",
            "pressure_range": "Up to 60,000 psi (4,135 bar)"
        }
    };

    // --- ELEMENTS ---
    const chatToggle = document.getElementById('chatToggle');
    const chatPanel = document.getElementById('chatPanel');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('chatbotUserInput');
    const sendBtn = document.getElementById('chatbotSendBtn');
    
    const boardMessages = document.getElementById('boardMessages');
    const boardInput = document.getElementById('boardUserInput');

    let isOpen = false;

    // --- WIDGET FUNCTIONS ---
    window.toggleChatWidget = function() {
        if (!chatPanel) return;
        isOpen = !isOpen;
        if (isOpen) {
            chatPanel.classList.remove('hidden');
            if (chatMessages && chatMessages.children.length === 0) {
                addMessage(KNOWLEDGE.agent_config.greeting, 'bot');
            }
            if (userInput) userInput.focus();
        } else {
            chatPanel.classList.add('hidden');
        }
    };

    function addMessage(text, sender = 'bot') {
        if (!chatMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTyping() {
        if (!chatMessages) return;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-indicator-container';
        typingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        typingDiv.id = 'typingIndicator';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) typing.remove();
    }

    window.handleChatbotSend = async function() {
        if (!userInput) return;
        const text = userInput.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        userInput.value = '';
        showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text, chat_history: [] })
            });

            removeTyping();
            if (response.ok) {
                const reader = response.body.getReader();
                let fullText = '';
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message bot';
                chatMessages.appendChild(messageDiv);

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = new TextDecoder().decode(value);
                    fullText += chunk;
                    messageDiv.textContent = fullText;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            } else {
                addMessage(`Error: Backend returned ${response.status}. Please check if the server is running.`, 'bot');
            }
        } catch (e) {
            removeTyping();
            addMessage("Connection error. Please check your network.", 'bot');
        }
    };

    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleChatbotSend();
        });
    }

    // --- BOARD FUNCTIONS ---
    window.handleBoardSend = async function() {
        if (!boardInput) return;
        const text = boardInput.value.trim();
        if (!text) return;

        addBoardMessage(text, 'user');
        boardInput.value = '';
        showBoardTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text, chat_history: [] })
            });

            removeBoardTyping();
            if (response.ok) {
                const reader = response.body.getReader();
                let fullText = '';
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message bot board-message';
                messageDiv.style.cssText = "background: #ecf3fc; align-self: flex-start; padding: 1.2rem; border-radius: 18px; max-width: 80%; line-height: 1.6;";
                boardMessages.appendChild(messageDiv);

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = new TextDecoder().decode(value);
                    fullText += chunk;
                    messageDiv.textContent = fullText;
                    boardMessages.scrollTop = boardMessages.scrollHeight;
                }
            }
        } catch (e) {
            removeBoardTyping();
            addBoardMessage("Error connecting to server.", 'bot');
        }
    };

    function addBoardMessage(text, sender = 'bot') {
        if (!boardMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} board-message`;
        messageDiv.textContent = text;
        
        if (sender === 'user') {
            messageDiv.style.cssText = "background: #d2e6ff; align-self: flex-end; padding: 1.2rem; border-radius: 18px; max-width: 80%; line-height: 1.6; border: 1px solid #b8d9ff;";
        } else {
            messageDiv.style.cssText = "background: #ecf3fc; align-self: flex-start; padding: 1.2rem; border-radius: 18px; max-width: 80%; line-height: 1.6;";
        }
        
        boardMessages.appendChild(messageDiv);
        boardMessages.scrollTop = boardMessages.scrollHeight;
    }

    function showBoardTyping() {
        if (!boardMessages) return;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot board-message';
        typingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        typingDiv.id = 'boardTypingIndicator';
        boardMessages.appendChild(typingDiv);
        boardMessages.scrollTop = boardMessages.scrollHeight;
    }

    function removeBoardTyping() {
        const typing = document.getElementById('boardTypingIndicator');
        if (typing) typing.remove();
    }

    // Initial greeting for board
    if (boardMessages) {
        setTimeout(() => {
            if (boardMessages.children.length === 0) {
                addBoardMessage("Welcome to your dedicated Procurement Board. How can I assist you with your projects today?", 'bot');
            }
        }, 500);
    }
})();
