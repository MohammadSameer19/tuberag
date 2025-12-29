# TubeRAG - YouTube RAG Chrome Extension

Chat with YouTube videos using RAG (Retrieval Augmented Generation) and analyze sentiment from comments.

## Features

- 💬 **Chat with Videos** - Ask questions about video content using AI
- 📊 **Sentiment Analysis** - Analyze viewer opinions from comments
- 🔍 **Embeddings Viewer** - Inspect stored vector embeddings
- 🌍 **Multilingual Support** - Works with 100+ languages

## Architecture

- **Frontend**: React Chrome Extension (Manifest V3)
- **Backend**: Flask (Python)
- **LLM**: Perplexity API
- **Vector DB**: ChromaDB (local)
- **Embeddings**: sentence-transformers (local, multilingual)

## Quick Start

### Backend Setup

```bash
cd tuberag-project/backend
pip install -r requirements.txt

# Add your Perplexity API key to .env
# PERPLEXITY_API_KEY=your-key-here

python main.py
```

### Extension Setup

```bash
cd tuberag-project/extension
npm install
npm run build
```

Load in Chrome:
1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → select `extension` folder

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/videos` | GET | List stored videos |
| `/videos/<id>` | DELETE | Delete video data |
| `/videos/<id>/debug` | GET | Inspect embeddings |
| `/chat` | POST | Chat with video |
| `/analyze` | POST | Sentiment analysis |

## Deployment

See `render.yaml` for Render deployment config with persistent storage.

## License

MIT
