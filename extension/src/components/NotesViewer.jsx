import React, { useState } from 'react';
import './NotesViewer.css';

function NotesViewer({ videoId, apiBaseUrl, notes, setNotes }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [format, setFormat] = useState('markdown');
  const [detailLevel, setDetailLevel] = useState('standard');

  const generateNotes = async (regenerate = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_id: videoId,
          format: format,
          detail_level: detailLevel,
          include_timestamps: true,
          regenerate: regenerate
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setNotes({
          content: data.notes,
          metadata: data.metadata,
          cached: data.cached,
          format: data.format,
          detailLevel: data.detail_level
        });
      } else {
        setError(data.error || 'Failed to generate notes');
      }

    } catch (err) {
      console.error('Error generating notes:', err);
      setError('Failed to generate notes. Please make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const downloadNotes = () => {
    if (!notes || !notes.content) return;

    const blob = new Blob([notes.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notes_${videoId}.${format === 'markdown' ? 'md' : 'txt'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!notes || !notes.content) return;

    navigator.clipboard.writeText(notes.content).then(() => {
      alert('Notes copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy:', err);
      alert('Failed to copy notes');
    });
  };

  return (
    <div className="notes-viewer">
      {!notes && !loading && (
        <div className="welcome-section">
          <div className="welcome-content">
            <h3>📝 Key Notes Generator</h3>
            <p>Generate structured notes from this video's content.</p>
            
            <div className="options-section">
              <div className="option-group">
                <label>Format:</label>
                <select value={format} onChange={(e) => setFormat(e.target.value)}>
                  <option value="markdown">Markdown (.md)</option>
                  <option value="text">Plain Text (.txt)</option>
                </select>
              </div>

              <div className="option-group">
                <label>Detail Level:</label>
                <select value={detailLevel} onChange={(e) => setDetailLevel(e.target.value)}>
                  <option value="brief">Brief (2-3 topics)</option>
                  <option value="standard">Standard (5-8 topics)</option>
                  <option value="detailed">Detailed (8-10 topics)</option>
                </select>
              </div>
            </div>

            <button 
              className="generate-button primary"
              onClick={() => generateNotes(false)}
              disabled={loading}
            >
              📝 Generate Notes
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-section">
          <div className="loading-spinner"></div>
          <p>Generating notes...</p>
          <small>Analyzing video content and creating structured notes</small>
        </div>
      )}

      {error && (
        <div className="error-section">
          <div className="error-message">
            ⚠️ {error}
          </div>
          <button 
            className="generate-button secondary"
            onClick={() => generateNotes(false)}
          >
            🔄 Try Again
          </button>
        </div>
      )}

      {notes && notes.content && (
        <div className="notes-results">
          <div className="notes-header">
            <div className="notes-info">
              <h3>📝 Generated Notes</h3>
              {notes.cached && <span className="cached-badge">📦 Cached</span>}
              {notes.metadata && (
                <div className="metadata">
                  <span>{notes.metadata.topics_count} topics</span>
                  <span>•</span>
                  <span>{notes.metadata.chunks_processed} segments</span>
                  <span>•</span>
                  <span>{notes.format}</span>
                </div>
              )}
            </div>
            
            <div className="notes-actions">
              <button 
                className="action-button"
                onClick={copyToClipboard}
                title="Copy to clipboard"
              >
                📋 Copy
              </button>
              <button 
                className="action-button"
                onClick={downloadNotes}
                title="Download notes"
              >
                💾 Download
              </button>
              <button 
                className="action-button secondary"
                onClick={() => generateNotes(true)}
                disabled={loading}
                title="Regenerate notes"
              >
                🔄 Regenerate
              </button>
            </div>
          </div>

          <div className="notes-content">
            <pre>{notes.content}</pre>
          </div>

          <div className="notes-footer">
            <div className="format-options">
              <label>Change format:</label>
              <select 
                value={format} 
                onChange={(e) => {
                  setFormat(e.target.value);
                  setNotes(null);
                }}
              >
                <option value="markdown">Markdown</option>
                <option value="text">Plain Text</option>
              </select>
              
              <select 
                value={detailLevel} 
                onChange={(e) => {
                  setDetailLevel(e.target.value);
                  setNotes(null);
                }}
              >
                <option value="brief">Brief</option>
                <option value="standard">Standard</option>
                <option value="detailed">Detailed</option>
              </select>
              
              <button 
                className="generate-button small"
                onClick={() => generateNotes(false)}
              >
                Apply Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NotesViewer;
