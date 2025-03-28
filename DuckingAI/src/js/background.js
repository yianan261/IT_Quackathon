// 统一的API配置
const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  AUTOMATION_ENDPOINT: '/test/automation'
};

// 简化的状态管理
const automationState = {
  isRunning: false,
  completedSessionIds: new Set(),
  lastRunTime: 0,
  polling: true, // 默认开启轮询
  navigationInProgress: false, // 添加导航状态跟踪
  lastNavigationUrl: null, // 上次导航的URL
  processingLock: false // 防止并发处理
};

// 限制集合大小的辅助函数
function limitSetSize(set, maxSize = 20) {
  if (set.size > maxSize) {
    const iterator = set.values();
    set.delete(iterator.next().value);
  }
}

// 统一的初始化函数
function initialize() {
  console.log('DuckingAI Extension initialized');
  
  // 注册右键菜单
  chrome.contextMenus.create({
    id: 'trigger-automation',
    title: 'Trigger Automation',
    contexts: ['all']
  });
  
  // 设置消息和命令监听器
  setupListeners();
  
  // 立即执行一次自动化，然后开始轮询
  setTimeout(() => {
    triggerAutomation();
    startPolling();
  }, 2000);
}

// 启动轮询
function startPolling() {
  console.log('Starting automation polling');
  // 将轮询间隔从5秒增加到10秒，减少重复触发的可能性
  setInterval(() => {
    if (automationState.polling) {
      pollForAutomation();
    }
  }, 10000); // 从5秒增加到10秒
}

// 轮询检查自动化指令
async function pollForAutomation() {
  // 如果已经在运行，则跳过
  if (automationState.isRunning || automationState.processingLock) {
    console.log('Automation already running or processing lock active, skipping poll');
    return;
  }
  
  // 设置处理锁，防止并发处理
  automationState.processingLock = true;
  
  try {
    // 添加额外检查：查看是否有活动的导航进行中
    if (automationState.navigationInProgress) {
      console.log('Navigation in progress, skipping poll');
      return;
    }
    
    // 检查是否有待处理的自动化，如果有则不触发新的自动化
    const pendingData = await chrome.storage.local.get('pendingAutomation');
    if (pendingData.pendingAutomation) {
      console.log('Found pending automation, skipping polling');
      return;
    }
    
    // 获取当前标签信息，确认是否已经在目标URL上
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentUrl = tabs[0]?.url || '';
    
    // 如果当前已经在目标URL上，避免重复导航
    if (currentUrl.includes('login.stevens.edu/app/UserHome') || 
        currentUrl.includes('workday') ||
        currentUrl === automationState.lastNavigationUrl) {
      console.log('Already on target URL or related page, skipping poll');
      return;
    }
    
    // 如果最近30秒内执行过，则跳过
    const now = Date.now();
    if (now - automationState.lastRunTime < 30000) {
      console.log(`Last automation was ${(now - automationState.lastRunTime)/1000}s ago, skipping poll`);
      return;
    }
    
    console.log('Polling for automation instructions...');
    await triggerAutomation();
  } finally {
    // 释放处理锁
    automationState.processingLock = false;
  }
}

// 设置各种事件监听器
function setupListeners() {
  // 监听右键菜单点击
  chrome.contextMenus.onClicked.addListener((info) => {
    if (info.menuItemId === 'trigger-automation') {
      triggerAutomation();
    }
  });
  
  // 监听键盘快捷键
  chrome.commands.onCommand.addListener((command) => {
    if (command === 'trigger-automation') {
      triggerAutomation();
    }
  });
  
  // 监听来自popup或content script的消息
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
      case 'TRIGGER_AUTOMATION':
        triggerAutomation();
        sendResponse({ status: 'triggered' });
        break;
      case 'AUTOMATION_COMPLETED':
        handleAutomationCompleted(message.result);
        sendResponse({ status: 'acknowledged' });
        break;
      case 'AUTOMATION_FAILED':
        handleAutomationFailed(message.error);
        sendResponse({ status: 'acknowledged' });
        break;
      case 'TOGGLE_POLLING':
        automationState.polling = message.enabled;
        sendResponse({ status: 'polling_' + (message.enabled ? 'started' : 'stopped') });
        break;
      case 'CONTENT_SCRIPT_LOADED':
        console.log('Content script loaded in tab:', sender.tab.id, 'URL:', message.url);
        // 如果内容脚本表示准备好接收自动化指令，检查是否有待处理的操作
        if (message.readyForAutomation && sender.tab) {
          chrome.storage.local.get('pendingAutomation', (data) => {
            if (data.pendingAutomation) {
              console.log('Found pending automation, resuming...');
              // 给页面一些额外的加载时间
              setTimeout(() => {
                handleCurrentStep(sender.tab.id, data.pendingAutomation.instruction)
                  .catch(error => console.error('Error resuming automation after content script load:', error));
              }, 2000);
            }
          });
        }
        sendResponse({ status: 'acknowledged' });
        break;
    }
    return true; // 保持消息通道开放
  });
}

