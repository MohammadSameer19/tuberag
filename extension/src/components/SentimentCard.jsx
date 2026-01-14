import React, { useState } from 'react';
import './SentimentCard.css';

function SentimentCard({ videoId, apiBaseUrl }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeVideo = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_id: videoId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data);

      if (!data.success && data.error) {
        setError(data.error);
      }

    } catch (err) {
      console.error('Error analyzing video:', err);
      setError('Failed to analyze video. Please make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return '#4caf50'; // Green
    if (score >= 40) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  const getScoreLabel = (score) => {
    if (score >= 70) return 'Highly Recommended';
    if (score >= 40) return 'Mixed Reviews';
    return 'Not Recommended';
  };

  const getSentimentEmoji = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return '😊';
      case 'negative': return '😞';
      case 'mixed': return '😐';
      default: return '🤔';
    }
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence?.toLowerCase()) {
      case 'high': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'low': return '#f44336';
      default: return '#999';
    }
  };

  return (
    <div className="sentiment-card">
      {!analysis && !loading && (
        <div className="welcome-section">
          <div className="welcome-content">
            <h3>📊 Sentiment Analysis</h3>
            <p>Analyze what viewers think about this video based on comments.</p>
            <button 
              className="analyze-button primary"
              onClick={analyzeVideo}
              disabled={loading}
            >
              🔍 Check Quality
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-section">
          <div className="loading-spinner"></div>
          <p>Analyzing comments...</p>
          <small>This may take a few moments</small>
        </div>
      )}

      {error && (
        <div className="error-section">
          <div className="error-message">
            ⚠️ {error}
          </div>
          <button 
            className="analyze-button secondary"
            onClick={analyzeVideo}
          >
            🔄 Try Again
          </button>
        </div>
      )}

      {analysis && (
        <div className="analysis-results">
          <div className="score-section">
            <div 
              className="score-circle"
              style={{ borderColor: getScoreColor(analysis.worth_watching_score) }}
            >
              <div 
                className="score-number"
                style={{ color: getScoreColor(analysis.worth_watching_score) }}
              >
                {analysis.worth_watching_score}
              </div>
              <div className="score-label">
                {getScoreLabel(analysis.worth_watching_score)}
              </div>
            </div>
          </div>

          <div className="sentiment-overview">
            <div className="sentiment-item">
              <span className="sentiment-emoji">
                {getSentimentEmoji(analysis.overall_sentiment)}
              </span>
              <span className="sentiment-text">
                {analysis.overall_sentiment?.charAt(0).toUpperCase() + analysis.overall_sentiment?.slice(1)} Sentiment
              </span>
            </div>
            
            <div className="confidence-item">
              <span 
                className="confidence-badge"
                style={{ backgroundColor: getConfidenceColor(analysis.confidence_level) }}
              >
                {analysis.confidence_level?.toUpperCase()} CONFIDENCE
              </span>
            </div>
          </div>

          <div className="summary-section">
            <h4>📝 Summary</h4>
            <p>{analysis.summary}</p>
          </div>

          {analysis.pros && analysis.pros.length > 0 && (
            <div className="pros-section">
              <h4>✅ Pros</h4>
              <ul>
                {analysis.pros.map((pro, index) => (
                  <li key={index}>{pro}</li>
                ))}
              </ul>
            </div>
          )}

          {analysis.cons && analysis.cons.length > 0 && (
            <div className="cons-section">
              <h4>❌ Cons</h4>
              <ul>
                {analysis.cons.map((con, index) => (
                  <li key={index}>{con}</li>
                ))}
              </ul>
            </div>
          )}

          {analysis.key_themes && analysis.key_themes.length > 0 && (
            <div className="themes-section">
              <h4>🏷️ Key Themes</h4>
              <div className="themes-tags">
                {analysis.key_themes.map((theme, index) => (
                  <span key={index} className="theme-tag">
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="metadata-section">
            <small>
              Based on {analysis.total_comments_analyzed || 0} comments
            </small>
            <button 
              className="analyze-button secondary small"
              onClick={analyzeVideo}
              disabled={loading}
            >
              🔄 Refresh Analysis
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default SentimentCard;