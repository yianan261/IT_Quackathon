// 确保ALLOWED_DOMAINS和API_ENDPOINT存在，如果不存在，设置默认值
const { ALLOWED_DOMAINS = ['localhost:8000', 'login.stevens.edu'], API_ENDPOINT = 'http://localhost:8000/api/chat' } = window;

class ChatBot {
  constructor() {
    this.isOpen = false;
    this.isRecording = false;
    this.recognition = null;
    this.speechSynthesis = window.speechSynthesis;
    this.voiceOutputEnabled = false; // Users can toggle this
    this.currentSpeakingMessageId = null; // Track which message is currently being spoken
    this.messageIdCounter = 0; // Counter for unique message IDs
    this.init();
    this.initVoice();
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
          <button class="speaker-btn" title="Toggle voice output">🔇</button>
          <button class="minimize-btn">−</button>
          <button class="close-btn">×</button>
        </div>
      </div>
      <div class="chat-body">
        <div class="chat-messages">
          <div class="message bot" data-message-id="welcome-msg">
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
              <div class="message-controls">
                <button class="control-btn speaker-control" data-message-id="welcome-msg" title="Read aloud">
                  <span class="speaker-icon">🔊</span>
                </button>
                <button class="control-btn copy-control" data-message-id="welcome-msg" title="Copy message">
                  <span class="copy-icon">📋</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <input type="text" placeholder="Ask me a question">
          <button class="voice-btn" title="Voice input">
            <span style="color: #8B0000;">🎤</span>
          </button>
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

    // Speaker toggle button
    const speakerBtn = document.querySelector('.speaker-btn');
    speakerBtn.addEventListener('click', () => this.toggleVoiceOutput());

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
      
      // Handle speaker control buttons
      if (e.target.closest('.speaker-control')) {
        const messageId = e.target.closest('.speaker-control').getAttribute('data-message-id');
        this.toggleMessageSpeech(messageId);
      }
      
      // Handle copy control buttons
      if (e.target.closest('.copy-control')) {
        const messageId = e.target.closest('.copy-control').getAttribute('data-message-id');
        this.copyMessage(messageId);
      }
    });

    // Voice button
    const voiceBtn = document.querySelector('.voice-btn');
    voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());

    // Initialize button states
    this.updateSpeakerButton();
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

  // Toggle voice output
  toggleVoiceOutput() {
    this.voiceOutputEnabled = !this.voiceOutputEnabled;
    this.updateSpeakerButton();
    console.log('🔊 Voice output:', this.voiceOutputEnabled ? 'enabled' : 'disabled');
  }

  // Update speaker button appearance
  updateSpeakerButton() {
    const speakerBtn = document.querySelector('.speaker-btn');
    
    if (this.voiceOutputEnabled) {
      speakerBtn.textContent = '🔊';
      speakerBtn.title = 'Voice output enabled (click to disable)';
      speakerBtn.style.color = '#8B0000';
    } else {
      speakerBtn.textContent = '🔇';
      speakerBtn.title = 'Voice output disabled (click to enable)';
      speakerBtn.style.color = '#6c757d';
    }
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
    
    // Generate unique message ID
    const messageId = `msg-${++this.messageIdCounter}`;
    
    // Return the complete message HTML
    return `
      <div class="message bot" data-message-id="${messageId}">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <div class="assignments-response">
            <p class="response-message">${this.escapeHtml(message)}</p>
            ${summaryHtml}
            ${coursesHtml}
            ${suggestionsHtml}
          </div>
          <div class="message-controls">
            <button class="control-btn speaker-control" data-message-id="${messageId}" title="Read aloud">
              <span class="speaker-icon">🔊</span>
            </button>
            <button class="control-btn copy-control" data-message-id="${messageId}" title="Copy message">
              <span class="copy-icon">📋</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Helper method: Render announcements cards for structured announcement data
  renderAnnouncementsCards(structuredResponse) {
    const { data, message, suggestions } = structuredResponse;
    const { courses, summary } = data;
    
    // Build the summary header
    let summaryHtml = '';
    if (summary && summary.total_announcements > 0) {
      summaryHtml = `
        <div class="announcements-summary">
          <div class="summary-stats">
            <span class="stat-item">📢 Total: ${summary.total_announcements}</span>
            <span class="stat-item recent">🔥 Recent: ${summary.recent_announcements}</span>
            <span class="stat-item courses">📚 Courses: ${summary.courses_with_announcements}/${summary.total_courses}</span>
          </div>
        </div>
      `;
    }
    
    // Build announcement cards for each course
    let coursesHtml = '';
    courses.forEach(course => {
      const announcements = course.announcements || [];
      
      // If course has announcements, show them as cards
      if (announcements.length > 0) {
        let announcementsHtml = '';
        announcements.forEach(announcement => {
          const postedDate = new Date(announcement.posted_datetime);
          const formattedDate = postedDate.toLocaleDateString();
          const formattedTime = postedDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
          const recentClass = announcement.is_recent ? 'recent' : '';
          
          announcementsHtml += `
            <a href="${announcement.url}" target="_blank" class="announcement-card-link">
              <div class="announcement-card ${recentClass}">
                <div class="announcement-header">
                  <h4 class="announcement-title">${this.escapeHtml(announcement.title)}</h4>
                  ${announcement.is_recent ? '<span class="recent-badge">NEW</span>' : ''}
                </div>
                <div class="announcement-meta">
                  <span class="announcement-author">👤 ${this.escapeHtml(announcement.author)}</span>
                  <span class="announcement-date">📅 ${formattedDate} at ${formattedTime}</span>
                </div>
                <div class="announcement-preview">
                  <p>${this.escapeHtml(announcement.message_preview)}</p>
                </div>
              </div>
            </a>
          `;
        });
        
        coursesHtml += `
          <div class="course-section">
            <div class="course-header">
              <h3 class="course-title">${this.escapeHtml(course.course_name)}</h3>
              <span class="announcement-count">${announcements.length} announcement${announcements.length > 1 ? 's' : ''}</span>
            </div>
            <div class="announcements-grid">
              ${announcementsHtml}
            </div>
          </div>
        `;
      } else {
        // Course has no announcements, show link to check directly
        coursesHtml += `
          <div class="course-section no-announcements">
            <div class="course-header">
              <h3 class="course-title">${this.escapeHtml(course.course_name)}</h3>
              <span class="no-announcements-text">No recent announcements</span>
            </div>
            <div class="course-link">
              <a href="${course.announcements_link}" target="_blank" class="btn-primary">
                📢 Check ${course.course_code} Announcements
              </a>
            </div>
          </div>
        `;
      }
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
    
    // Generate unique message ID
    const messageId = `msg-${++this.messageIdCounter}`;
    
    // Return the complete message HTML
    return `
      <div class="message bot" data-message-id="${messageId}">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <div class="announcements-response">
            <p class="response-message">${this.escapeHtml(message)}</p>
            ${summaryHtml}
            ${coursesHtml}
            ${suggestionsHtml}
          </div>
          <div class="message-controls">
            <button class="control-btn speaker-control" data-message-id="${messageId}" title="Read aloud">
              <span class="speaker-icon">🔊</span>
            </button>
            <button class="control-btn copy-control" data-message-id="${messageId}" title="Copy message">
              <span class="copy-icon">📋</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Helper method: Render course comparison for structured course comparison data
  renderCourseComparison(structuredResponse) {
    const { data, message, suggestions } = structuredResponse;
    const { courses, recommendations, comparison_title } = data;
    
    // Build the comparison title
    let titleHtml = '';
    if (comparison_title) {
      titleHtml = `
        <div class="comparison-title">
          <h3>${this.escapeHtml(comparison_title)}</h3>
        </div>
      `;
    }
    
    // Build course comparison sections
    let coursesHtml = '';
    courses.forEach((course, index) => {
      const learningPoints = course.learning_points || [];
      
      let learningPointsHtml = '';
      if (learningPoints.length > 0) {
        learningPointsHtml = learningPoints.map(point => 
          `<li class="learning-point">${this.escapeHtml(point)}</li>`
        ).join('');
      } else {
        learningPointsHtml = '<li class="learning-point no-info">No specific information available</li>';
      }
      
      coursesHtml += `
        <div class="course-comparison-section">
          <div class="course-comparison-header">
            <h4 class="course-comparison-title">
              ${index === 0 ? '📚' : '💻'} ${this.escapeHtml(course.course_name)}
            </h4>
            ${course.info_sources && course.info_sources.length > 0 ? 
              `<span class="sources-count">${course.info_sources.length} source${course.info_sources.length > 1 ? 's' : ''}</span>` : ''
            }
          </div>
          <div class="learning-objectives">
            <p class="section-subtitle">What you'll learn and implement:</p>
            <ul class="learning-points-list">
              ${learningPointsHtml}
            </ul>
          </div>
        </div>
      `;
    });
    
    // Build recommendations section
    let recommendationsHtml = '';
    if (recommendations && recommendations.length > 0) {
      const recommendationCards = recommendations.map(rec => `
        <div class="recommendation-card">
          <div class="recommendation-header">
            <h5 class="recommendation-title">${this.escapeHtml(rec.title)}</h5>
            ${rec.course_preference && rec.course_preference !== 'both' && rec.course_preference !== 'consult_advisor' ? 
              `<span class="course-preference">${this.escapeHtml(rec.course_preference)}</span>` : ''
            }
          </div>
          <p class="recommendation-description">${this.escapeHtml(rec.description)}</p>
        </div>
      `).join('');
      
      recommendationsHtml = `
        <div class="recommendations-section">
          <h4 class="recommendations-title">💡 Course Selection Recommendations:</h4>
          <div class="recommendations-grid">
            ${recommendationCards}
          </div>
        </div>
      `;
    }
    
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
    
    // Generate unique message ID
    const messageId = `msg-${++this.messageIdCounter}`;
    
    // Return the complete message HTML
    return `
      <div class="message bot" data-message-id="${messageId}">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <div class="course-comparison-response">
            <p class="response-message">${this.escapeHtml(message)}</p>
            ${titleHtml}
            <div class="courses-comparison-grid">
              ${coursesHtml}
            </div>
            ${recommendationsHtml}
            ${suggestionsHtml}
          </div>
          <div class="message-controls">
            <button class="control-btn speaker-control" data-message-id="${messageId}" title="Read aloud">
              <span class="speaker-icon">🔊</span>
            </button>
            <button class="control-btn copy-control" data-message-id="${messageId}" title="Copy message">
              <span class="copy-icon">📋</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Helper method: Render default message for non-structured responses
  renderDefaultMessage(responseText) {
    const responseHtml = this.convertUrlsToLinks(responseText || "Received a response but couldn't extract the message content.");
    const messageId = `msg-${++this.messageIdCounter}`;
    
    return `
      <div class="message bot" data-message-id="${messageId}">
        <div class="bot-avatar" style="background-color: #8B0000; color: white; display: flex; justify-content: center; align-items: center;">S</div>
        <div class="message-content">
          <p>${responseHtml}</p>
          <div class="message-controls">
            <button class="control-btn speaker-control" data-message-id="${messageId}" title="Read aloud">
              <span class="speaker-icon">🔊</span>
            </button>
            <button class="control-btn copy-control" data-message-id="${messageId}" title="Copy message">
              <span class="copy-icon">📋</span>
            </button>
          </div>
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

  // Initialize voice recognition
  initVoice() {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('🎤 Speech recognition not supported in this browser');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onstart = () => {
      console.log('🎤 Voice recording started');
      this.isRecording = true;
      this.updateVoiceButton();
    };

    this.recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      const input = document.querySelector('.chat-input input');
      if (input) {
        input.value = finalTranscript + interimTranscript;
      }

      if (finalTranscript) {
        console.log('🎤 Final transcript:', finalTranscript);
        this.sendMessage(finalTranscript);
        input.value = '';
      }
    };

    this.recognition.onend = () => {
      console.log('🎤 Voice recording ended');
      this.isRecording = false;
      this.updateVoiceButton();
    };

    this.recognition.onerror = (event) => {
      console.error('🎤 Voice recognition error:', event.error);
      this.isRecording = false;
      this.updateVoiceButton();
    };
  }

  // Toggle voice recording
  toggleVoiceRecording() {
    if (!this.recognition) {
      alert('Voice recognition not supported in this browser');
      return;
    }

    if (this.isRecording) {
      this.recognition.stop();
    } else {
      this.recognition.start();
    }
  }

  // Update voice button appearance
  updateVoiceButton() {
    const voiceBtn = document.querySelector('.voice-btn');
    const voiceIcon = voiceBtn.querySelector('span');
    
    if (this.isRecording) {
      voiceIcon.textContent = '🔴';
      voiceIcon.style.color = '#dc3545';
      voiceBtn.title = '🎤 Recording... (click to stop)';
      voiceBtn.style.background = '#ffe6e6';
    } else {
      voiceIcon.textContent = '🎤';
      voiceIcon.style.color = '#8B0000';
      voiceBtn.title = 'Voice input';
      voiceBtn.style.background = 'transparent';
    }
  }

  // Speak text using text-to-speech
  speakText(text) {
    if (!this.speechSynthesis) {
      return;
    }

    // Only speak if voice output is enabled
    if (!this.voiceOutputEnabled) {
      return;
    }

    // Cancel any ongoing speech
    this.speechSynthesis.cancel();

    // Clean text for speech (remove HTML tags, extra whitespace)
    const cleanText = text
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .trim();

    if (cleanText.length === 0) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;

    // Try to use a more natural voice
    const voices = this.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes('Google') && voice.lang.includes('en')
    ) || voices.find(voice => voice.lang.includes('en'));
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    // Add event listeners for speech events
    utterance.onstart = () => {
      console.log('🔊 Speech started');
    };
    
    utterance.onend = () => {
      console.log('🔊 Speech ended');
      if (this.currentSpeakingMessageId) {
        this.updateSpeakerIcon(this.currentSpeakingMessageId, false);
        this.currentSpeakingMessageId = null;
      }
    };
    
    utterance.onerror = () => {
      console.log('🔊 Speech error');
      if (this.currentSpeakingMessageId) {
        this.updateSpeakerIcon(this.currentSpeakingMessageId, false);
        this.currentSpeakingMessageId = null;
      }
    };

    this.speechSynthesis.speak(utterance);
    console.log('🔊 Speaking:', cleanText.substring(0, 50) + '...');
  }

  // Toggle speech for a specific message
  toggleMessageSpeech(messageId) {
    if (!this.speechSynthesis) {
      alert('Speech synthesis not supported in this browser');
      return;
    }

    // If this message is currently being spoken, stop it
    if (this.currentSpeakingMessageId === messageId) {
      this.speechSynthesis.cancel();
      this.updateSpeakerIcon(messageId, false);
      this.currentSpeakingMessageId = null;
      console.log('🔊 Stopped speaking message:', messageId);
      return;
    }

    // Stop any currently speaking message
    if (this.currentSpeakingMessageId) {
      this.speechSynthesis.cancel();
      this.updateSpeakerIcon(this.currentSpeakingMessageId, false);
    }

    // Get the message content
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageElement) {
      console.error('Message element not found:', messageId);
      return;
    }

    // Extract text content for speaking
    let textToSpeak = '';
    const messageContent = messageElement.querySelector('.message-content');
    
    // Check if it's a structured response (assignments)
    const assignmentsResponse = messageContent.querySelector('.assignments-response');
    if (assignmentsResponse) {
      // For structured responses, speak the main message
      const responseMessage = assignmentsResponse.querySelector('.response-message');
      textToSpeak = responseMessage ? responseMessage.textContent : 'Here is the information you requested.';
    } else {
      // For regular messages, speak the paragraph content
      const paragraph = messageContent.querySelector('p');
      textToSpeak = paragraph ? paragraph.textContent : messageContent.textContent;
    }

    // Clean and speak the text
    const cleanText = textToSpeak
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .trim();

    if (cleanText.length === 0) {
      console.error('No text to speak for message:', messageId);
      return;
    }

    // Set up speech
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;

    // Try to use a more natural voice
    const voices = this.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes('Google') && voice.lang.includes('en')
    ) || voices.find(voice => voice.lang.includes('en'));
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    // Set up event listeners
    utterance.onstart = () => {
      this.currentSpeakingMessageId = messageId;
      this.updateSpeakerIcon(messageId, true);
      console.log('🔊 Started speaking message:', messageId);
    };
    
    utterance.onend = () => {
      this.updateSpeakerIcon(messageId, false);
      this.currentSpeakingMessageId = null;
      console.log('🔊 Finished speaking message:', messageId);
    };
    
    utterance.onerror = () => {
      this.updateSpeakerIcon(messageId, false);
      this.currentSpeakingMessageId = null;
      console.log('🔊 Error speaking message:', messageId);
    };

    // Start speaking
    this.speechSynthesis.speak(utterance);
  }

  // Update speaker icon based on speaking state
  updateSpeakerIcon(messageId, isSpeaking) {
    const speakerBtn = document.querySelector(`.speaker-control[data-message-id="${messageId}"]`);
    if (!speakerBtn) return;

    const icon = speakerBtn.querySelector('.speaker-icon');
    if (isSpeaking) {
      icon.textContent = '🔇';
      speakerBtn.title = 'Stop reading';
      speakerBtn.style.background = '#ffe6e6';
    } else {
      icon.textContent = '🔊';
      speakerBtn.title = 'Read aloud';
      speakerBtn.style.background = 'transparent';
    }
  }

  // Copy message content to clipboard
  async copyMessage(messageId) {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageElement) {
      console.error('Message element not found:', messageId);
      return;
    }

    const messageContent = messageElement.querySelector('.message-content');
    let textToCopy = '';

    // Check if it's a structured response (assignments)
    const assignmentsResponse = messageContent.querySelector('.assignments-response');
    if (assignmentsResponse) {
      // For structured responses, copy a formatted version
      const responseMessage = assignmentsResponse.querySelector('.response-message');
      textToCopy = responseMessage ? responseMessage.textContent : '';
      
      // Add course information
      const courseSections = assignmentsResponse.querySelectorAll('.course-section');
      courseSections.forEach(section => {
        const courseTitle = section.querySelector('.course-title');
        if (courseTitle) {
          textToCopy += '\n\n' + courseTitle.textContent + ':\n';
          
          const assignments = section.querySelectorAll('.assignment-card');
          assignments.forEach(assignment => {
            const name = assignment.querySelector('.assignment-name');
            const dueDate = assignment.querySelector('.due-date');
            if (name && dueDate) {
              textToCopy += '• ' + name.textContent + ' - ' + dueDate.textContent + '\n';
            }
          });
        }
      });
    } else {
      // For regular messages, copy the paragraph content
      const paragraph = messageContent.querySelector('p');
      textToCopy = paragraph ? paragraph.textContent : messageContent.textContent;
    }

    // Clean up the text
    textToCopy = textToCopy.replace(/\s+/g, ' ').trim();

    try {
      await navigator.clipboard.writeText(textToCopy);
      
      // Show feedback
      const copyBtn = document.querySelector(`.copy-control[data-message-id="${messageId}"]`);
      const originalIcon = copyBtn.querySelector('.copy-icon').textContent;
      const originalTitle = copyBtn.title;
      
      copyBtn.querySelector('.copy-icon').textContent = '✅';
      copyBtn.title = 'Copied!';
      copyBtn.style.background = '#e8f5e9';
      
      // Reset after 2 seconds
      setTimeout(() => {
        copyBtn.querySelector('.copy-icon').textContent = originalIcon;
        copyBtn.title = originalTitle;
        copyBtn.style.background = 'transparent';
      }, 2000);
      
      console.log('📋 Copied message:', messageId);
    } catch (err) {
      console.error('Failed to copy text:', err);
      alert('Failed to copy to clipboard');
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
        } else if (structuredResponse.response_type === 'announcements') {
          // Render announcements cards
          console.log('📢 Rendering announcements cards');
          botMessageHtml = this.renderAnnouncementsCards(structuredResponse);
        } else if (structuredResponse.response_type === 'course_comparison') {
          // Render course comparison
          console.log('🔍 Rendering course comparison');
          botMessageHtml = this.renderCourseComparison(structuredResponse);
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
      
              // Handle automatic voice output (only if global toggle is enabled)
      if (this.voiceOutputEnabled && !this.currentSpeakingMessageId) {
        try {
          const parsedResponse = JSON.parse(data.response);
          if (!parsedResponse.response_type) {
            // Plain text response
            this.speakText(data.response);
            console.log('🔊 Global voice output: speaking full response');
          } else {
            // Structured response (like assignments) - speak summary
            const message = parsedResponse.message || "Here's the information you requested.";
            this.speakText(message);
            console.log('🔊 Global voice output: speaking summary');
          }
        } catch (e) {
          // Not JSON, plain text
          this.speakText(data.response);
          console.log('🔊 Global voice output: speaking text response');
        }
      }
      
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