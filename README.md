# TubeRAG - Intelligent YouTube Video Assistant

A powerful Chrome extension that transforms how you interact with YouTube videos. Chat with video content, analyze viewer sentiment, and generate structured notes - all powered by AI and RAG (Retrieval-Augmented Generation).

## ✨ Features

### 💬 Chat with Videos
Ask questions about any YouTube video and get accurate answers based on the actual transcript. The AI understands context and remembers your conversation.

**Example:**
- "What are the main topics covered?"
- "Explain the concept mentioned at 5:30"
- "Summarize the key takeaways"

### 📊 Sentiment Analysis
Analyze what viewers think about the video by processing YouTube comments. Get insights on:
- Overall sentiment (positive/negative/neutral)
- Worth watching score (0-100)
- Pros and cons
- Key themes from comments
- Confidence level

### 📝 Key Notes Generator
Generate structured, educational notes from video transcripts with:
- **Semantic Clustering**: Groups related content into topics
- **Multiple Formats**: Markdown (.md) or Plain Text (.txt)
- **Detail Levels**: Brief (2-3 topics), Standard (5-8 topics), Detailed (8-10 topics)
- **Smart Caching**: 70-99% token savings on repeated requests
- **Export Options**: Download or copy to clipboard

### 🔍 Embeddings Viewer
Debug and inspect stored vector embeddings for any video. See how content is chunked and stored in the vector database.

### 🧠 Context Memory
The AI remembers your conversation within each video session:
- Stores last 10 Q&A exchanges per video
- Includes last 3 exchanges in prompts for context
- Understands follow-up questions naturally

### 🗄️ Persistent Storage
All video transcripts and embeddings are stored in ChromaDB for instant access:
- No re-processing on subsequent visits
- Fast retrieval with vector similarity search
- Efficient storage with multilingual embeddings

### 🌍 Multilingual Support
Works with 50+ languages using multilingual sentence transformers

## 🏗️ Architecture

### Backend (Python + Flask)
- **RAG Engine** (`rag_engine.py`): ChromaDB vector storage + Perplexity AI for generation
- **Notes Generator** (`notes_engine.py`): Semantic clustering + AI summarization
- **Sentiment Analyzer** (`sentiment_engine.py`): YouTube comment analysis
- **Transcript Extractor** (`manual_transcript.py`): Fetches video captions/subtitles
- **API Server** (`main.py`): Flask REST API with CORS support

### Frontend (React + Chrome Extension)
- **Chat Interface** (`ChatWindow.jsx`): Real-time Q&A with context memory
- **Notes Viewer** (`NotesViewer.jsx`): Generate and export structured notes
- **Sentiment Dashboard** (`SentimentCard.jsx`): Visual sentiment analysis
- **Embeddings Inspector** (`EmbeddingsViewer.jsx`): Debug vector storage
- **Extension Integration**: Background script + content script for YouTube integration

## 📋 Prerequisites

