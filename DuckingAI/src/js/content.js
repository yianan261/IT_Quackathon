// 在文件顶部添加调试辅助函数
function debug(message) {
  console.log(`[DuckingAI Automation] ${message}`);
}

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

// 自动化功能模块 - 优化版
class AutomationManager {
  constructor() {
    debug('AutomationManager initialized');
    this.setupListeners();
  }

  setupListeners() {
    // 监听来自background script的消息
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      debug(`Received message: ${JSON.stringify(message)}`);
      
      if (message.type === 'AUTOMATION_CLICK') {
        // 立即发送响应，表示已收到命令
        sendResponse({ status: 'received' });
        
        // 异步处理点击操作
        this.handleElementsToClick(message.elementsToClick)
          .then(result => {
            chrome.runtime.sendMessage({
              type: 'AUTOMATION_COMPLETED',
              result: result
            });
          })
          .catch(error => {
            chrome.runtime.sendMessage({
              type: 'AUTOMATION_FAILED',
              error: error.message
            });
          });
        
        return true; // 保持消息通道开放
      }
    });
  }

  // 处理点击元素的指令
  async handleElementsToClick(elementsToClick) {
    if (!elementsToClick || !elementsToClick.length) {
      throw new Error('No elements to click specified');
    }

    const results = [];
    
    for (const elementInfo of elementsToClick) {
      try {
        debug(`Attempting to click: ${elementInfo.description}`);
        const result = await this.clickElement(elementInfo);
        results.push(result);
      } catch (error) {
        debug(`Error clicking element ${elementInfo.description}: ${error.message}`);
        
        // 在开发模式下显示错误
        this.showErrorIndicator(error.message);
        
        results.push({
          description: elementInfo.description,
          success: false,
          error: error.message
        });
        
        // 如果是关键元素，则中止后续操作
        if (elementInfo.critical) {
          throw new Error(`Critical element click failed: ${error.message}`);
        }
      }
    }
    
    return results;
  }

  // 简化的错误显示
  showErrorIndicator(message) {
    const errorElement = document.createElement('div');
    Object.assign(errorElement.style, {
      position: 'fixed',
      top: '10px',
      right: '10px',
      backgroundColor: 'rgba(255, 0, 0, 0.8)',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      zIndex: '9999',
      maxWidth: '300px'
    });
    errorElement.textContent = `Automation Error: ${message}`;
    
    document.body.appendChild(errorElement);
    setTimeout(() => errorElement.remove(), 5000);
  }

  // 优化的元素点击功能
  async clickElement(elementInfo) {
    const { description, selector, fallback_selectors = [], timeout = 5000, wait_before_click = 0 } = elementInfo;
    
    // 1. 尝试所有选择器
    let element = null;
    let allSelectors = [];
    
    // 处理可能包含逗号的选择器（CSS组合选择器）
    if (selector.includes(',')) {
      // 分割组合选择器并添加到选择器列表
      allSelectors = [...selector.split(',').map(s => s.trim())];
      debug(`Detected compound selector, split into ${allSelectors.length} individual selectors`);
    } else {
      allSelectors = [selector];
    }
    
    // 添加所有备用选择器
    allSelectors = [...allSelectors, ...(fallback_selectors || [])];
    
    // 记录所有将要尝试的选择器
    debug(`Will try ${allSelectors.length} selectors to find "${description}"`);
    
    for (const sel of allSelectors) {
      try {
        debug(`Trying selector: ${sel}`);
        // 使用querySelectorAll来获取匹配数量
        const matches = document.querySelectorAll(sel);
        if (matches && matches.length > 0) {
          element = matches[0]; // 使用第一个匹配
          debug(`Found ${matches.length} elements with selector: ${sel}, using first match`);
          
          // 如果找到了多个元素，记录一些附加信息以便诊断
          if (matches.length > 1) {
            debug(`Multiple matches found! Text of first element: "${element.textContent?.trim() || 'no text'}"`);
          }
          break;
        } else {
          debug(`No matches for selector: ${sel}`);
        }
      } catch (error) {
        debug(`Selector error: ${sel} - ${error.message}`);
      }
    }
    
    // 2. 如果没找到，等待元素出现
    if (!element) {
      debug(`Element "${description}" not found immediately, waiting up to ${timeout}ms for it to appear`);
      element = await this.waitForElement(allSelectors, timeout);
    }
    
    // 3. 如果还没找到，尝试一些更宽松的查找
    if (!element) {
      debug('Trying looser text-based search as last resort');
      
      // 尝试基于内容的查找，不区分大小写
      if (description) {
        const textToFind = description.replace(/button in.+$/i, '').trim();
        debug(`Looking for elements containing text: "${textToFind}"`);
        
        // 查找包含描述文本的所有元素
        const allElements = Array.from(document.querySelectorAll('button, a, div[role="button"], [role="menuitem"], .gwt-Label, [data-automation-id]'));
        const matchingElements = allElements.filter(el => {
          const text = el.textContent || el.innerText || el.getAttribute('aria-label') || '';
          return text.toLowerCase().includes(textToFind.toLowerCase());
        });
        
        if (matchingElements.length > 0) {
          element = matchingElements[0];
          debug(`Found ${matchingElements.length} elements by text content, using first match: ${element.tagName}`);
        } else {
          debug('No elements found by text content');
        }
      }
    }
    
    // 4. 如果还没找到，抛出错误
    if (!element) {
      // 记录页面内容，帮助诊断
      debug('Failed to find element, dumping page information:');
      debug(`Page title: ${document.title}`);
      debug(`Current URL: ${window.location.href}`);
      debug(`Body classes: ${document.body.className}`);
      debug(`Body ID: ${document.body.id}`);
      
      throw new Error(`Element "${description}" not found after ${timeout}ms`);
    }
    
    // 5. 滚动到元素位置并点击
    debug(`Found element for "${description}". Tag: ${element.tagName}, Text: "${element.textContent?.trim() || 'no text'}"`);
    debug('Scrolling to element');
    element.scrollIntoView({ behavior: 'auto', block: 'center' });
    
    // 等待一小段时间，确保元素可交互
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 如果需要额外等待，则执行等待
    if (wait_before_click > 0) {
      debug(`Waiting ${wait_before_click}ms before clicking as requested`);
      await new Promise(resolve => setTimeout(resolve, wait_before_click));
    }
    
    // 6. 执行点击
    debug(`Clicking element: ${description}`);
    
    try {
      // 尝试使用原生click方法
      element.click();
    } catch (clickError) {
      debug(`Native click failed: ${clickError.message}, trying alternative methods`);
      
      // 尝试使用更高级的点击方法模拟点击
      try {
        // 创建和分发点击事件
        const clickEvent = new MouseEvent('click', {
          view: window,
          bubbles: true,
          cancelable: true
        });
        element.dispatchEvent(clickEvent);
        debug('Used MouseEvent click simulation');
      } catch (eventError) {
        // 如果所有尝试都失败，抛出原始错误
        throw clickError;
      }
    }
    
    return {
      description,
      success: true,
      timestamp: new Date().toISOString(),
      elementInfo: {
        tagName: element.tagName,
        id: element.id,
        className: element.className,
        textContent: element.textContent?.substring(0, 50) || 'no text'
      }
    };
  }

  // 优化的元素等待功能
  waitForElement(selectors, timeout = 5000) {
    return new Promise(resolve => {
      // 记录开始时间
      const startTime = Date.now();
      debug(`Starting to wait for element with ${selectors.length} selectors, timeout: ${timeout}ms`);
      
      // 定义检查元素的函数
      const checkForElement = () => {
        for (const selector of selectors) {
          try {
            const elements = document.querySelectorAll(selector);
            if (elements && elements.length > 0) {
              const element = elements[0];
              debug(`waitForElement: found element with selector: ${selector}`);
              return element;
            }
          } catch (error) {
            debug(`waitForElement: selector error: ${selector} - ${error.message}`);
          }
        }
        
        // 尝试更宽松的文本查找（只用描述中的关键词）
        const keywordMatch = selectors.join(' ').match(/academics|workday|button/i);
        if (keywordMatch) {
          const keyword = keywordMatch[0].toLowerCase();
          debug(`waitForElement: trying text-based search for keyword: ${keyword}`);
          
          const allElements = Array.from(document.querySelectorAll('button, a, div[role="button"], [role="menuitem"], .gwt-Label, [data-automation-id]'));
          const matchingElements = allElements.filter(el => {
            const text = el.textContent || el.innerText || el.getAttribute('aria-label') || '';
            return text.toLowerCase().includes(keyword);
          });
          
          if (matchingElements.length > 0) {
            return matchingElements[0];
          }
        }
        
        return null;
      };
      
      // 立即先检查一次
      let element = checkForElement();
      if (element) {
        debug('waitForElement: element found immediately');
        resolve(element);
        return;
      }
      
      // 设置MutationObserver监听DOM变化
      const observer = new MutationObserver(() => {
        // 检查是否已经超时
        if (Date.now() - startTime > timeout) {
          debug(`waitForElement: timeout after ${timeout}ms`);
          observer.disconnect();
          resolve(null);
          return;
        }
        
        // 重新检查元素
        element = checkForElement();
        if (element) {
          debug(`waitForElement: element found after ${Date.now() - startTime}ms`);
          observer.disconnect();
          resolve(element);
        }
      });
      
      // 开始观察
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        characterData: false
      });
      
      // 设置周期性检查
      const interval = setInterval(() => {
        // 检查是否已经超时
        if (Date.now() - startTime > timeout) {
          debug(`waitForElement: timeout after ${timeout}ms (from interval)`);
          clearInterval(interval);
          observer.disconnect();
          resolve(null);
          return;
        }
        
        // 重新检查元素
        element = checkForElement();
        if (element) {
          debug(`waitForElement: element found after ${Date.now() - startTime}ms (from interval)`);
          clearInterval(interval);
          observer.disconnect();
          resolve(element);
        }
      }, 500); // 每500毫秒检查一次
      
      // 确保超时后清理资源
      setTimeout(() => {
        observer.disconnect();
        clearInterval(interval);
        if (!element) {
          debug(`waitForElement: final timeout after ${timeout}ms`);
          resolve(null);
        }
      }, timeout);
    });
  }
}

// 初始化自动化管理器
debug('Initializing AutomationManager');
const automationManager = new AutomationManager();

// 向background脚本发送内容脚本已加载的消息
try {
  chrome.runtime.sendMessage({
    type: 'CONTENT_SCRIPT_LOADED',
    url: window.location.href,
    readyForAutomation: true  // 表明此内容脚本已准备好接收自动化指令
  });
  debug('Sent content script loaded message');
} catch (error) {
  debug(`Failed to send content script loaded message: ${error.message}`);
} 