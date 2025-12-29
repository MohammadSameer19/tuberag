import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import SentimentCard from './components/SentimentCard';
import EmbeddingsViewer from './components/EmbeddingsViewer';

const API_BASE_URL = 'https://tuberag-backend.onrender.com';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [videoId, setVideoId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Extract video ID from current YouTube tab
  useEffect(() => {
    const getCurrentVideoId = async () => {
      try {
        setLoading(true);
        setError(null);

        // Check if we're in a Chrome extension context
        if (typeof chrome !== 'undefined' && chrome.runtime) {
          // Try to get video ID from background script
          chrome.runtime.sendMessage(
            { type: 'GET_CURRENT_VIDEO_ID' },
            (response) => {
              if (chrome.runtime.lastError) {
                console.error('Chrome runtime error:', chrome.runtime.lastError);
                setError('Unable to connect to extension background script');
                setLoading(false);
                return;
              }

              if (response && response.videoId) {
                setVideoId(response.videoId);
                setError(null);
              } else {
                setError('Please navigate to a YouTube video page');
              }
              setLoading(false);
            }
          );
        } else {
          // Fallback for development/testing
          const urlParams = new URLSearchParams(window.location.search);
          const testVideoId = urlParams.get('v') || 'dQw4w9WgXcQ'; // Rick Roll as default
          setVideoId(testVideoId);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error getting video ID:', err);
        setError('Failed to detect YouTube video');
        setLoading(false);
      }
    };

    getCurrentVideoId();

    // Listen for tab changes
    const handleMessage = (message) => {
      if (message.type === 'VIDEO_CHANGED') {
        setVideoId(message.videoId);
        setError(null);
      }
    };

    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.onMessage.addListener(handleMessage);
      return () => {
        chrome.runtime.onMessage.removeListener(handleMessage);
      };
    }
  }, []);

  const formatVideoId = (id) => {
    return id ? `${id.substring(0, 8)}...` : 'None';
  };

  if (loading) {
    return (
      <div className="app">
        <div className="header">
          <h1>TubeRAG</h1>
        </div>
        <div className="loading">
          <div>Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="header">
        <h1>TubeRAG</h1>
      </div>
      
      <div className={`video-info ${error ? 'error' : ''}`}>
        {error ? (
          <div>⚠️ {error}</div>
        ) : (
          <div>📺 Video: {formatVideoId(videoId)}</div>
        )}
      </div>

      {!error && videoId && (
        <>
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 Chat
            </button>
            <button
              className={`tab ${activeTab === 'sentiment' ? 'active' : ''}`}
              onClick={() => setActiveTab('sentiment')}
            >
              📊 Sentiment
            </button>
            <button
              className={`tab ${activeTab === 'embeddings' ? 'active' : ''}`}
              onClick={() => setActiveTab('embeddings')}
            >
              🔍 Embeddings
            </button>
          </div>

          <div className="content">
            {activeTab === 'chat' ? (
              <ChatWindow videoId={videoId} apiBaseUrl={API_BASE_URL} />
            ) : activeTab === 'sentiment' ? (
              <SentimentCard videoId={videoId} apiBaseUrl={API_BASE_URL} />
            ) : (
              <EmbeddingsViewer videoId={videoId} apiBaseUrl={API_BASE_URL} />
            )}
          </div>
        </>
      )}

      {error && (
        <div className="content">
          <div className="error">
            <h3>How to use TubeRAG:</h3>
            <ol>
              <li>Navigate to a YouTube video</li>
              <li>Click the TubeRAG extension icon</li>
              <li>Start chatting with the video or analyze sentiment</li>
            </ol>
            <p><strong>Note:</strong> Make sure the backend server is running on localhost:8000</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;