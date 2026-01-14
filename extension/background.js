// Background script for TubeRAG Chrome Extension

// Listen for tab updates to detect YouTube navigation
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('youtube.com/watch')) {
    chrome.tabs.sendMessage(tabId, {
      type: 'YOUTUBE_VIDEO_DETECTED',
      url: tab.url
    }).catch(() => {});
  }
});

// Handle messages from content script and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_CURRENT_VIDEO_ID') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0] && tabs[0].url) {
        const videoId = extractVideoId(tabs[0].url);
        sendResponse({ videoId: videoId });
      } else {
        sendResponse({ videoId: null });
      }
    });
    return true;
  }
});

// Extract video ID from YouTube URL
function extractVideoId(url) {
  const match = url.match(/[?&]v=([^&#]*)/);
  return match ? match[1] : null;
}