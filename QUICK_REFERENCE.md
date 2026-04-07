# TubeRAG - Quick Reference Guide

**Version:** 1.1.1 | **Last Updated:** March 7, 2026

---

## 🚀 Quick Start

### Start Backend
```bash
cd tuberag/backend
python main.py
# Server runs on http://localhost:8000
```

### Load Extension
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `tuberag/extension` folder

---

## 📊 Features at a Glance

| Feature | What it Does | Speed | Model |
|---------|-------------|-------|-------|
| **Chat** | Q&A with video | 5.89s | GPT-4o |
| **Sentiment** | Analyze comments | 8.48s | GPT-4o mini |
| **Notes** | Generate study notes | 26.84s / 2.07s* | GPT-4o |
| **Embeddings** | View vectors | Instant | - |

*Uncached / Cached

---

## 🔧 Configuration

### API Setup (.env)
```bash
API_PROVIDER=github
GITHUB_API_KEY=ghp_your_key_here
CHROMA_PERSIST_DIR=./chroma_db
```

### Enable Timestamps
```python
# main.py, line 43
include_timestamps=True
```

---

## 📡 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/chat` | POST | Ask questions |
| `/analyze` | POST | Sentiment analysis |
| `/notes` | POST | Generate notes |
| `/videos` | GET | List videos |
| `/videos/<id>` | DELETE | Delete video |

---

## 🎯 Key Metrics

- **Token Savings:** 72.8%
- **Cache Speedup:** 13×
- **Embedding Dims:** 384
- **Chunk Size:** 1000 chars
- **Top-k Retrieval:** 4 chunks
- **Success Rate:** 100%

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| No transcript | Video needs captions |
| 401 Error | Check API key in .env |
| Connection refused | Start backend server |
| Slow response | First load takes 15-30s |
| Out of quota | Wait for daily reset |

---

## 📁 File Locations

```
backend/
├── main.py          # API server
├── rag_engine.py    # RAG logic
├── notes_engine.py  # Notes generation
├── sentiment_engine.py  # Sentiment analysis
└── .env             # Configuration

extension/
├── src/App.jsx      # Main UI
├── background.js    # Extension logic
└── manifest.json    # Extension config
```

---

## 💡 Pro Tips

1. **First load is slow** - Subsequent requests are 13× faster
2. **Use GPT-4o mini** for sentiment to save quota
3. **Format changes are free** - Cached topics, 0 tokens
4. **Clear history** - Use clear_history=true in /chat
5. **Debug mode** - Use /videos/<id>/debug endpoint

---

## 📚 Full Documentation

See `COMPLETE_TECHNICAL_DOCUMENTATION.md` for:
- Detailed architecture
- Algorithm explanations
- API documentation
- Performance optimizations
- Deployment guides

---

**Need Help?** Check the full documentation or troubleshooting section.
