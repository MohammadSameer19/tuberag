import requests
from typing import List, Optional
from manual_transcript import get_transcript_fallback
import chromadb
import logging

logger = logging.getLogger(__name__)


class ChromaDBVideoRAG:
    """
    RAG engine using ChromaDB vector database.
    Uses Perplexity API for LLM and ChromaDB's default embeddings.
    """

    def __init__(self, perplexity_api_key: str, persist_dir: str = "./chroma_db"):
        self.perplexity_api_key = perplexity_api_key
        self.persist_dir = persist_dir

        # Perplexity API endpoint
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_dir)

        # Current video state
        self.current_video_id = None
        self.current_collection = None

    def _generate_content(self, prompt: str) -> str:
        """Generate content using Perplexity API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1024
            }

            response = requests.post(self.perplexity_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def _fetch_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript from YouTube video."""
        try:
            logger.info(f"Attempting to fetch transcript for video {video_id}")
            transcript_text = get_transcript_fallback(video_id)

            if transcript_text and transcript_text.strip():
                logger.info(f"Successfully fetched transcript ({len(transcript_text)} chars)")
                return transcript_text
            else:
                logger.error(f"No transcript retrieved for video {video_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching transcript: {str(e)}")
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
                    chunk = text[start:start + break_point + 1]
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
            if self.current_video_id == video_id and self.current_collection is not None:
                return True

            collection_name = self._get_collection_name(video_id)

            # Try to get existing collection
            try:
                self.current_collection = self.client.get_collection(name=collection_name)
                count = self.current_collection.count()

                if count > 0:
                    self.current_video_id = video_id
                    logger.info(f"Loaded existing collection for video {video_id}")
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

            # Create collection (ChromaDB handles embeddings automatically)
            self.current_collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"video_id": video_id, "hnsw:space": "cosine"},
            )

            # Add documents to ChromaDB
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"chunk_index": i, "video_id": video_id} for i in range(len(chunks))]

            self.current_collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )

            self.current_video_id = video_id
            logger.info(f"Loaded video {video_id} with {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error loading video {video_id}: {str(e)}")
            return False

    def query(self, question: str, k: int = 4) -> str:
        """Query the loaded video using RAG."""
        if not self.current_collection or not self.current_video_id:
            return "No video loaded. Please load a video first."

        try:
            results = self.current_collection.query(
                query_texts=[question],
                n_results=k,
                include=["documents", "distances"],
            )

            relevant_chunks = results["documents"][0] if results["documents"] else []

            if not relevant_chunks:
                return "No relevant information found in the video transcript."

            context = "\n\n".join(relevant_chunks)

            prompt = f"""Based on the following YouTube video transcript, please answer the question.

Video Transcript Context:
{context}

Question: {question}

IMPORTANT: Respond in the SAME LANGUAGE as the question.

Please provide a helpful and accurate answer based only on the transcript.
If the information is not available, please say so."""

            return self._generate_content(prompt)

        except Exception as e:
            logger.error(f"Error querying video: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"

    def delete_video(self, video_id: str) -> bool:
        """Delete a video's data from ChromaDB."""
        try:
            collection_name = self._get_collection_name(video_id)
            self.client.delete_collection(name=collection_name)

            if self.current_video_id == video_id:
                self.current_video_id = None
                self.current_collection = None

            logger.info(f"Deleted collection for video {video_id}")
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
