// 确保ALLOWED_DOMAINS和API_ENDPOINT存在，如果不存在，设置默认值
const { ALLOWED_DOMAINS = ['localhost:8000', 'login.stevens.edu'], API_ENDPOINT = 'http://localhost:8000/api/chat' } = window;

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
      <div style="width: 100%; height: 100%; background-color: #8B0000; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: white; font-weight: bold;">S</div>
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
        <h2>Stevens AI Assistant</h2>
        <div class="header-controls">
          <button class="minimize-btn">−</button>
          <button class="close-btn">×</button>
        </div>
      </div>
      <div class="chat-body">
        <div class="chat-messages">
          <div class="message bot">
            <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
            <div class="message-content">
              <p>Hi, I'm your Stevens AI Assistant! I'm here to help answer your questions about Stevens Institute of Technology.</p>
              <div class="suggestions-section">
                <p class="suggestions-title">💡 Try asking:</p>
                <div class="suggestions-grid">
                  <button class="suggestion-btn" data-suggestion="Give me upcoming assignments">📝 Give me upcoming assignments</button>
                  <button class="suggestion-btn" data-suggestion="Show me my current courses">📚 Show me my current courses</button>
                  <button class="suggestion-btn" data-suggestion="Help me register for courses">🎓 Help me register for courses</button>
                </div>
              </div>
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

    // Event delegation for suggestion buttons (they're added dynamically)
    const messagesContainer = document.querySelector('.chat-messages');
    messagesContainer.addEventListener('click', (e) => {
      if (e.target.classList.contains('suggestion-btn')) {
        const suggestion = e.target.getAttribute('data-suggestion');
        this.handleSuggestionClick(suggestion);
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

  // Helper method: Render assignment cards for structured assignment data
  renderAssignmentCards(structuredResponse) {
    const { data, message, suggestions } = structuredResponse;
    const { courses, summary } = data;
    
    // Build the summary header
    let summaryHtml = '';
    if (summary) {
      summaryHtml = `
        <div class="assignment-summary">
          <div class="summary-stats">
            <span class="stat-item">📝 Total: ${summary.total_assignments}</span>
            <span class="stat-item high-priority">🔥 High: ${summary.high_priority}</span>
            <span class="stat-item medium-priority">⚡ Medium: ${summary.medium_priority}</span>
          </div>
        </div>
      `;
    }
    
    // Build assignment cards for each course
    let coursesHtml = '';
    courses.forEach(course => {
      const assignments = course.assignments || [];
      
      let assignmentsHtml = '';
      assignments.forEach(assignment => {
        const priorityClass = `priority-${assignment.priority}`;
        const dueDate = new Date(assignment.due_datetime);
        const formattedDate = dueDate.toLocaleDateString();
        const formattedTime = dueDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        assignmentsHtml += `
          <div class="assignment-card ${priorityClass}">
            <div class="assignment-header">
              <h4 class="assignment-name">${this.escapeHtml(assignment.name)}</h4>
              <span class="priority-badge ${priorityClass}">${assignment.priority.toUpperCase()}</span>
            </div>
            <div class="assignment-details">
              <div class="due-date">
                📅 Due: ${formattedDate} at ${formattedTime}
              </div>
              ${assignment.points_possible ? `<div class="points">💯 Points: ${assignment.points_possible}</div>` : ''}
              <div class="assignment-actions">
                <a href="${assignment.details_url}" target="_blank" class="btn-primary">View Details</a>
              </div>
            </div>
          </div>
        `;
      });
      
      coursesHtml += `
        <div class="course-section">
          <h3 class="course-title">${this.escapeHtml(course.course_name)}</h3>
          <div class="assignments-grid">
            ${assignmentsHtml}
          </div>
        </div>
      `;
    });
    
    // Build suggestions buttons if available
    let suggestionsHtml = '';
    if (suggestions && suggestions.length > 0) {
      const suggestionButtons = suggestions.map((suggestion, index) => 
        `<button class="suggestion-btn" data-suggestion="${this.escapeHtml(suggestion)}" data-index="${index}">${this.escapeHtml(suggestion)}</button>`
      ).join('');
      
      suggestionsHtml = `
        <div class="suggestions-section">
          <p class="suggestions-title">💡 Try asking:</p>
          <div class="suggestions-grid">
            ${suggestionButtons}
          </div>
        </div>
      `;
    }
    
    // Return the complete message HTML
    return `
      <div class="message bot">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <div class="assignments-response">
            <p class="response-message">${this.escapeHtml(message)}</p>
            ${summaryHtml}
            ${coursesHtml}
            ${suggestionsHtml}
          </div>
        </div>
      </div>
    `;
  }

  // Helper method: Render default message for non-structured responses
  renderDefaultMessage(responseText) {
    const responseHtml = this.convertUrlsToLinks(responseText || "Received a response but couldn't extract the message content.");
    
    return `
      <div class="message bot">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <p>${responseHtml}</p>
        </div>
      </div>
    `;
  }

  // Handle suggestion button clicks
  handleSuggestionClick(suggestion) {
    console.log('🔧 Suggestion clicked:', suggestion);
    const input = document.querySelector('.chat-input input');
    
    if (input) {
      // First, show the suggestion in the input field
      input.value = suggestion;
      console.log('✅ Input value set:', input.value);
      
      // Give a small delay to show the text, then send
      setTimeout(() => {
        this.sendMessage(suggestion);
        input.value = ''; // Clear input after sending
      }, 100);
    } else {
      console.error('❌ Input field not found!');
    }
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
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <p>Thinking...</p>
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
      
      // Check if response is structured JSON
      let botMessageHtml;
      try {
        const structuredResponse = JSON.parse(data.response);
        
        if (structuredResponse.response_type === 'assignments') {
          // Render assignment cards
          console.log('🎯 Rendering assignment cards');
          botMessageHtml = this.renderAssignmentCards(structuredResponse);
        } else {
          // Handle other structured response types in the future
          botMessageHtml = this.renderDefaultMessage(data.response);
        }
      } catch (e) {
        // Not structured JSON, render as normal text
        console.log('📝 Rendering as plain text');
        botMessageHtml = this.renderDefaultMessage(data.response);
      }
      
      // Add bot reply
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
          <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
          <div class="message-content">
            <p>Sorry, I encountered an error: ${this.escapeHtml(errorMessage)}</p>
          </div>
        </div>
      `;
      messagesContainer.insertAdjacentHTML('beforeend', errorMessageHtml);
    }
  }
}

// 初始化聊天机器人，在所有页面上显示
window.chatBot = new ChatBot(); 