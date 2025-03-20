// Listen for extension installation event
chrome.runtime.onInstalled.addListener(() => {
  console.log('DuckingAI Extension installed');
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'CHAT_MESSAGE') {
    // Process chat message
    console.log('Received chat message:', request.message);
    // Add other processing logic here
  }
}); 