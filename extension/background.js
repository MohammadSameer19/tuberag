// Background script for TubeRAG Chrome Extension

// Listen for extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Open side panel when extension icon is clicked
  chrome.sidePanel.open({ windowId: tab.windowId });
});

// Listen for tab updates to detect YouTube navigation
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('youtube.com/watch')) {
    // Send message to content script that we're on a YouTube video page
    chrome.tabs.sendMessage(tabId, {
      type: 'YOUTUBE_VIDEO_DETECTED',
      url: tab.url
    }).catch(() => {
      // Ignore errors if content script isn't ready
    });
  }
});

// Handle messages from content script and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_CURRENT_VIDEO_ID') {
    // Get current active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0] && tabs[0].url) {
        const videoId = extractVideoId(tabs[0].url);
        sendResponse({ videoId: videoId });
      } else {
        sendResponse({ videoId: null });
      }
    });
    return true; // Keep message channel open for async response
  }
});

// Utility function to extract video ID from YouTube URL
function extractVideoId(url) {
  const regex = /[?&]v=([^&#]*)/;
  const match = url.match(regex);
  return match ? match[1] : null;
}