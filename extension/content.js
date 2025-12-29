// Content script for TubeRAG Chrome Extension
// Runs on YouTube pages to detect video changes and communicate with popup

let currentVideoId = null;

// Function to extract video ID from current URL
function getCurrentVideoId() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}

// Function to notify background script of video changes
function notifyVideoChange() {
  const videoId = getCurrentVideoId();
  if (videoId && videoId !== currentVideoId) {
    currentVideoId = videoId;
    
    // Send message to background script
    chrome.runtime.sendMessage({
      type: 'VIDEO_CHANGED',
      videoId: videoId,
      url: window.location.href
    }).catch(() => {
      // Ignore errors if background script isn't ready
    });
  }
}

// Listen for URL changes (YouTube uses pushState for navigation)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    setTimeout(notifyVideoChange, 1000); // Delay to ensure page is loaded
  }
}).observe(document, { subtree: true, childList: true });

// Initial check when content script loads
setTimeout(notifyVideoChange, 1000);

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'YOUTUBE_VIDEO_DETECTED') {
    notifyVideoChange();
  }
  
  if (request.type === 'GET_VIDEO_ID') {
    sendResponse({ videoId: getCurrentVideoId() });
  }
});

// Inject a small indicator that TubeRAG is active (optional)
function addTubeRAGIndicator() {
  if (document.querySelector('#tuberag-indicator')) return;
  
  const indicator = document.createElement('div');
  indicator.id = 'tuberag-indicator';
  indicator.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: #4285f4;
    color: white;
    padding: 5px 10px;
    border-radius: 15px;
    font-size: 12px;
    z-index: 10000;
    font-family: Arial, sans-serif;
    opacity: 0.8;
  `;
  indicator.textContent = 'TubeRAG Active';
  document.body.appendChild(indicator);
  
  // Remove indicator after 3 seconds
  setTimeout(() => {
    indicator.remove();
  }, 3000);
}

// Show indicator when on YouTube video page
if (window.location.href.includes('youtube.com/watch')) {
  addTubeRAGIndicator();
}