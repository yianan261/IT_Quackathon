// 简化的background.js - 只保留基本功能
console.log('DuckingAI Extension initialized');

// 初始化扩展
chrome.runtime.onInstalled.addListener(() => {
  console.log('DuckingAI Extension installed');
}); 