// 处理自动化完成的回调
function handleAutomationCompleted(result) {
  console.log('Automation completed successfully:', result);
  automationState.isRunning = false;
}

// 处理自动化失败的回调
function handleAutomationFailed(error) {
  console.error('Automation failed:', error);
  automationState.isRunning = false;
}

// 触发自动化的主函数
async function triggerAutomation() {
  // 如果已经在运行，则跳过
  if (automationState.isRunning) {
    console.log('Automation already running, skipping');
    return;
  }
  
  // 检查是否有待处理的自动化任务
  const pendingData = await chrome.storage.local.get('pendingAutomation');
  if (pendingData.pendingAutomation) {
    console.log('There is a pending automation task, resuming instead of starting new');
    automationState.isRunning = true;
    
    // 获取当前活动标签页
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs.length > 0) {
      // 尝试在当前标签页恢复自动化
      await handleCurrentStep(tabs[0].id, pendingData.pendingAutomation.instruction)
        .catch(error => console.error('Error resuming pending automation:', error));
    }
    
    automationState.isRunning = false;
    return;
  }
  
  // 限制频率 - 防止短时间内多次触发
  const now = Date.now();
  if (now - automationState.lastRunTime < 5000) {
    console.log('Triggered too frequently, please wait');
    return;
  }
  
  try {
    automationState.isRunning = true;
    automationState.lastRunTime = now;
    
    // 获取自动化指令
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.AUTOMATION_ENDPOINT}`);
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    
    const data = await response.json();
    if (!data.instruction) throw new Error('No valid instruction received');
    
    // 检查会话ID，避免重复执行
    const sessionId = data.instruction.session_id;
    if (sessionId && automationState.completedSessionIds.has(sessionId)) {
      console.log(`Session ${sessionId} already executed, skipping`);
      automationState.isRunning = false;
      return;
    }
    
    // 执行自动化指令
    await executeAutomation(data.instruction);
    
    // 记录完成的会话ID
    if (sessionId) {
      automationState.completedSessionIds.add(sessionId);
      limitSetSize(automationState.completedSessionIds);
    }
  } catch (error) {
    console.error('Error during automation:', error);
    automationState.isRunning = false;
  }
}

// 执行自动化指令的函数
async function executeAutomation(instruction) {
  // 支持多种自动化动作类型
  if (instruction.action !== 'navigate_and_click' && instruction.action !== 'multi_step_navigation') {
    throw new Error(`Unsupported action: ${instruction.action}`);
  }
  
  try {
    // 获取活动标签页或创建新标签页
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tabs || tabs.length === 0) {
      await chrome.tabs.create({ url: instruction.target_url });
      return; // 让新标签页加载完成，等待下一次触发
    }
    
    const tab = tabs[0];
    
    // 检查当前URL以避免重复导航
    if (tab.url === instruction.target_url || 
        (automationState.lastNavigationUrl === instruction.target_url && 
         Date.now() - automationState.lastRunTime < 10000)) {
      console.log('Already at target URL or recently navigated there, skipping navigation');
      
      // 如果当前在目标URL上，直接执行点击操作
      return handleCurrentStep(tab.id, instruction);
    }
    
    // 设置导航状态
    automationState.navigationInProgress = true;
    automationState.lastNavigationUrl = instruction.target_url;
    
    // 保存多步操作状态到 storage
    if (instruction.action === 'multi_step_navigation') {
      console.log('Saving multi-step navigation state');
      await chrome.storage.local.set({ 
        'pendingAutomation': {
          instruction,
          currentStepIndex: 0,
          lastUpdated: Date.now()
        }
      });
    }
    
    // 导航到目标URL
    console.log(`Navigating to: ${instruction.target_url}`);
    await chrome.tabs.update(tab.id, { url: instruction.target_url });
    
    // 等待页面加载完成
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        chrome.tabs.onUpdated.removeListener(listener);
        automationState.navigationInProgress = false; // 导航超时，重置状态
        reject(new Error('Page load timeout'));
      }, 30000); // 30秒超时
      
      function listener(tabId, changeInfo, updatedTab) {
        if (tabId === tab.id && changeInfo.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          clearTimeout(timeout);
          
          // 重置导航状态
          automationState.navigationInProgress = false;
          
          // 发送点击指令给content script
          setTimeout(() => {
            // 获取当前步骤
            handleCurrentStep(tab.id, instruction).then(resolve).catch(error => {
              automationState.navigationInProgress = false; // 确保在出错时重置
              reject(error);
            });
          }, 1000); // 给页面一些额外的加载时间
        }
      }
      
      chrome.tabs.onUpdated.addListener(listener);
    });
  } catch (error) {
    console.error('Error executing automation:', error);
    automationState.navigationInProgress = false; // 发生错误时重置导航状态
    throw error;
  }
}

// 处理当前步骤
async function handleCurrentStep(tabId, instruction) {
  try {
    // 适配不同的指令格式
    let elementsToClick;
    let isLastStep = false;
    let currentStepIndex = 0;
    
    if (instruction.action === 'navigate_and_click') {
      elementsToClick = instruction.elements_to_click;
      isLastStep = true; // 单步操作，完成后就结束
    } else if (instruction.action === 'multi_step_navigation') {
      // 从存储中获取当前步骤索引
      const data = await chrome.storage.local.get('pendingAutomation');
      const pendingAutomation = data.pendingAutomation || { 
        instruction: instruction,
        currentStepIndex: 0,
        lastUpdated: Date.now(),
        executedSteps: [] // 添加已执行步骤追踪
      };
      
      currentStepIndex = pendingAutomation.currentStepIndex || 0;
      const executedSteps = pendingAutomation.executedSteps || [];
      
      console.log(`Processing step ${currentStepIndex} of multi-step navigation`);
      
      // 检查当前步骤是否已执行过
      if (executedSteps.includes(currentStepIndex)) {
        console.log(`Step ${currentStepIndex} already executed, skipping to next step`);
        
        // 如果当前步骤已执行，递增到下一步
        const nextStepIndex = currentStepIndex + 1;
        
        // 检查是否已完成所有步骤
        if (nextStepIndex >= instruction.steps.length) {
          console.log('All steps already completed, clearing pending automation');
          await chrome.storage.local.remove('pendingAutomation');
          automationState.isRunning = false;
          return { status: 'completed' };
        }
        
        // 更新到下一步
        await chrome.storage.local.set({
          'pendingAutomation': {
            instruction: instruction,
            currentStepIndex: nextStepIndex,
            lastUpdated: Date.now(),
            executedSteps: executedSteps
          }
        });
        
        // 递归处理下一步
        return handleCurrentStep(tabId, instruction);
      }
      
      // 只发送当前步骤
      if (currentStepIndex < instruction.steps.length) {
        // 复制当前步骤以避免引用问题
        const currentStep = {...instruction.steps[currentStepIndex]};
        console.log('Current step:', currentStep);
        elementsToClick = [currentStep];
        
        // 更新下一步的索引
        const nextStepIndex = currentStepIndex + 1;
        isLastStep = nextStepIndex >= instruction.steps.length;
        
        // 记录当前步骤为已执行
        executedSteps.push(currentStepIndex);
        
        // 只有在还有下一步时才更新存储
        if (!isLastStep) {
          console.log(`Updating to next step: ${nextStepIndex}`);
          await chrome.storage.local.set({
            'pendingAutomation': {
              instruction: instruction,
              currentStepIndex: nextStepIndex,
              lastUpdated: Date.now(),
              executedSteps: executedSteps
            }
          });
        } else {
          console.log('This is the last step, will clear pendingAutomation after execution');
        }
      } else {
        console.log('All steps completed, clearing pending automation');
        await chrome.storage.local.remove('pendingAutomation');
        automationState.isRunning = false;
        return { status: 'completed' };
      }
    }
    
    // 发送消息到内容脚本
    return new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(
        tabId, 
        { type: 'AUTOMATION_CLICK', elementsToClick: elementsToClick },
        async (response) => {
          if (chrome.runtime.lastError) {
            console.error('Error sending message:', chrome.runtime.lastError);
            reject(chrome.runtime.lastError);
          } else {
            console.log(`Successfully executed step ${currentStepIndex}`);
            
            // 如果是最后一步，清理存储
            if (isLastStep) {
              console.log('Last step completed, cleaning up...');
              await chrome.storage.local.remove('pendingAutomation');
              automationState.isRunning = false;
            }
            resolve(response);
          }
        }
      );
    });
  } catch (error) {
    console.error('Error handling current step:', error);
    // 发生错误时，也需要清理状态，避免卡住
    automationState.isRunning = false;
    throw error;
  }
}

// 检查是否有待处理的自动化任务并继续执行
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    chrome.storage.local.get('pendingAutomation', async (data) => {
      const pendingAutomation = data.pendingAutomation;
      
      // 检查是否有未完成的多步骤操作
      if (pendingAutomation && pendingAutomation.instruction) {
        // 检查最后更新时间，避免处理过期的操作
        const lastUpdated = pendingAutomation.lastUpdated || 0;
        const now = Date.now();
        
        // 如果操作超过5分钟，认为已过期
        if (now - lastUpdated > 5 * 60 * 1000) {
          console.log('Pending automation expired, removing');
          await chrome.storage.local.remove('pendingAutomation');
          return;
        }
        
        console.log('Resuming multi-step navigation');
        setTimeout(() => {
          handleCurrentStep(tabId, pendingAutomation.instruction).catch(error => {
            console.error('Error resuming automation:', error);
          });
        }, 2000); // 给页面足够的加载时间
      }
    });
  }
});

// 初始化扩展
chrome.runtime.onInstalled.addListener(initialize); 