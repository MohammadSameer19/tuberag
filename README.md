# TubeRAG - YouTube RAG Chrome Extension

A Chrome Extension that allows users to chat with YouTube videos using RAG (Retrieval Augmented Generation) and analyze sentiment from comments via a local Python backend.

## 🏗️ Architecture

- **Frontend**: React.js Chrome Extension (Manifest V3)
- **Backend**: Flask (Python) on localhost:8000
- **AI/LLM**: Perplexity API (sonar-pro model)
- **Vector Database**: ChromaDB (local persistence)
- **Embeddings**: Local multilingual sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Data Sources**: YouTube Transcript API + youtube-comment-downloader

## ✨ Features

- 💬 **Chat with Videos**: Ask questions about any YouTube video with captions
- 📊 **Sentiment Analysis**: Analyze video quality from top comments
- 🌍 **Multilingual**: Supports 50+ languages for transcripts and queries
- 💾 **Persistent Storage**: ChromaDB stores embeddings locally
- 🚀 **No Rate Limits**: Local embeddings, no API quotas
- 🔍 **Debug Tools**: Inspect stored embeddings and chunks

## 📁 Project Structure

```
tuberag-project/
├── backend/
│   ├── main.py              # Flask server
│   ├── rag_engine.py        # ChromaDB RAG implementation
│   ├── sentiment_engine.py  # Comment sentiment analysis
│   ├── manual_transcript.py # Transcript fetching utilities
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables
│   └── chroma_db/           # ChromaDB persistent storage
└── extension/
    ├── manifest.json        # Chrome extension manifest
    ├── background.js        # Extension background script
    ├── content.js           # YouTube page integration
    ├── index.html           # Extension popup
    ├── src/                 # React source files
    └── package.json         # Node.js dependencies
```

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd tuberag-project/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env and add your PERPLEXITY_API_KEY

# Run server
python main.py
```

### 2. Get Perplexity API Key

1. Go to [Perplexity AI](https://www.perplexity.ai/)
2. Sign up and navigate to API settings
3. Generate an API key
4. Add to `backend/.env`:
   ```
   PERPLEXITY_API_KEY=your_api_key_here
   ```

### 3. Frontend Setup

```bash
cd tuberag-project/extension

# Install dependencies
npm install

# Build extension
npm run build
```

### 4. Load Chrome Extension

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/videos` | GET | List stored videos |
| `/videos/<id>` | DELETE | Delete video data |
| `/videos/<id>/debug` | GET | Inspect embeddings |
| `/chat` | POST | Chat with video |
| `/analyze` | POST | Sentiment analysis |

## � How It Works

### RAG Pipeline

1. **Fetch Transcript** → YouTube Transcript API (with manual scraping fallback)
2. **Chunk Text** → Split into 1000-char chunks with 100-char overlap
3. **Create Embeddings** → Local multilingual sentence-transformers (supports 50+ languages)
4. **Store in ChromaDB** → Persistent vector storage with cosine similarity
5. **Query** → Semantic search + Perplexity LLM generation

### Sentiment Analysis

1. **Fetch Comments** → youtube-comment-downloader (no API key needed)
2. **Analyze with LLM** → Perplexity API generates insights
3. **Return Scores** → Worth watching score, pros/cons, key themes

## 📋 Requirements

- Python 3.8+
- Node.js 16+
- Perplexity API Key
- Chrome browser

## 🌍 Multilingual Support

TubeRAG supports 50+ languages including:
- English, Spanish, French, German, Italian
- Arabic, Chinese, Japanese, Korean
- Hindi, Portuguese, Russian, Turkish
- And many more!

## 📄 License

MIT License
