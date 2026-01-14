// Content script for TubeRAG Chrome Extension

let currentVideoId = null;

function getCurrentVideoId() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}

function notifyVideoChange() {
  const videoId = getCurrentVideoId();
  if (videoId && videoId !== currentVideoId) {
    currentVideoId = videoId;
    chrome.runtime.sendMessage({
      type: 'VIDEO_CHANGED',
      videoId: videoId,
      url: window.location.href
    }).catch(() => {});
  }
}

// Listen for URL changes (YouTube uses pushState)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    setTimeout(notifyVideoChange, 1000);
  }
}).observe(document, { subtree: true, childList: true });

// Initial check
setTimeout(notifyVideoChange, 1000);

// Listen for messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'YOUTUBE_VIDEO_DETECTED') {
    notifyVideoChange();
  }
  if (request.type === 'GET_VIDEO_ID') {
    sendResponse({ videoId: getCurrentVideoId() });
  }
});

// Show TubeRAG indicator
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
  
  setTimeout(() => indicator.remove(), 3000);
}

if (window.location.href.includes('youtube.com/watch')) {
  addTubeRAGIndicator();
}