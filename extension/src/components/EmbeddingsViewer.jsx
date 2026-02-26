import React, { useState } from 'react';
import './EmbeddingsViewer.css';

function EmbeddingsViewer({ videoId, apiBaseUrl, embeddings, setEmbeddings }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copyingSubtitles, setCopyingSubtitles] = useState(false);

  const fetchEmbeddings = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/videos/${videoId}/debug`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setEmbeddings(data);

      if (!data.success) {
        setError(data.error || 'Failed to fetch embeddings');
      }

    } catch (err) {
      console.error('Error fetching embeddings:', err);
      setError('Failed to fetch embeddings. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const copySubtitles = async () => {
    setCopyingSubtitles(true);
    try {
      // Fetch full transcript from backend
      const response = await fetch(`${apiBaseUrl}/videos/${videoId}/transcript`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.transcript) {
        // Copy to clipboard
        await navigator.clipboard.writeText(data.transcript);
        alert('✅ Subtitles copied to clipboard!');
      } else {
        alert('❌ Failed to fetch subtitles: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error copying subtitles:', err);
      alert('❌ Failed to copy subtitles. Make sure the backend server is running.');
    } finally {
      setCopyingSubtitles(false);
    }
  };

  const formatEmbedding = (embedding) => {
    if (!embedding || embedding.length === 0) return 'No embedding data';
    return `[${embedding.map(val => val.toFixed(4)).join(', ')}]`;
  };

  const getEmbeddingStatus = (embedding) => {
    if (!embedding || embedding.length === 0) return { status: 'empty', color: '#999' };
    
    const nonZeroCount = embedding.filter(val => val !== 0).length;
    if (nonZeroCount === 0) {
      return { status: 'all zeros', color: '#f44336' };
    } else if (nonZeroCount < embedding.length * 0.1) {
      return { status: 'mostly zeros', color: '#ff9800' };
    } else {
      return { status: 'valid', color: '#4caf50' };
    }
  };

  return (
    <div className="embeddings-viewer">
      {!embeddings && !loading && (
        <div className="welcome-section">
          <div className="welcome-content">
            <h3>🔍 Embeddings Inspector</h3>
            <p>View the stored vector embeddings for this video's transcript chunks.</p>
            <button 
              className="inspect-button primary"
              onClick={fetchEmbeddings}
              disabled={loading}
            >
              🔍 Inspect Embeddings
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-section">
          <div className="loading-spinner"></div>
          <p>Fetching embeddings data...</p>
        </div>
      )}

      {error && (
        <div className="error-section">
          <div className="error-message">⚠️ {error}</div>
          <button className="inspect-button secondary" onClick={fetchEmbeddings}>
            🔄 Try Again
          </button>
        </div>
      )}

      {embeddings && embeddings.success && (
        <div className="embeddings-results">
          <div className="summary-section">
            <h3>📊 Embeddings Summary</h3>
            <div className="summary-stats">
              <div className="stat-item">
                <span className="stat-label">Video ID:</span>
                <span className="stat-value">{embeddings.video_id}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Collection:</span>
                <span className="stat-value">{embeddings.collection_name}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Total Chunks:</span>
                <span className="stat-value">{embeddings.total_chunks}</span>
              </div>
            </div>
          </div>

          {embeddings.sample_chunks && embeddings.sample_chunks.length > 0 && (
            <div className="chunks-section">
              <h4>📝 Sample Chunks</h4>
              {embeddings.sample_chunks.map((chunk, index) => {
                const embeddingStatus = getEmbeddingStatus(chunk.embedding_sample);
                return (
                  <div key={index} className="chunk-item">
                    <div className="chunk-header">
                      <span className="chunk-id">{chunk.id}</span>
                      <span className="embedding-status" style={{ color: embeddingStatus.color }}>
                        {embeddingStatus.status}
                      </span>
                    </div>
                    <div className="chunk-text">
                      <strong>Text Preview:</strong>
                      <p>{chunk.text_preview}</p>
                      <small>Length: {chunk.text_length} characters</small>
                    </div>
                    <div className="chunk-embedding">
                      <strong>Embedding Info:</strong>
                      <div className="embedding-details">
                        <div>Dimensions: {chunk.embedding_dimensions}</div>
                        <div>Sample (first 5): {formatEmbedding(chunk.embedding_sample)}</div>
                      </div>
                    </div>
                    {chunk.metadata && (
                      <div className="chunk-metadata">
                        <strong>Metadata:</strong>
                        <pre>{JSON.stringify(chunk.metadata, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          <div className="actions-section">
            <button className="inspect-button secondary" onClick={fetchEmbeddings} disabled={loading}>
              🔄 Refresh Data
            </button>
            <button 
              className="inspect-button primary" 
              onClick={copySubtitles} 
              disabled={copyingSubtitles}
              style={{ marginLeft: '10px' }}
            >
              {copyingSubtitles ? '⏳ Copying...' : '📋 Copy Subtitles'}
            </button>
          </div>
        </div>
      )}

      {embeddings && !embeddings.success && (
        <div className="no-data-section">
          <h3>📭 No Embeddings Found</h3>
          <p>This video hasn't been indexed yet. Try chatting with the video first to create embeddings.</p>
          <button className="inspect-button secondary" onClick={fetchEmbeddings}>
            🔄 Check Again
          </button>
        </div>
      )}
    </div>
  );
}

export default EmbeddingsViewer;
