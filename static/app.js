document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const memoryCounter = document.getElementById('memory-counter');
    const errorBanner = document.getElementById('error-banner');
    const errorMessage = document.getElementById('error-message');
    const closeErrorBtn = document.getElementById('close-error-btn');
    const resetBtn = document.getElementById('reset-btn');

    // Focus input on load
    userInput.focus();

    // Event Listeners
    chatForm.addEventListener('submit', handleFormSubmit);
    resetBtn.addEventListener('click', resetChat);
    closeErrorBtn.addEventListener('click', hideError);

    /**
     * Show floating error banner with custom message
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorBanner.classList.remove('hidden');
        
        // Auto hide after 6 seconds
        setTimeout(hideError, 6000);
    }

    /**
     * Hide error banner
     */
    function hideError() {
        errorBanner.classList.add('hidden');
    }

    /**
     * Add a message bubble to the chat log
     */
    function addMessageBubble(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        // Simple HTML sanitization and formatting linebreaks
        const escapedContent = content
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/\n/g, "<br>");
            
        messageDiv.innerHTML = escapedContent;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    /**
     * Scroll messages container to the bottom
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Handle Form Submission
     */
    async function handleFormSubmit(e) {
        e.preventDefault();
        
        const messageText = userInput.value;
        
        // 4. Structural validation gate: reject empty or whitespace-only input
        if (!messageText || !messageText.trim()) {
            showError("Input cannot be empty. Please type a message.");
            return;
        }

        // Clear input
        userInput.value = '';
        hideError();

        const trimmedText = messageText.trim();

        // Handle client-side command shortcuts
        const lowerText = trimmedText.toLowerCase();
        if (lowerText === '/exit' || lowerText === '/quit') {
            addMessageBubble(trimmedText, 'user');
            addMessageBubble("To close the chatbot, shutdown the backend server in your terminal or close this browser window.", 'assistant');
            return;
        }

        if (trimmedText === '/reset') {
            await resetChat();
            return;
        }

        // 3. Append user input to UI
        addMessageBubble(trimmedText, 'user');

        // Show typing indicator
        typingIndicator.classList.remove('hidden');
        scrollToBottom();

        try {
            // Post message to backend api
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: trimmedText })
            });

            const data = await response.json();
            
            // Hide typing indicator
            typingIndicator.classList.add('hidden');

            if (response.ok) {
                // Append model's response to UI
                addMessageBubble(data.reply, 'assistant');
                
                // Update memory counter badge
                updateMemoryCounter(data.history_count);
            } else {
                // API Error
                showError(data.error || "An error occurred with the AI request.");
                
                // Optional: remove user's message from the UI since it failed, or show it failed
                const lastMsg = chatMessages.lastElementChild;
                if (lastMsg && lastMsg.classList.contains('user')) {
                    lastMsg.style.opacity = '0.5';
                    lastMsg.innerHTML += ' <span style="font-size:0.8rem; color:#ef4444;">(Failed)</span>';
                }
            }
        } catch (error) {
            typingIndicator.classList.add('hidden');
            showError("Cannot connect to server. Ensure backend is running.");
            
            const lastMsg = chatMessages.lastElementChild;
            if (lastMsg && lastMsg.classList.contains('user')) {
                lastMsg.style.opacity = '0.5';
                lastMsg.innerHTML += ' <span style="font-size:0.8rem; color:#ef4444;">(Failed)</span>';
            }
        }
    }

    /**
     * Update Sliding Window Memory Badge
     */
    function updateMemoryCounter(count) {
        memoryCounter.textContent = `${count} / 20 messages`;
        if (count >= 18) {
            memoryCounter.className = 'info-value highlight warning';
            memoryCounter.style.color = '#ef4444';
        } else if (count >= 14) {
            memoryCounter.className = 'info-value highlight alert';
            memoryCounter.style.color = '#f59e0b';
        } else {
            memoryCounter.className = 'info-value highlight';
            memoryCounter.style.color = '#a5b4fc';
        }
    }

    /**
     * Clear memory history on server and UI
     */
    async function resetChat() {
        try {
            const response = await fetch('/api/reset', {
                method: 'POST'
            });

            if (response.ok) {
                // Clear UI
                chatMessages.innerHTML = '';
                addMessageBubble("Chat history has been reset. Memory is cleared.", 'system-message');
                updateMemoryCounter(0);
                hideError();
                userInput.value = '';
                userInput.focus();
            } else {
                showError("Failed to reset memory.");
            }
        } catch (error) {
            showError("Cannot connect to server to reset chat memory.");
        }
    }
});
