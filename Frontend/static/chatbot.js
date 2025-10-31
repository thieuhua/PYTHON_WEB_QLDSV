// Chatbot AI for Student Advisory
class ChatbotUI {
    constructor() {
        this.conversationHistory = [];
        this.isOpen = false;
        this.isTyping = false;
        this.init();
    }

    init() {
        this.createChatbotUI();
        this.attachEventListeners();
        this.loadSuggestions();
    }

    createChatbotUI() {
        const chatbotHTML = `
            <!-- Chatbot Toggle Button -->
            <button id="chatbot-toggle" class="chatbot-toggle" aria-label="Mở chatbot">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </button>

            <!-- Chatbot Window -->
            <div id="chatbot-window" class="chatbot-window hidden">
                <!-- Header -->
                <div class="chatbot-header">
                    <div class="chatbot-header-info">
                        <div class="chatbot-avatar">🤖</div>
                        <div>
                            <h3>Trợ lý AI</h3>
                            <span class="chatbot-status">Sẵn sàng hỗ trợ</span>
                        </div>
                    </div>
                    <button id="chatbot-close" class="chatbot-close" aria-label="Đóng chatbot">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <!-- Messages Container -->
                <div id="chatbot-messages" class="chatbot-messages">
                    <div class="chatbot-message assistant">
                        <div class="message-content">
                            👋 Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn với:
                            <ul>
                                <li>📊 Xem điểm và phân tích kết quả học tập</li>
                                <li>📚 Tư vấn về lịch học và môn học</li>
                                <li>💡 Gợi ý cách học hiệu quả hơn</li>
                                <li>❓ Giải đáp thắc mắc về quy định trường</li>
                            </ul>
                            Bạn muốn hỏi gì?
                        </div>
                    </div>
                </div>

                <!-- Suggestions -->
                <div id="chatbot-suggestions" class="chatbot-suggestions">
                    <!-- Suggestions will be loaded here -->
                </div>

                <!-- Input Area -->
                <div class="chatbot-input-area">
                    <input 
                        type="text" 
                        id="chatbot-input" 
                        placeholder="Nhập câu hỏi của bạn..."
                        autocomplete="off"
                    />
                    <button id="chatbot-send" class="chatbot-send-btn" aria-label="Gửi tin nhắn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    attachEventListeners() {
        const toggle = document.getElementById('chatbot-toggle');
        const close = document.getElementById('chatbot-close');
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggle.addEventListener('click', () => this.toggleChatbot());
        close.addEventListener('click', () => this.toggleChatbot());
        send.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    toggleChatbot() {
        this.isOpen = !this.isOpen;
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');

        if (this.isOpen) {
            window.classList.remove('hidden');
            toggle.classList.add('hidden');
            document.getElementById('chatbot-input').focus();
        } else {
            window.classList.add('hidden');
            toggle.classList.remove('hidden');
        }
    }

    async loadSuggestions() {
        try {
            const response = await fetch('/api/chatbot/suggestions', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) throw new Error('Failed to load suggestions');

            const data = await response.json();
            this.displaySuggestions(data.suggestions);
        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    }

    displaySuggestions(suggestions) {
        const container = document.getElementById('chatbot-suggestions');
        container.innerHTML = suggestions.slice(0, 3).map(suggestion => `
            <button class="suggestion-chip" data-suggestion="${suggestion}">
                ${suggestion}
            </button>
        `).join('');

        // Attach click handlers
        container.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const suggestion = e.target.dataset.suggestion;
                document.getElementById('chatbot-input').value = suggestion;
                this.sendMessage();
            });
        });
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();

        if (!message || this.isTyping) return;

        // Add user message to UI
        this.addMessage('user', message);
        input.value = '';

        // Hide suggestions
        document.getElementById('chatbot-suggestions').style.display = 'none';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chatbot/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: this.conversationHistory
                })
            });

            if (!response.ok) throw new Error('Failed to get response');

            const data = await response.json();
            
            // Remove typing indicator
            this.hideTypingIndicator();

            // Add assistant response
            this.addMessage('assistant', data.response);

            // Update conversation history
            this.conversationHistory.push(
                { role: 'user', content: message },
                { role: 'assistant', content: data.response }
            );

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', '😔 Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.');
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.formatMessage(content);
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // Convert markdown-style formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        this.isTyping = true;
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message assistant typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }
}

// Initialize chatbot when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ChatbotUI();
    });
} else {
    new ChatbotUI();
}