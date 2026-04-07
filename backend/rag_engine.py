import requests
from typing import List, Optional, Dict
from manual_transcript import get_transcript_fallback
import chromadb
from chromadb.utils import embedding_functions
import logging

logger = logging.getLogger(__name__)


class ChromaDBVideoRAG:
    """
    RAG engine using ChromaDB vector database.
    Uses Perplexity API for LLM generation and local sentence-transformers for embeddings.
    """

    def __init__(self, api_key: str, persist_dir: str = "./chroma_db", api_provider: str = "github", include_timestamps: bool = False):
        self.api_key = api_key
        self.persist_dir = persist_dir
        self.api_provider = api_provider
        self.include_timestamps = include_timestamps

        # API endpoint based on provider
        if api_provider == "github":
            self.api_url = "https://models.github.ai/inference/chat/completions"
            self.model = "openai/gpt-4o"  # Free with Copilot Pro
        else:  # perplexity
            self.api_url = "https://api.perplexity.ai/chat/completions"
            self.model = "sonar-pro"
        
        # Use local multilingual sentence-transformers embedding (supports 50+ languages)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_dir)

        # Current video state
        self.current_video_id = None
        self.current_collection = None
        
        # Conversation history for context memory
        self.conversation_history = {}
        
        # Notes cache for generated notes
        self.notes_cache = {}

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using local sentence-transformers."""
        try:
            embeddings = self.embedding_fn([text])
            return embeddings[0]
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise RuntimeError(f"Failed to get embedding: {e}")

    def _generate_content(self, prompt: str) -> str:
        """Generate content using GitHub Models or Perplexity API."""
        try:
            if self.api_provider == "github":
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                }
            else:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def _fetch_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript from YouTube video."""
        try:
            transcript_text = get_transcript_fallback(video_id, self.include_timestamps)
            if transcript_text and transcript_text.strip():
                logger.info(f"Fetched transcript for {video_id} ({len(transcript_text)} chars, timestamps={self.include_timestamps})")
                return transcript_text
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {str(e)}")
            return None

    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into chunks with overlap."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if end < len(text):
                last_period = chunk.rfind(".")
                last_space = chunk.rfind(" ")
                break_point = max(last_period, last_space)

                if break_point > chunk_size // 2:
                    chunk = text[start : start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return [chunk for chunk in chunks if chunk.strip()]

    def _get_collection_name(self, video_id: str) -> str:
        """Generate a valid collection name from video ID."""
        return f"video_{video_id.replace('-', '_')}"

    def load_video(self, video_id: str) -> bool:
        """Load a video into ChromaDB for RAG processing."""
        try:
            # Clear conversation history when switching videos
            if self.current_video_id != video_id:
                logger.info(f"Switching from video {self.current_video_id} to {video_id}")
            
            if self.current_video_id == video_id and self.current_collection is not None:
                return True

            collection_name = self._get_collection_name(video_id)

            # Try to get existing collection
            try:
                self.current_collection = self.client.get_collection(name=collection_name)
                count = self.current_collection.count()

                if count > 0:
                    self.current_video_id = video_id
                    logger.info(f"Loaded existing ChromaDB collection for video {video_id} with {count} chunks")
                    return True
            except Exception:
                pass

            # Fetch transcript
            transcript = self._fetch_transcript(video_id)
            if not transcript:
                return False

            # Split into chunks
            chunks = self._split_text(transcript)
            if not chunks:
                return False

            logger.info(f"Creating embeddings for {len(chunks)} chunks...")

            # Create embeddings using local model
            embeddings = []
            for i, chunk in enumerate(chunks):
                try:
                    embedding = self._get_embedding(chunk)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to get embedding for chunk {i}: {e}")
                    return False

            # Create collection
            self.current_collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"video_id": video_id, "hnsw:space": "cosine"},
            )

            # Add documents to ChromaDB
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"chunk_index": i, "video_id": video_id} for i in range(len(chunks))]

            self.current_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )

            self.current_video_id = video_id
            logger.info(f"Successfully loaded video {video_id} into ChromaDB with {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error loading video {video_id}: {str(e)}")
            return False

    def query(self, question: str, k: int = 4, use_context: bool = True) -> str:
        """Query the loaded video using RAG with ChromaDB and conversation context."""
        if not self.current_collection or not self.current_video_id:
            return "No video loaded. Please load a video first."

        try:
            query_embedding = self._get_embedding(question)

            results = self.current_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "distances"],
            )

            relevant_chunks = results["documents"][0] if results["documents"] else []

            if not relevant_chunks:
                return "No relevant information found in the video transcript."

            context = "\n\n".join(relevant_chunks)

            # Initialize conversation history for this video if not exists
            if self.current_video_id not in self.conversation_history:
                self.conversation_history[self.current_video_id] = []

            # Build conversation context
            conversation_context = ""
            if use_context and self.conversation_history[self.current_video_id]:
                conversation_context = "\n\nPrevious Conversation:\n"
                for i, exchange in enumerate(self.conversation_history[self.current_video_id][-3:]):  # Last 3 exchanges
                    conversation_context += f"Q{i+1}: {exchange['question']}\nA{i+1}: {exchange['answer']}\n"

            prompt = f"""Based on the following YouTube video transcript, please answer the question.

Video Transcript Context:
{context}
{conversation_context}

Current Question: {question}

Please provide a helpful and accurate answer based on the information available in the video transcript and previous conversation context.
If the information is not available in the transcript, please say so."""

            answer = self._generate_content(prompt)
            
            # Store conversation history
            self.conversation_history[self.current_video_id].append({
                "question": question,
                "answer": answer
            })
            
            # Keep only last 10 exchanges to avoid token limits
            if len(self.conversation_history[self.current_video_id]) > 10:
                self.conversation_history[self.current_video_id] = self.conversation_history[self.current_video_id][-10:]

            return answer

        except Exception as e:
            logger.error(f"Error querying video: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def clear_conversation_history(self, video_id: str = None):
        """Clear conversation history for a specific video or all videos."""
        if video_id:
            if video_id in self.conversation_history:
                self.conversation_history[video_id] = []
        else:
            self.conversation_history = {}

    def delete_video(self, video_id: str) -> bool:
        """Delete a video's data from ChromaDB."""
        try:
            collection_name = self._get_collection_name(video_id)
            self.client.delete_collection(name=collection_name)

            if self.current_video_id == video_id:
                self.current_video_id = None
                self.current_collection = None

            logger.info(f"Deleted ChromaDB collection for video {video_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {str(e)}")
            return False

    def list_videos(self) -> List[str]:
        """List all videos stored in ChromaDB."""
        try:
            collections = self.client.list_collections()
            video_ids = []

            for collection in collections:
                if collection.name.startswith("video_"):
                    video_id = collection.name[6:].replace("_", "-")
                    video_ids.append(video_id)

            return video_ids
        except Exception as e:
            logger.error(f"Error listing videos: {str(e)}")
            return []

    def get_chunks_and_embeddings(self, video_id: str) -> tuple:
        """
        Get all chunks and their embeddings for a video.
        Returns (chunks, embeddings) tuple.
        """
        try:
            # Load video if not already loaded
            if not self.load_video(video_id):
                return ([], [])
            
            # Get all documents and embeddings from collection
            results = self.current_collection.get(
                include=["documents", "embeddings"]
            )
            
            chunks = results.get("documents", [])
            embeddings = results.get("embeddings", [])
            
            logger.info(f"Retrieved {len(chunks)} chunks with embeddings for video {video_id}")
            return (chunks, embeddings)
            
        except Exception as e:
            logger.error(f"Error getting chunks and embeddings: {str(e)}")
            return ([], [])

    def cache_notes(self, video_id: str, detail_level: str, topics: List[Dict]):
        """Cache generated topics for a video (format-agnostic)."""
        cache_key = f"{video_id}_{detail_level}"
        self.notes_cache[cache_key] = {
            "topics": topics,
            "cached_at": self._get_timestamp()
        }
        logger.info(f"Cached topics for {cache_key}")

    def get_cached_notes(self, video_id: str, detail_level: str) -> Optional[List[Dict]]:
        """Retrieve cached topics if available."""
        cache_key = f"{video_id}_{detail_level}"
        cached = self.notes_cache.get(cache_key)
        if cached:
            logger.info(f"Retrieved cached topics for {cache_key}")
            return cached["topics"]
        return None

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
