import requests
import time
from typing import List, Optional
from manual_transcript import get_transcript_fallback
import chromadb
import logging

logger = logging.getLogger(__name__)

# Hugging Face Inference API (FREE, no API key required for public models)
HF_EMBEDDING_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class HuggingFaceEmbeddingFunction:
    """Custom embedding function using HuggingFace free Inference API."""
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        embeddings = []
        for text in input:
            embedding = self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _get_embedding(self, text: str, retries: int = 3) -> List[float]:
        """Get embedding for a single text with retry logic."""
        for attempt in range(retries):
            try:
                response = requests.post(
                    HF_EMBEDDING_URL,
                    headers={"Content-Type": "application/json"},
                    json={"inputs": text, "options": {"wait_for_model": True}},
                    timeout=30
                )
                
                if response.status_code == 503:
                    # Model is loading, wait and retry
                    time.sleep(5)
                    continue
                    
                response.raise_for_status()
                result = response.json()
                
                # Handle nested array response
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list):
                        # Average pooling for token embeddings
                        import numpy as np
                        return list(np.mean(result, axis=0))
                    return result
                    
                return result
                
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    raise RuntimeError(f"Failed to get embedding after {retries} attempts: {e}")
        
        return []


class ChromaDBVideoRAG:
    """
    RAG engine using ChromaDB vector database.
    Uses Perplexity API for LLM and HuggingFace free API for multilingual embeddings.
    """

    def __init__(self, perplexity_api_key: str, persist_dir: str = "./chroma_db"):
        self.perplexity_api_key = perplexity_api_key
        self.persist_dir = persist_dir
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        
        # Use HuggingFace free multilingual embeddings
        self.embedding_fn = HuggingFaceEmbeddingFunction()
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_dir)
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
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def _fetch_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript from YouTube video."""
        try:
            logger.info(f"Fetching transcript for video {video_id}")
            transcript_text = get_transcript_fallback(video_id)
            if transcript_text and transcript_text.strip():
                logger.info(f"Got transcript ({len(transcript_text)} chars)")
                return transcript_text
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
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
        return [c for c in chunks if c.strip()]

    def _get_collection_name(self, video_id: str) -> str:
        return f"video_{video_id.replace('-', '_')}"

    def load_video(self, video_id: str) -> bool:
        """Load a video into ChromaDB for RAG processing."""
        try:
            if self.current_video_id == video_id and self.current_collection:
                return True

            collection_name = self._get_collection_name(video_id)

            # Check for existing collection
            try:
                self.current_collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_fn
                )
                if self.current_collection.count() > 0:
                    self.current_video_id = video_id
                    logger.info(f"Loaded existing collection for {video_id}")
                    return True
            except Exception:
                pass

            # Fetch and process transcript
            transcript = self._fetch_transcript(video_id)
            if not transcript:
                return False

            chunks = self._split_text(transcript)
            if not chunks:
                return False

            logger.info(f"Creating embeddings for {len(chunks)} chunks...")

            # Get embeddings from HuggingFace (free API)
            embeddings = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Embedding chunk {i+1}/{len(chunks)}")
                emb = self.embedding_fn._get_embedding(chunk)
                embeddings.append(emb)
                time.sleep(0.1)  # Rate limiting

            # Create collection and add data
            self.current_collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,
                metadata={"video_id": video_id, "hnsw:space": "cosine"},
            )

            self.current_collection.add(
                ids=[f"chunk_{i}" for i in range(len(chunks))],
                embeddings=embeddings,
                documents=chunks,
                metadatas=[{"chunk_index": i, "video_id": video_id} for i in range(len(chunks))],
            )

            self.current_video_id = video_id
            logger.info(f"Loaded video {video_id} with {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error loading video: {e}")
            return False

    def query(self, question: str, k: int = 4) -> str:
        """Query the loaded video using RAG."""
        if not self.current_collection or not self.current_video_id:
            return "No video loaded. Please load a video first."

        try:
            # Get query embedding
            query_embedding = self.embedding_fn._get_embedding(question)

            results = self.current_collection.query(
                query_embeddings=[query_embedding],
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

Please provide a helpful answer based only on the video transcript.
If the information is not available, say so."""

            return self._generate_content(prompt)

        except Exception as e:
            logger.error(f"Error querying: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def delete_video(self, video_id: str) -> bool:
        """Delete a video's data from ChromaDB."""
        try:
            self.client.delete_collection(name=self._get_collection_name(video_id))
            if self.current_video_id == video_id:
                self.current_video_id = None
                self.current_collection = None
            return True
        except Exception as e:
            logger.error(f"Error deleting video: {e}")
            return False

    def list_videos(self) -> List[str]:
        """List all videos stored in ChromaDB."""
        try:
            collections = self.client.list_collections()
            return [c.name[6:].replace("_", "-") for c in collections if c.name.startswith("video_")]
        except Exception as e:
            logger.error(f"Error listing videos: {e}")
            return []
