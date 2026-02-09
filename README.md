# TubeRAG - Chat with YouTube Videos

A Chrome extension that lets you chat with YouTube videos using RAG (Retrieval-Augmented Generation) and analyze video sentiment from comments.

## Features

- 💬 **Chat with Videos**: Ask questions about video content using AI
- 📊 **Sentiment Analysis**: Analyze viewer sentiment from comments
- 🔍 **Embeddings Viewer**: Inspect stored vector embeddings
- 🧠 **Context Memory**: AI remembers previous questions in the conversation
- 🗄️ **Persistent Storage**: Video transcripts stored in ChromaDB
- 🌍 **Multilingual Support**: Works with 50+ languages

## Architecture

### Backend (Python + Flask)
- **RAG Engine**: ChromaDB for vector storage, Perplexity AI for generation
- **Sentiment Analysis**: Analyzes YouTube comments
- **Transcript Extraction**: Fetches video transcripts

### Frontend (React + Chrome Extension)
- **Chat Interface**: Real-time Q&A with videos
- **Sentiment Dashboard**: Visual sentiment analysis
- **Embeddings Inspector**: Debug vector storage

## Prerequisites

- Python 3.8+
- Node.js 16+
- Chrome Browser
- Perplexity API Key

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tuberag.git
cd tuberag
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your PERPLEXITY_API_KEY
```

### 3. Extension Setup

```bash
cd extension

# Install dependencies
npm install

# Build the extension
npm run build
```

### 4. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Navigate to `tuberag/extension/dist/` folder
5. Click "Select Folder"

## Usage

### Start the Backend

```bash
cd backend
python main.py
```

Server will start on `http://localhost:8000`

### Use the Extension

1. Go to any YouTube video
2. Click the TubeRAG extension icon
3. Choose a feature:
   - **Chat**: Ask questions about the video
   - **Sentiment**: Analyze viewer opinions
   - **Embeddings**: View stored data

## Context Memory

The RAG engine maintains conversation history for each video:

- **Storage**: In-memory dictionary (per video)
- **Capacity**: Last 10 Q&A exchanges
- **Context Window**: Last 3 exchanges included in prompts
- **Benefit**: AI understands follow-up questions

Example:
```
Q1: "What is this video about?"
A1: "This video discusses machine learning..."

Q2: "Can you elaborate on that?"  ← AI knows "that" refers to ML
A2: "Machine learning involves..."
```

**Note**: Context is cleared when:
- Server restarts
- You switch to a different video

## API Endpoints

### Chat
```http
POST /chat
Content-Type: application/json

{
  "video_id": "dQw4w9WgXcQ",
  "question": "What is this video about?",
  "clear_history": false
}
```

### Sentiment Analysis
```http
POST /analyze
Content-Type: application/json

{
  "video_id": "dQw4w9WgXcQ"
}
```

### List Videos
```http
GET /videos
```

### Delete Video
```http
DELETE /videos/{video_id}
```

## Project Structure

```
tuberag/
├── backend/
│   ├── main.py                 # Flask server
│   ├── rag_engine.py           # RAG implementation
│   ├── sentiment_engine.py     # Sentiment analysis
│   ├── manual_transcript.py    # Transcript extraction
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Environment template
│
├── extension/
│   ├── src/                   # React source code
│   │   ├── components/        # React components
│   │   ├── App.jsx           # Main app
│   │   └── main.jsx          # Entry point
│   ├── dist/                  # Built extension (load this)
│   ├── background.js          # Extension background script
│   ├── content.js            # YouTube page script
│   ├── manifest.json         # Extension manifest
│   └── package.json          # Node dependencies
│
└── README.md
```

## Development

### Backend Development

```bash
cd backend
python main.py
```

Make changes to Python files and restart the server.

### Extension Development

```bash
cd extension

# Make changes to files in src/
# Then rebuild:
npm run build

# Reload extension in chrome://extensions/
```

## Configuration

### Backend (.env)

```env
PERPLEXITY_API_KEY=your_api_key_here
CHROMA_PERSIST_DIR=./chroma_db
```

### Extension

Edit `extension/src/App.jsx` to change API base URL:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## Troubleshooting

### Extension shows blank screen
- Make sure you loaded `extension/dist/` folder, not `extension/`
- Check path in chrome://extensions/ ends with `/dist`

### Backend connection errors
- Verify backend is running on port 8000
- Check CORS settings in main.py

### No transcript available
- Video must have captions/subtitles enabled
- Try a different video

### Context not working
- Context is stored in RAM (lost on restart)
- Check backend logs for errors

## Technologies Used

- **Backend**: Python, Flask, ChromaDB, Perplexity AI
- **Frontend**: React, Vite
- **Extension**: Chrome Extension Manifest V3
- **Embeddings**: sentence-transformers (multilingual)
- **Vector DB**: ChromaDB (persistent storage)

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Perplexity AI for LLM generation
- ChromaDB for vector storage
- sentence-transformers for embeddings

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

## Roadmap

- [ ] Persistent context memory (database storage)
- [ ] Multi-video comparison
- [ ] Export chat history
- [ ] Custom AI models
- [ ] Timestamp-based navigation
- [ ] Video summarization
