import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from rag_engine import ChromaDBVideoRAG
from sentiment_engine import analyze_video_sentiment

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for Chrome Extension and web access
CORS(app, origins="*")

# Get API keys from environment
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY environment variable is required")

# Initialize ChromaDB RAG engine with Perplexity
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
rag_engine = ChromaDBVideoRAG(PERPLEXITY_API_KEY, PERSIST_DIR)


@app.route("/", methods=["GET"])
def root():
    """Health check endpoint"""
    return jsonify(
        {
            "message": "TubeRAG API (ChromaDB) is running",
            "version": "1.0.0",
            "status": "healthy",
            "database": "ChromaDB",
            "note": "Using ChromaDB vector database for persistent storage!",
        }
    )


@app.route("/videos", methods=["GET"])
def list_videos():
    """List all videos stored in ChromaDB."""
    try:
        videos = rag_engine.list_videos()
        return jsonify({"videos": videos, "count": len(videos), "success": True})
    except Exception as e:
        return jsonify({"videos": [], "count": 0, "success": False, "error": str(e)})


@app.route("/videos/<video_id>/debug", methods=["GET"])
def debug_video(video_id):
    """Debug endpoint to inspect stored embeddings for a video."""
    try:
        collection_name = f"video_{video_id.replace('-', '_')}"
        
        try:
            collection = rag_engine.client.get_collection(name=collection_name)
        except Exception:
            return jsonify({
                "video_id": video_id,
                "exists": False,
                "error": "Video not found in database",
                "success": False
            })
        
        # Get collection info
        count = collection.count()
        
        # Get sample data (first 3 chunks)
        if count > 0:
            sample = collection.get(
                limit=3,
                include=["documents", "embeddings", "metadatas"]
            )
            
            # Format sample data
            sample_chunks = []
            for i in range(len(sample["ids"])):
                # Handle embeddings - convert numpy arrays to lists
                embeddings = sample.get("embeddings")
                if embeddings is not None and len(embeddings) > i:
                    emb = embeddings[i]
                    # Convert to list if numpy array
                    emb_list = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
                    emb_dims = len(emb_list)
                    emb_sample = [float(x) for x in emb_list[:5]]
                else:
                    emb_dims = 0
                    emb_sample = []
                
                # Handle metadata
                metadatas = sample.get("metadatas")
                metadata = metadatas[i] if metadatas is not None and len(metadatas) > i else {}
                
                chunk_info = {
                    "id": sample["ids"][i],
                    "text_preview": sample["documents"][i][:200] + "..." if len(sample["documents"][i]) > 200 else sample["documents"][i],
                    "text_length": len(sample["documents"][i]),
                    "embedding_dimensions": emb_dims,
                    "embedding_sample": emb_sample,
                    "metadata": metadata
                }
                sample_chunks.append(chunk_info)
        else:
            sample_chunks = []
        
        return jsonify({
            "video_id": video_id,
            "collection_name": collection_name,
            "exists": True,
            "total_chunks": count,
            "sample_chunks": sample_chunks,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({
            "video_id": video_id,
            "exists": False,
            "error": str(e),
            "success": False
        })


@app.route("/videos/<video_id>", methods=["DELETE"])
def delete_video(video_id):
    """Delete a video from ChromaDB."""
    try:
        success = rag_engine.delete_video(video_id)
        return jsonify(
            {
                "video_id": video_id,
                "deleted": success,
                "success": success,
            }
        )
    except Exception as e:
        return jsonify(
            {"video_id": video_id, "deleted": False, "success": False, "error": str(e)}
        )


@app.route("/chat", methods=["POST"])
def chat_with_video():
    """Chat with a YouTube video using ChromaDB RAG."""
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "answer": "Invalid request format",
                        "video_id": "",
                        "success": False,
                        "error": "No JSON data provided",
                    }
                ),
                400,
            )

        video_id = data.get("video_id", "")
        question = data.get("question", "")

        logger.info(f"Chat request for video {video_id}: {question}")

        # Validate video ID
        if not video_id or len(video_id) != 11:
            return (
                jsonify(
                    {
                        "answer": "Invalid YouTube video ID format",
                        "video_id": video_id,
                        "success": False,
                        "error": "Invalid YouTube video ID format",
                    }
                ),
                400,
            )

        # Load video into ChromaDB RAG engine
        if not rag_engine.load_video(video_id):
            return (
                jsonify(
                    {
                        "answer": "This video doesn't have captions/transcripts available. Please try a different video with subtitles enabled.",
                        "video_id": video_id,
                        "success": False,
                        "error": "No transcript available",
                    }
                ),
                404,
            )

        # Query the video
        answer = rag_engine.query(question)

        return jsonify({"answer": answer, "video_id": video_id, "success": True})

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return (
            jsonify(
                {
                    "answer": "Sorry, I encountered an error while processing your question.",
                    "video_id": data.get("video_id", "") if "data" in locals() else "",
                    "success": False,
                    "error": str(e),
                }
            ),
            500,
        )


