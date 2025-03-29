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
      
      if (message.type === 'VERIFY_DIALOG') {
        // 立即发送响应，表示已收到命令
        sendResponse({ status: 'received' });
        
        // 异步处理对话框验证
        this.verifyDialogForm(message.dialogInfo)
          .then(result => {
            chrome.runtime.sendMessage({
              type: 'DIALOG_VERIFIED',
              result: result
            });
          })
          .catch(error => {
            chrome.runtime.sendMessage({
              type: 'DIALOG_VERIFICATION_FAILED',
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
    
    // 增加特殊日志，跟踪当前正在尝试点击的元素
    debug(`==========================================`);
    debug(`Starting click process for: "${description}"`);
    debug(`Current URL: ${window.location.href}`);
    debug(`Current page title: ${document.title}`);
    debug(`==========================================`);
    
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
    
    // 对Academics按钮做特殊处理
    if (description.includes('Academics')) {
      debug('Special handling for Academics button');
      
      // 查找任何包含Academics文字的可交互元素
      const academicsElements = Array.from(document.querySelectorAll('*')).filter(el => {
        const text = (el.textContent || '').trim();
        const isVisible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
        const isInteractive = el.tagName === 'BUTTON' || 
                             el.tagName === 'A' || 
                             el.hasAttribute('role') || 
                             el.hasAttribute('tabindex') ||
                             el.hasAttribute('data-automation-id');
        return text.includes('Academic') && isVisible && isInteractive;
      });
      
      if (academicsElements.length > 0) {
        debug(`Found ${academicsElements.length} potential Academics elements by text content`);
        
        // 查找最可能是按钮的元素
        const bestMatch = academicsElements.find(el => 
          el.tagName === 'BUTTON' || 
          el.getAttribute('role') === 'button' ||
          el.getAttribute('tabindex') === '0'
        ) || academicsElements[0];
        
        debug(`Selected best Academics element: ${bestMatch.tagName}, text: "${bestMatch.textContent.trim()}"`);
        element = bestMatch;
      }
    }
    
    // 如果特殊处理没找到元素，继续常规查找
    if (!element) {
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
      
      // 特殊情况：对于Academics按钮，如果找不到，尝试遍历和记录所有可点击元素
      if (description.includes('Academics')) {
        debug('Dumping all clickable elements on page:');
        const clickableElements = Array.from(document.querySelectorAll('button, a, [role="button"], [tabindex="0"]'));
        debug(`Found ${clickableElements.length} clickable elements`);
        clickableElements.slice(0, 10).forEach((el, i) => {
          debug(`Clickable #${i}: ${el.tagName}, text: "${el.textContent?.trim() || 'no text'}", class: ${el.className}`);
        });
      }
      
      throw new Error(`Element "${description}" not found after ${timeout}ms`);
    }
    
    // 5. 滚动到元素位置并点击
    debug(`Found element for "${description}". Tag: ${element.tagName}, Text: "${element.textContent?.trim() || 'no text'}"`);
    debug('Scrolling to element');
    element.scrollIntoView({ behavior: 'auto', block: 'center' });
    
    // 只有在明确要求等待时才执行等待
    // 否则立即点击元素，不进行默认等待
    if (wait_before_click > 0) {
      debug(`Waiting ${wait_before_click}ms before clicking as requested`);
      await new Promise(resolve => setTimeout(resolve, wait_before_click));
    } else {
      debug('Clicking element immediately without waiting');
    }
    
    // 6. 执行点击
    debug(`Clicking element: ${description}`);
    
    // 对于Academics按钮的特殊处理
    if (description.includes('Academics')) {
      debug('Using enhanced click method for Academics button');
      try {
        // 首先尝试直接点击
        element.click();
        debug('Direct click on Academics button successful');
        
        // 添加一个额外的检查，在点击后等待URL变化
        const startUrl = window.location.href;
        debug(`Current URL before Academics click: ${startUrl}`);
        
        // 等待并检查URL是否变化
        await new Promise(resolve => {
          const checkInterval = setInterval(() => {
            if (window.location.href !== startUrl) {
              debug(`URL changed to: ${window.location.href}`);
              clearInterval(checkInterval);
              resolve();
            }
          }, 100);
          
          // 设置超时
          setTimeout(() => {
            clearInterval(checkInterval);
            debug('No URL change detected, continuing anyway');
            resolve();
          }, 5000);
        });
        
        // 返回成功结果
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
      } catch (error) {
        debug(`Error during Academics click: ${error.message}`);
        // 尝试备用点击方法
      }
    }
    
    try {
      // 对于链接元素，阻止默认行为
      if (element.tagName.toLowerCase() === 'a' || element.closest('a')) {
        debug('Element is or is inside a link, preventing default behavior');
        // 创建并分发自定义的鼠标点击事件，并阻止默认行为
        const clickEvent = new MouseEvent('click', {
          view: window,
          bubbles: true,
          cancelable: true
        });
        
        // 检查是否是Workday卡片
        if (description.toLowerCase().includes('workday')) {
          debug('This is a Workday card, using custom click handling');
          
          // 保存链接目标，以便后续手动导航
          const href = element.href || element.closest('a')?.href;
          
          // 阻止事件传播和默认行为
          element.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            debug('Prevented default link behavior for Workday card');
          }, { once: true, capture: true });
          
          // 触发点击
          element.click();
          
          // 向background脚本发送消息，通知已点击Workday卡片
          chrome.runtime.sendMessage({
            type: 'WORKDAY_CARD_CLICKED',
            href: href
          });
          
          // 返回成功结果（对于非Workday元素）
          return {
            description,
            success: true,
            timestamp: new Date().toISOString(),
            elementInfo: {
              tagName: element.tagName,
              id: element.id,
              className: element.className,
              textContent: element.textContent?.substring(0, 50) || 'no text',
              href: href
            }
          };
        }
        
        // 对于其他链接，使用正常点击
        const prevented = !element.dispatchEvent(clickEvent);
        if (prevented) {
          debug('Click default prevented via dispatchEvent');
        } else {
          // 如果事件未被阻止，手动点击
          element.click();
        }
      } else {
        // 尝试使用原生click方法
        element.click();
      }
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
    
    // 返回成功结果（对于非Workday元素）
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

  // 验证对话框是否显示
  async verifyDialogForm(dialogInfo) {
    const { description, selector, fallback_selectors = [], timeout = 5000 } = dialogInfo;
    
    debug(`Attempting to verify dialog: ${description}`);
    
    // 组合所有选择器
    const allSelectors = [selector, ...(fallback_selectors || [])];
    
    try {
      // 特殊处理：首先尝试使用更通用的对话框检测
      const genericDialogSelectors = [
        '[role="dialog"]', 
        '[aria-modal="true"]', 
        '.wd-popup', 
        '[data-automation-id="editPopup"]',
        '.WKQS.WHEH', // Workday特定对话框类
        'div.WCU[data-popup-version]'
      ];
      
      // 首先尝试通用选择器快速查找
      let dialog = null;
      for (const genericSelector of genericDialogSelectors) {
        try {
          const elements = document.querySelectorAll(genericSelector);
          if (elements && elements.length > 0) {
            dialog = elements[0];
            debug(`Found dialog with generic selector: ${genericSelector}`);
            break;
          }
        } catch (error) {
          debug(`Generic selector error: ${genericSelector} - ${error.message}`);
        }
      }
      
      // 如果通用选择器没找到，再等待特定选择器
      if (!dialog) {
        debug('No dialog found with generic selectors, waiting for specific selectors...');
        dialog = await this.waitForElement(allSelectors, timeout);
      }
      
      // 最后一次尝试：查找任何包含"Find Course Sections"文本的大型容器
      if (!dialog) {
        debug('Trying to find dialog by content...');
        const potentialDialogs = Array.from(document.querySelectorAll('div')).filter(div => {
          return div.offsetWidth > 300 && div.offsetHeight > 300 && 
                 (div.textContent || '').includes('Find Course Sections') &&
                 (div.className || '').length > 0;
        });
        
        if (potentialDialogs.length > 0) {
          dialog = potentialDialogs[0];
          debug(`Found potential dialog by content: ${dialog.className}`);
        }
      }
      
      if (!dialog) {
        throw new Error(`Dialog "${description}" did not appear after ${timeout}ms`);
      }
      
      debug(`Successfully verified dialog: ${description}`);
      debug(`Dialog details: Tag=${dialog.tagName}, Class=${dialog.className}`);
      
      // 可以添加截图功能帮助调试
      this.showSuccessIndicator(`Dialog "${description}" verified`);
      
      return {
        description,
        success: true,
        timestamp: new Date().toISOString(),
        elementInfo: {
          tagName: dialog.tagName,
          id: dialog.id || 'no-id',
          className: dialog.className,
          textContent: dialog.textContent?.substring(0, 50) || 'no text',
          attributes: {
            role: dialog.getAttribute('role') || 'none',
            ariaModal: dialog.getAttribute('aria-modal') || 'none',
            dataAutomationId: dialog.getAttribute('data-automation-id') || 'none'
          }
        }
      };
    } catch (error) {
      debug(`Error verifying dialog: ${error.message}`);
      this.showErrorIndicator(error.message);
      throw error;
    }
  }
  
  // 显示成功提示
  showSuccessIndicator(message) {
    const successElement = document.createElement('div');
    Object.assign(successElement.style, {
      position: 'fixed',
      top: '10px',
      right: '10px',
      backgroundColor: 'rgba(0, 128, 0, 0.8)',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      zIndex: '9999',
      maxWidth: '300px'
    });
    successElement.textContent = `Automation Success: ${message}`;
    
    document.body.appendChild(successElement);
    setTimeout(() => successElement.remove(), 3000);
  }

  // 优化的元素等待功能
  waitForElement(selectors, timeout = 5000) {
    return new Promise(resolve => {
      // 记录开始时间
      const startTime = Date.now();
      debug(`Starting to wait for element with ${selectors.length} selectors, timeout: ${timeout}ms`);
      
      // 检查是否正在寻找Academics按钮
      const isAcademicsSearch = selectors.some(s => s.toLowerCase().includes('academic'));
      if (isAcademicsSearch) {
        debug('Special handling activated for Academics element search');
      }
      
      // 定义检查元素的函数
      const checkForElement = () => {
        // 首先尝试所有指定的选择器
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
        
        // 尝试基于文本内容查找（专门针对Workday UI）
        // 提取选择器中的关键词
        const selectorString = selectors.join(' ');
        let targetTexts = [];
        
        if (selectorString.includes('Find Course Sections')) {
          targetTexts.push('Find Course Sections');
        } else if (selectorString.includes('Academic')) {
          targetTexts.push('Academic', 'Academics');
          // 对于Academics按钮，增加更多变体
          debug('Searching for Academic/Academics text in any element');
        } else if (selectorString.includes('dialog') || selectorString.includes('editPopup')) {
          // 查找对话框
          const dialogs = document.querySelectorAll('[role="dialog"], [aria-modal="true"], .wd-popup');
          if (dialogs && dialogs.length > 0) {
            debug(`waitForElement: found dialog using role/modal attribute`);
            return dialogs[0];
          }
        }
        
        if (targetTexts.length > 0) {
          debug(`waitForElement: trying text-based search for: ${targetTexts.join(', ')}`);
          
          // 查找匹配文本内容的任何元素
          // 这种方法更有可能找到Workday的元素，即使它们没有明确的标题或ID
          const allElementsWithText = Array.from(document.querySelectorAll('*')).filter(el => {
            // 仅考虑可见元素
            if (el.offsetWidth === 0 && el.offsetHeight === 0) return false;
            
            // 检查元素的文本内容
            const text = el.textContent || el.innerText || '';
            return targetTexts.some(target => text.includes(target) && text.length < target.length * 5);
          });
          
          if (allElementsWithText.length > 0) {
            debug(`waitForElement: found ${allElementsWithText.length} elements by text content`);
            
            // 对于Academics特殊处理 - 优先选择按钮或可点击元素
            if (isAcademicsSearch) {
              const clickableAcademics = allElementsWithText.filter(el => 
                el.tagName === 'BUTTON' || 
                el.getAttribute('role') === 'button' ||
                el.getAttribute('tabindex') === '0' ||
                el.tagName === 'A'
              );
              
              if (clickableAcademics.length > 0) {
                debug(`waitForElement: found ${clickableAcademics.length} clickable Academic elements`);
                return clickableAcademics[0];
              }
            }
            
            // 尝试找到最小的包含元素 - 通常是实际的可点击元素
            const smallestTextElement = allElementsWithText.reduce((smallest, current) => {
              // 优先考虑按钮和可点击元素
              if (current.tagName === 'BUTTON' || current.getAttribute('role') === 'button') {
                return current;
              }
              
              const currentSize = current.textContent.length;
              const smallestSize = smallest ? smallest.textContent.length : Infinity;
              return currentSize < smallestSize ? current : smallest;
            }, null);
            
            if (smallestTextElement) {
              debug(`waitForElement: using smallest text element: ${smallestTextElement.tagName}, text length: ${smallestTextElement.textContent.length}`);
              return smallestTextElement;
            }
            
            // 回退到第一个找到的元素
            return allElementsWithText[0];
          }
        }
        
        // 针对Academics按钮的最后尝试 - 查找顶级导航链接或按钮
        if (isAcademicsSearch) {
          const navElements = document.querySelectorAll('nav a, [role="navigation"] [role="menuitem"], .navigation button');
          
          for (const el of navElements) {
            const text = el.textContent || '';
            if (text.includes('Acad')) {
              debug(`waitForElement: found Academic in navigation: ${el.tagName}`);
              return el;
            }
          }
          
          // 记录页面上的所有按钮，以帮助诊断
          if (Date.now() - startTime > timeout / 2) { // 只在等待超过一半时间时执行此昂贵操作
            debug('waitForElement: Academic search timeout approaching, dumping all buttons:');
            const allButtons = document.querySelectorAll('button, [role="button"]');
            debug(`Found ${allButtons.length} buttons on page`);
            for (let i = 0; i < Math.min(allButtons.length, 5); i++) {
              const btn = allButtons[i];
              debug(`Button ${i}: ${btn.tagName}, text: "${btn.textContent?.trim() || 'no text'}"`);
            }
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
      
      // 设置最小检查间隔，避免过于频繁的DOM检查
      const CHECK_INTERVAL = 50; // 50毫秒的检查间隔
      let lastCheckTime = Date.now();
      
      // 设置MutationObserver监听DOM变化
      const observer = new MutationObserver(() => {
        // 限制检查频率
        const now = Date.now();
        if (now - lastCheckTime < CHECK_INTERVAL) {
          return;
        }
        lastCheckTime = now;
        
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
          debug(`waitForElement: element found after ${Date.now() - startTime}ms due to DOM change`);
          observer.disconnect();
          if (interval) clearInterval(interval);
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
      
      // 设置周期性检查，但使用更短的间隔
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
      }, 100); // 每100毫秒检查一次，比原来的500毫秒更频繁
      
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