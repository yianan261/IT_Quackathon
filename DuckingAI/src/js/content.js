const { ALLOWED_DOMAINS, API_ENDPOINT } = window;

class ChatBot {
  constructor() {
    this.isOpen = false;
    this.init();
  }

  init() {
    // Create chat icon
    this.createChatIcon();
    // Create chat interface
    this.createChatInterface();
    // Bind events
    this.bindEvents();
  }

  createChatIcon() {
    const icon = document.createElement('div');
    icon.id = 'ducking-ai-icon';
    icon.innerHTML = `
      <div style="width: 100%; height: 100%; background-color: #8B0000; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: white; font-weight: bold;">AI</div>
    `;
    document.body.appendChild(icon);
  }

  createChatInterface() {
    const chatContainer = document.createElement('div');
    chatContainer.id = 'ducking-ai-container';
    chatContainer.classList.add('chat-closed');
    
    chatContainer.innerHTML = `
      <div class="chat-header">
        <div class="header-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <h2>Attila IT Virtual Assistant</h2>
        <div class="header-controls">
          <button class="minimize-btn">−</button>
          <button class="close-btn">×</button>
        </div>
      </div>
      <div class="chat-body">
        <div class="chat-messages">
          <div class="message bot">
            <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">AI</div>
            <div class="message-content">
              <p>Hi, I'm Attila! I am a virtual assistant here to answer any questions you may have about The Division of Information Technology.</p>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <input type="text" placeholder="Ask me a question">
          <button class="send-btn">
            <span style="color: white;">↑</span>
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(chatContainer);
  }

  bindEvents() {
    // Icon click event
    const icon = document.getElementById('ducking-ai-icon');
    icon.addEventListener('click', () => this.toggleChat());

    // Minimize button
    const minimizeBtn = document.querySelector('.minimize-btn');
    minimizeBtn.addEventListener('click', () => this.toggleChat());

    // Close button
    const closeBtn = document.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => this.closeChat());

    // Send message
    const input = document.querySelector('.chat-input input');
    const sendBtn = document.querySelector('.send-btn');
    
    const sendMessage = () => {
      const message = input.value.trim();
      if (message) {
        this.sendMessage(message);
        input.value = '';
      }
    };

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }

  toggleChat() {
    const container = document.getElementById('ducking-ai-container');
    this.isOpen = !this.isOpen;
    container.classList.toggle('chat-closed');
  }

  closeChat() {
    const container = document.getElementById('ducking-ai-container');
    this.isOpen = false;
    container.classList.add('chat-closed');
  }

  // Helper method: Escape HTML special characters
  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  
  // Helper method: Convert URLs to clickable links
  convertUrlsToLinks(text) {
    if (!text) return '';
    
    // First escape HTML
    let safeText = this.escapeHtml(text);
    
    // Regex to match URLs
    const urlRegex = /(https?:\/\/[^\s\)]+)/g;
    
    // Replace URLs with anchor tags
    return safeText.replace(urlRegex, url => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });
  }
  
  async sendMessage(message) {
    const messagesContainer = document.querySelector('.chat-messages');
    
    // Add user message
    const userMessageHtml = `
      <div class="message user">
        <div class="message-content">
          <p>${this.escapeHtml(message)}</p>
        </div>
      </div>
    `;
    messagesContainer.insertAdjacentHTML('beforeend', userMessageHtml);
    
    // Show typing indicator
    const loadingMessageHtml = `
      <div class="message bot loading">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">AI</div>
        <div class="message-content">
          <p>Typing...</p>
        </div>
      </div>
    `;
    messagesContainer.insertAdjacentHTML('beforeend', loadingMessageHtml);
    const loadingMessage = messagesContainer.querySelector('.message.bot.loading');

    try {
      console.log('Sending message to API:', message);
      console.log('API endpoint:', API_ENDPOINT);
      
      // Prepare request body
      const requestBody = {
        messages: [{
          role: "user",
          content: message
        }]
      };
      
      console.log('Request body:', JSON.stringify(requestBody));
      
      // Use API
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      console.log('API response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Parse response
      const data = await response.json();
      console.log('Parsed response data:', data);
      
      // Remove typing indicator
      if (loadingMessage) {
        loadingMessage.remove();
      }
      
      // Process response text to convert URLs to links
      const responseHtml = this.convertUrlsToLinks(data.response || "Received a response but couldn't extract the message content.");
      
      // Add bot reply
      const botMessageHtml = `
        <div class="message bot">
          <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">AI</div>
          <div class="message-content">
            <p>${responseHtml}</p>
          </div>
        </div>
      `;
      messagesContainer.insertAdjacentHTML('beforeend', botMessageHtml);
      
      // Scroll to bottom
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Remove typing indicator
      if (loadingMessage) {
        loadingMessage.remove();
      }
      
      // Build detailed error message
      let errorMessage = error.message || 'Unknown error';
      if (errorMessage === 'Failed to fetch') {
        errorMessage = 'Failed to connect to the server. Please check that your backend is running at ' + API_ENDPOINT + ' and CORS is properly configured.';
      }
      
      // Show error message
      const errorMessageHtml = `
        <div class="message bot error">
          <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">AI</div>
          <div class="message-content">
            <p>Sorry, I encountered an error: ${this.escapeHtml(errorMessage)}</p>
          </div>
        </div>
      `;
      messagesContainer.insertAdjacentHTML('beforeend', errorMessageHtml);
    }
  }
}

// Check if current domain is in allowed list
const currentDomain = window.location.hostname;
if (ALLOWED_DOMAINS.some(domain => currentDomain.includes(domain))) {
  // Initialize chatbot
  new ChatBot();
} 