@app.route("/analyze", methods=["POST"])
def analyze_video():
    """Analyze YouTube video sentiment from comments."""
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "worth_watching_score": 50,
                        "overall_sentiment": "error",
                        "summary": "Invalid request format",
                        "pros": [],
                        "cons": [],
                        "key_themes": [],
                        "confidence_level": "low",
                        "total_comments_analyzed": 0,
                        "video_id": "",
                        "success": False,
                        "error": "No JSON data provided",
                    }
                ),
                400,
            )

        video_id = data.get("video_id", "")

        logger.info(f"Sentiment analysis request for video {video_id}")

        # Validate video ID
        if not video_id or len(video_id) != 11:
            return (
                jsonify(
                    {
                        "worth_watching_score": 50,
                        "overall_sentiment": "error",
                        "summary": "Invalid YouTube video ID format",
                        "pros": [],
                        "cons": [],
                        "key_themes": [],
                        "confidence_level": "low",
                        "total_comments_analyzed": 0,
                        "video_id": video_id,
                        "success": False,
                        "error": "Invalid YouTube video ID format",
                    }
                ),
                400,
            )

        # Analyze video sentiment
        analysis = analyze_video_sentiment(video_id, PERPLEXITY_API_KEY)

        # Check if analysis failed
        if "error" in analysis:
            return jsonify(
                {
                    "worth_watching_score": analysis.get("worth_watching_score", 50),
                    "overall_sentiment": analysis.get("overall_sentiment", "unknown"),
                    "summary": analysis.get("summary", "Analysis failed"),
                    "pros": analysis.get("pros", []),
                    "cons": analysis.get("cons", []),
                    "key_themes": analysis.get("key_themes", []),
                    "confidence_level": analysis.get("confidence_level", "low"),
                    "total_comments_analyzed": analysis.get(
                        "total_comments_analyzed", 0
                    ),
                    "video_id": video_id,
                    "success": False,
                    "error": analysis["error"],
                }
            )

        return jsonify(
            {
                "worth_watching_score": analysis["worth_watching_score"],
                "overall_sentiment": analysis["overall_sentiment"],
                "summary": analysis["summary"],
                "pros": analysis["pros"],
                "cons": analysis["cons"],
                "key_themes": analysis["key_themes"],
                "confidence_level": analysis["confidence_level"],
                "total_comments_analyzed": analysis.get("total_comments_analyzed", 0),
                "video_id": video_id,
                "success": True,
            }
        )

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify(
            {
                "worth_watching_score": 50,
                "overall_sentiment": "error",
                "summary": f"Analysis failed: {str(e)}",
                "pros": [],
                "cons": [],
                "key_themes": [],
                "confidence_level": "low",
                "total_comments_analyzed": 0,
                "video_id": data.get("video_id", "") if "data" in locals() else "",
                "success": False,
                "error": str(e),
            }
        )


if __name__ == "__main__":
    print("🚀 Starting TubeRAG ChromaDB Server...")
    print("📍 Server will run on http://localhost:8000")
    print("🗄️  Using ChromaDB vector database for persistent storage")
    print("✨ Embeddings and chunks are stored efficiently!")
    app.run(host="0.0.0.0", port=8000, debug=False)
