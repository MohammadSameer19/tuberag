import React, { useState, useRef, useEffect } from 'react';
import './ChatWindow.css';

function ChatWindow({ videoId, apiBaseUrl }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset messages when video changes
  useEffect(() => {
    setMessages([]);
    setError(null);
  }, [videoId]);

  const sendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setLoading(true);
    setError(null);

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch(`${apiBaseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_id: videoId,
          question: userMessage
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: data.answer,
        timestamp: new Date(),
        success: data.success
      };

      setMessages(prev => [...prev, aiMessage]);

      if (!data.success && data.error) {
        setError(data.error);
      }

    } catch (err) {
      console.error('Error sending message:', err);
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: 'Sorry, I encountered an error while processing your question. Please make sure the backend server is running.',
        timestamp: new Date(),
        success: false
      };

      setMessages(prev => [...prev, errorMessage]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const suggestedQuestions = [
    "What is this video about?",
    "Summarize the main points",
    "What are the key takeaways?",
    "Who is the target audience?",
    "What topics are covered?"
  ];

  const handleSuggestedQuestion = (question) => {
    setInputValue(question);
  };

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.length === 0 && !loading && (
          <div className="welcome-message">
            <h3>💬 Chat with this video</h3>
            <p>Ask questions about the video content and I'll answer based on the transcript.</p>
            
            <div className="suggested-questions">
              <h4>Try asking:</h4>
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  className="suggested-question"
                  onClick={() => handleSuggestedQuestion(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-header">
              <span className="message-sender">
                {message.type === 'user' ? '👤 You' : '🤖 AI'}
              </span>
              <span className="message-time">
                {formatTime(message.timestamp)}
              </span>
            </div>
            <div className={`message-content ${!message.success ? 'error' : ''}`}>
              {message.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message ai">
            <div className="message-header">
              <span className="message-sender">🤖 AI</span>
            </div>
            <div className="message-content loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about this video..."
            disabled={loading}
            rows={1}
            className="message-input"
          />
          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || loading}
            className="send-button"
          >
            {loading ? '⏳' : '📤'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;