- **Python 3.8+** (for backend server)
- **Node.js 16+** (for building extension)
- **Chrome Browser** (for running extension)
- **Perplexity API Key** ([Get one here](https://www.perplexity.ai/))

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tuberag.git
cd tuberag
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your PERPLEXITY_API_KEY
```

**Required in .env:**
```env
PERPLEXITY_API_KEY=your_api_key_here
CHROMA_PERSIST_DIR=./chroma_db
```

### 3. Extension Setup

```bash
cd extension

# Install dependencies
npm install

# Build the extension
npm run build
```

This creates the `dist/` folder with the built extension.

### 4. Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Navigate to `tuberag/extension/dist/` folder
5. Click **Select Folder**

✅ The TubeRAG icon should appear in your Chrome toolbar!

## 🎯 Usage

### Start the Backend Server

```bash
cd backend
python main.py
```

You should see:
```
🚀 Starting TubeRAG ChromaDB Server...
📍 Server will run on http://localhost:8000
🗄️  Using ChromaDB vector database for persistent storage
✨ Embeddings and chunks are stored efficiently!
```

### Use the Extension

1. **Navigate to any YouTube video**
2. **Click the TubeRAG extension icon** in your Chrome toolbar
3. **Choose a feature** from the tabs:

#### 💬 Chat Tab
- Type questions about the video content
- AI answers based on the actual transcript
- Context is maintained throughout the conversation
- Example: "What is this video about?" → "Can you explain that in simpler terms?"

#### 📊 Sentiment Tab
- Click "Analyze Sentiment" to process comments
- View worth watching score (0-100)
- See pros, cons, and key themes
- Understand overall viewer sentiment

#### 📝 Notes Tab
- Select format: Markdown or Plain Text
- Choose detail level: Brief, Standard, or Detailed
- Click "Generate Notes"
- Download or copy to clipboard
- Notes include:
  - Topic summaries with key points
  - Table of contents

#### 🔍 Embeddings Tab
- View stored chunks for the current video
- Inspect embedding dimensions
- Debug vector storage
- See chunk metadata

## 🧠 Context Memory Explained

The RAG engine maintains intelligent conversation history for each video:

### How It Works
- **Storage**: In-memory dictionary indexed by video ID
- **Capacity**: Stores last 10 Q&A exchanges per video
- **Context Window**: Includes last 3 exchanges in AI prompts
- **Benefit**: AI understands follow-up questions and references

### Example Conversation
```
User: "What is this video about?"
AI: "This video discusses machine learning fundamentals..."

User: "Can you elaborate on that?"  ← AI knows "that" = ML fundamentals
AI: "Machine learning involves training algorithms on data..."

User: "What are some examples?"  ← AI maintains full context
AI: "Based on the video, examples include image recognition..."
```

### Context Lifecycle
- ✅ **Persists**: During the same video session
- ✅ **Maintained**: Across multiple questions
- ❌ **Cleared**: When switching to a different video
- ❌ **Lost**: When backend server restarts

### Clear Context
Send `clear_history: true` in the API request to reset conversation history for a video.

## 📝 Notes Feature Deep Dive

### Token Optimization Strategy

The Notes Generator uses **semantic clustering** to dramatically reduce token usage:

| Video Length | Direct Approach | Clustering Approach | Savings |
|--------------|----------------|---------------------|---------|
| 10 min | ~5,000 tokens | ~1,500 tokens | 70% |
| 30 min | ~17,000 tokens | ~5,000 tokens | 71% |
| 60 min | ~35,000 tokens | ~10,000 tokens | 71% |

**With Caching**: 99% savings on subsequent requests for the same video/format/level

### How It Works

1. **Retrieve Chunks**: Get existing transcript chunks from ChromaDB (no extra cost)
2. **Cluster by Topic**: Use K-means on embeddings to group related content
3. **Select Representatives**: Pick chunks from beginning, middle, and end of each cluster
4. **Summarize**: AI generates explanatory notes for each topic cluster
5. **Format**: Create structured notes
6. **Cache**: Store results for instant retrieval

### Detail Levels

- **Brief**: 2-3 main topics, quick overview (5-8 seconds)
- **Standard**: 5-8 topics, balanced detail (8-12 seconds)
- **Detailed**: 8-10 topics, comprehensive coverage (12-18 seconds)

### Key Benefits

✅ **70-99% token savings** - Clustering reduces tokens dramatically
✅ **Smart caching** - Instant retrieval on subsequent requests
✅ **Accurate representation** - Based on actual content distribution
✅ **Multiple formats** - Markdown or plain text
✅ **GitHub-ready** - Renders automatically in README files and GitHub

## 🔌 API Endpoints

### POST /chat
Chat with a video using RAG.

**Request:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "question": "What is this video about?",
  "clear_history": false
}
```

**Response:**
```json
{
  "success": true,
  "answer": "This video discusses...",
  "video_id": "dQw4w9WgXcQ"
}
```

### POST /analyze
Analyze video sentiment from comments.

**Request:**
```json
{
  "video_id": "dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "success": true,
  "worth_watching_score": 85,
  "overall_sentiment": "positive",
  "summary": "Viewers found this video...",
  "pros": ["Clear explanations", "Good examples"],
  "cons": ["Could be shorter"],
  "key_themes": ["Educational", "Well-produced"],
  "confidence_level": "high",
  "total_comments_analyzed": 150
}
```

### POST /notes
Generate structured notes from video transcript.

**Request:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "format": "markdown",
  "detail_level": "standard",
  "include_timestamps": true,
  "include_diagrams": true,
  "regenerate": false
}
```

**Parameters:**
- `format`: "markdown" or "text"
- `detail_level`: "brief", "standard", or "detailed"
- `include_timestamps`: true/false
- `regenerate`: true/false (bypass cache)

**Response:**
```json
{
  "success": true,
  "notes": "# Video Notes: dQw4w9WgXcQ\n\n...",
  "video_id": "dQw4w9WgXcQ",
  "cached": false,
  "format": "markdown",
  "detail_level": "standard",
  "metadata": {
    "topics_count": 6,
    "chunks_processed": 45,
    "generated_at": "2024-02-06 10:30:00"
  }
}
```

### GET /videos
List all videos stored in ChromaDB.

**Response:**
```json
{
  "success": true,
  "videos": ["dQw4w9WgXcQ", "jNQXAC9IVRw"],
  "count": 2
}
```

### DELETE /videos/{video_id}
Delete a video from ChromaDB.

**Response:**
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "deleted": true
}
```

### GET /
Health check endpoint.

**Response:**
```json
{
  "message": "TubeRAG API (ChromaDB) is running",
  "version": "1.1.1",
  "status": "healthy",
  "database": "ChromaDB"
}
```

## 📁 Project Structure

```
tuberag/
├── backend/
│   ├── main.py                  # Flask REST API server
│   ├── rag_engine.py            # RAG with ChromaDB + context memory
│   ├── notes_engine.py          # Notes generation with clustering
│   ├── sentiment_engine.py      # YouTube comment sentiment analysis
│   ├── manual_transcript.py     # Transcript extraction utility
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── chroma_db/              # ChromaDB persistent storage
│
├── extension/
│   ├── src/                    # React source code
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx          # Chat interface
│   │   │   ├── NotesViewer.jsx         # Notes generator UI
│   │   │   ├── SentimentCard.jsx       # Sentiment dashboard
│   │   │   └── EmbeddingsViewer.jsx    # Debug embeddings
│   │   ├── App.jsx             # Main application component
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Global styles
│   ├── dist/                   # Built extension (LOAD THIS IN CHROME)
│   ├── background.js           # Extension background script
│   ├── content.js              # YouTube page integration
│   ├── manifest.json           # Chrome extension manifest
│   ├── vite.config.js          # Vite build configuration
│   └── package.json            # Node dependencies
│
├── README.md                   # This file
├── CONTEXT_MEMORY.md          # Context memory documentation
├── NOTES_FEATURE.md           # Notes feature documentation
└── .gitignore                 # Git ignore rules
```

## 🛠️ Development

### Backend Development

```bash
cd backend

# Start development server
python main.py

# The server will run on http://localhost:8000
# Make changes to Python files and restart the server
```

**Key Files:**
- `main.py`: Add new API endpoints here
- `rag_engine.py`: Modify RAG logic, embeddings, or context memory
- `notes_engine.py`: Customize notes generation and clustering
- `sentiment_engine.py`: Adjust sentiment analysis logic

### Extension Development

```bash
cd extension

# Install dependencies (first time only)
npm install

# Make changes to files in src/

# Rebuild the extension
npm run build

# Reload extension in chrome://extensions/
# Click the refresh icon on the TubeRAG extension card
```

**Key Files:**
- `src/App.jsx`: Main app logic and state management
- `src/components/ChatWindow.jsx`: Chat interface
- `src/components/NotesViewer.jsx`: Notes generation UI
- `src/components/SentimentCard.jsx`: Sentiment display
- `vite.config.js`: Build configuration

### Testing

**Test Backend API:**
```bash
# Health check
curl http://localhost:8000/

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"video_id":"dQw4w9WgXcQ","question":"What is this about?"}'

# Test notes generation
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"video_id":"dQw4w9WgXcQ","format":"markdown","detail_level":"standard"}'
```

**Test Extension:**
1. Load extension in Chrome
2. Go to any YouTube video
3. Open Chrome DevTools (F12)
4. Check Console for errors
5. Test each tab (Chat, Sentiment, Notes, Embeddings)

## ⚙️ Configuration

### Backend Environment Variables (.env)

```env
# Required: Perplexity API Key
PERPLEXITY_API_KEY=your_api_key_here

# Optional: ChromaDB storage location
CHROMA_PERSIST_DIR=./chroma_db
```

**Get Perplexity API Key:**
1. Visit [perplexity.ai](https://www.perplexity.ai/)
2. Sign up for an account
3. Navigate to API settings
4. Generate a new API key

### Extension Configuration

Edit `extension/src/App.jsx` to change the API base URL:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

For production deployment, update this to your deployed backend URL.

## 🐛 Troubleshooting

### Extension Issues

**Blank screen when clicking extension**
- ✅ Ensure you loaded `extension/dist/` folder, NOT `extension/` root
- ✅ Check path in `chrome://extensions/` ends with `/dist`
- ✅ Rebuild extension: `cd extension && npm run build`
- ✅ Check browser console (F12) for errors

**Extension not appearing**
- ✅ Verify Developer mode is enabled in `chrome://extensions/`
- ✅ Check that extension is enabled (toggle switch)
- ✅ Try reloading the extension

**State disappears when switching tabs**
- ✅ This was fixed - state should persist across tabs
- ✅ If issue persists, check browser console for errors

### Backend Issues

**Connection errors / "Failed to fetch"**
- ✅ Verify backend is running: `curl http://localhost:8000/`
- ✅ Check backend terminal for errors
- ✅ Ensure port 8000 is not blocked by firewall
- ✅ Verify CORS settings in `main.py`

**"No transcript available" error**
- ✅ Video must have captions/subtitles enabled
- ✅ Try a different video with subtitles
- ✅ Check if video is age-restricted or private

**Context memory not working**
- ✅ Context is stored in RAM (lost on server restart)
- ✅ Check backend logs for errors
- ✅ Verify you're on the same video (context is per-video)

**Notes generation fails**
- ✅ Ensure video has transcript available
- ✅ Check Perplexity API key is valid
- ✅ Try "brief" detail level for faster generation
- ✅ Check backend logs for specific errors

**"Ambiguous truth value" error**
- ✅ This was fixed in `notes_engine.py`
- ✅ Update to latest code and restart backend

### API Issues

**Perplexity API errors**
- ✅ Verify API key is correct in `.env`
- ✅ Check API quota/rate limits
- ✅ Ensure API key has proper permissions

**ChromaDB errors**
- ✅ Delete `chroma_db/` folder and restart (will re-index videos)
- ✅ Check disk space for database storage
- ✅ Verify write permissions for `chroma_db/` directory

### Performance Issues

**Slow notes generation**
- ✅ Use "brief" detail level for faster results
- ✅ First generation is slower (subsequent requests use cache)
- ✅ Long videos (>1 hour) take 15-20 seconds

**High memory usage**
- ✅ Context memory and notes cache are in RAM
- ✅ Restart backend to clear memory
- ✅ Consider implementing persistent cache (future feature)

## 🛠️ Technologies Used

### Backend Stack
- **Python 3.8+**: Core backend language
- **Flask**: REST API server with CORS support
- **ChromaDB**: Vector database for persistent embeddings storage
- **Perplexity AI**: LLM for generation (sonar-pro model)
- **sentence-transformers**: Multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2)
- **scikit-learn**: K-means clustering for notes generation
- **numpy**: Array operations and numerical computing
- **youtube-transcript-api**: Transcript extraction

### Frontend Stack
- **React 18**: UI framework
- **Vite**: Fast build tool and dev server
- **Chrome Extension API**: Manifest V3
- **CSS3**: Styling with modern features

### Key Libraries
- **chromadb**: Vector similarity search
- **requests**: HTTP client for API calls
- **python-dotenv**: Environment variable management
- **flask-cors**: Cross-origin resource sharing

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly**: Backend + Extension
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Submit a pull request**

### Contribution Guidelines
- Follow existing code style
- Add comments for complex logic
- Update documentation for new features
- Test on multiple videos before submitting

## 🙏 Acknowledgments

- **Perplexity AI** for powerful LLM generation
- **ChromaDB** for efficient vector storage
- **sentence-transformers** for multilingual embeddings
- **YouTube** for transcript API access
- All contributors and users of TubeRAG

## 📞 Support

Need help? Here's how to get support:

- **Issues**: [Open an issue on GitHub](https://github.com/yourusername/tuberag/issues)
- **Discussions**: Check existing issues for solutions
- **Documentation**: Read `CONTEXT_MEMORY.md` and `NOTES_FEATURE.md`

## 📊 Performance Metrics

### Token Usage (30-min video)
- **Chat query**: ~500-1,000 tokens per question
- **Sentiment analysis**: ~2,000-3,000 tokens
- **Notes generation**: ~5,000 tokens (first time), 0 tokens (cached)

### Response Times
- **Chat**: 2-4 seconds
- **Sentiment**: 8-12 seconds
- **Notes (Brief)**: 5-8 seconds
- **Notes (Standard)**: 8-12 seconds
- **Notes (Detailed)**: 12-18 seconds

### Storage
- **Per video**: ~2-5 MB (embeddings + chunks)
- **Cache**: In-memory (cleared on restart)

---

**Made with ❤️ for better YouTube learning**
