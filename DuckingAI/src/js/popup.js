<<<<<<< HEAD
// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
  // 获取UI元素
  const triggerButton = document.getElementById('triggerAutomation');
  const pollingToggle = document.getElementById('pollingToggle');
  const statusDiv = document.getElementById('status');
  
  // 更新状态函数
  function updateStatus(message, isError = false) {
    statusDiv.textContent = message;
    statusDiv.className = isError ? 'error' : 'success';
    
    // 3秒后清除状态
    setTimeout(() => {
      statusDiv.textContent = '';
      statusDiv.className = '';
    }, 3000);
  }
  
  // 为触发自动化按钮添加点击事件
  if (triggerButton) {
    triggerButton.addEventListener('click', function() {
      updateStatus('触发自动化操作...');
      
      chrome.runtime.sendMessage({
        type: 'TRIGGER_AUTOMATION'
      }, function(response) {
        if (response && response.status === 'triggered') {
          updateStatus('已成功触发自动化操作');
        } else {
          updateStatus('触发自动化操作失败', true);
        }
      });
    });
  }
  
  // 为轮询开关添加变更事件
  if (pollingToggle) {
    // 初始化开关状态 - 从storage获取
    chrome.storage.local.get(['pollingEnabled'], function(result) {
      if (result.hasOwnProperty('pollingEnabled')) {
        pollingToggle.checked = result.pollingEnabled;
      }
    });
    
    pollingToggle.addEventListener('change', function() {
      const enabled = this.checked;
      
      // 保存状态到storage
      chrome.storage.local.set({ pollingEnabled: enabled });
      
      // 发送消息到background
      chrome.runtime.sendMessage({
        type: 'TOGGLE_POLLING',
        enabled: enabled
      }, function(response) {
        if (response) {
          updateStatus(enabled ? '已开启自动轮询' : '已关闭自动轮询');
        }
      });
    });
  }
}); 
=======
 
>>>>>>> main
