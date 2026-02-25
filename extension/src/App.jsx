import React, { useState, useEffect, useMemo } from 'react';
import ChatWindow from './components/ChatWindow';
import SentimentCard from './components/SentimentCard';
import EmbeddingsViewer from './components/EmbeddingsViewer';
import NotesViewer from './components/NotesViewer';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [videoId, setVideoId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Persistent state for each tab
  const [chatMessages, setChatMessages] = useState([]);
  const [sentimentAnalysis, setSentimentAnalysis] = useState(null);
  const [embeddingsData, setEmbeddingsData] = useState(null);
  const [notesData, setNotesData] = useState(null);

  useEffect(() => {
    const getCurrentVideoId = async () => {
      try {
        setLoading(true);
        setError(null);

        if (typeof chrome !== 'undefined' && chrome.runtime) {
          chrome.runtime.sendMessage({ type: 'GET_CURRENT_VIDEO_ID' }, (response) => {
            if (chrome.runtime.lastError) {
              setError('Unable to connect to extension');
              setLoading(false);
              return;
            }

            if (response && response.videoId) {
              // Clear state when video changes
              if (response.videoId !== videoId) {
                setChatMessages([]);
                setSentimentAnalysis(null);
                setEmbeddingsData(null);
                setNotesData(null);
              }
              setVideoId(response.videoId);
              setError(null);
            } else {
              setError('Please navigate to a YouTube video page');
            }
            setLoading(false);
          });
        } else {
          const urlParams = new URLSearchParams(window.location.search);
          const testVideoId = urlParams.get('v') || 'dQw4w9WgXcQ';
          setVideoId(testVideoId);
          setLoading(false);
        }
      } catch (err) {
        setError('Failed to detect YouTube video');
        setLoading(false);
      }
    };

    getCurrentVideoId();

    const handleMessage = (message) => {
      if (message.type === 'VIDEO_CHANGED') {
        // Clear state when video changes
        if (message.videoId !== videoId) {
          setChatMessages([]);
          setSentimentAnalysis(null);
          setEmbeddingsData(null);
          setNotesData(null);
        }
        setVideoId(message.videoId);
        setError(null);
      }
    };

    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.onMessage.addListener(handleMessage);
      return () => chrome.runtime.onMessage.removeListener(handleMessage);
    }
  }, [videoId]);

  const formatVideoId = (id) => {
    return id ? `${id.substring(0, 8)}...` : 'None';
  };

  // Memoize components to prevent unnecessary re-renders
  const chatWindow = useMemo(() => (
    <ChatWindow 
      videoId={videoId} 
      apiBaseUrl={API_BASE_URL}
      messages={chatMessages}
      setMessages={setChatMessages}
    />
  ), [videoId, chatMessages]);

  const sentimentCard = useMemo(() => (
    <SentimentCard 
      videoId={videoId} 
      apiBaseUrl={API_BASE_URL}
      analysis={sentimentAnalysis}
      setAnalysis={setSentimentAnalysis}
    />
  ), [videoId, sentimentAnalysis]);

  const embeddingsViewer = useMemo(() => (
    <EmbeddingsViewer 
      videoId={videoId} 
      apiBaseUrl={API_BASE_URL}
      embeddings={embeddingsData}
      setEmbeddings={setEmbeddingsData}
    />
  ), [videoId, embeddingsData]);

  const notesViewer = useMemo(() => (
    <NotesViewer 
      videoId={videoId} 
      apiBaseUrl={API_BASE_URL}
      notes={notesData}
      setNotes={setNotesData}
    />
  ), [videoId, notesData]);

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
              className={`tab ${activeTab === 'notes' ? 'active' : ''}`}
              onClick={() => setActiveTab('notes')}
            >
              📝 Notes
            </button>
            <button
              className={`tab ${activeTab === 'embeddings' ? 'active' : ''}`}
              onClick={() => setActiveTab('embeddings')}
            >
              🔍 Embeddings
            </button>
          </div>

          <div className="content">
            <div style={{ display: activeTab === 'chat' ? 'flex' : 'none', flexDirection: 'column', height: '100%' }}>
              {chatWindow}
            </div>
            <div style={{ display: activeTab === 'sentiment' ? 'flex' : 'none', flexDirection: 'column', height: '100%' }}>
              {sentimentCard}
            </div>
            <div style={{ display: activeTab === 'notes' ? 'flex' : 'none', flexDirection: 'column', height: '100%' }}>
              {notesViewer}
            </div>
            <div style={{ display: activeTab === 'embeddings' ? 'flex' : 'none', flexDirection: 'column', height: '100%' }}>
              {embeddingsViewer}
            </div>
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