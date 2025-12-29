import requests
import time
from typing import List, Optional
from manual_transcript import get_transcript_fallback
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import logging

logger = logging.getLogger(__name__)

# HuggingFace free Inference API
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"


class HuggingFaceEmbedding(EmbeddingFunction):
    """Embedding function using HuggingFace free Inference API."""

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            for attempt in range(3):
                try:
                    response = requests.post(
                        HF_API_URL,
                        json={"inputs": text[:512], "options": {"wait_for_model": True}},
                        timeout=30
                    )
                    if response.status_code == 200:
                        embedding = response.json()
                        if isinstance(embedding[0], list):
                            embedding = embedding[0]
                        embeddings.append(embedding)
                        break
                    elif response.status_code == 503:
                        time.sleep(2)
                    else:
                        logger.error(f"HF API error: {response.status_code}")
                        embeddings.append([0.0] * 384)
                        break
                except Exception as e:
                    logger.error(f"Embedding error: {e}")
                    if attempt == 2:
                        embeddings.append([0.0] * 384)
        return embeddings


class ChromaDBVideoRAG:
    """RAG engine using ChromaDB with HuggingFace embeddings."""

    def __init__(self, perplexity_api_key: str, persist_dir: str = "./chroma_db"):
        self.perplexity_api_key = perplexity_api_key
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.embedding_fn = HuggingFaceEmbedding()
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.current_video_id = None
        self.current_collection = None

    def _generate_content(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.perplexity_url,
                headers={
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1024
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def _fetch_transcript(self, video_id: str) -> Optional[str]:
        try:
            transcript = get_transcript_fallback(video_id)
            if transcript and transcript.strip():
                logger.info(f"Got transcript for {video_id}")
                return transcript
            return None
        except Exception as e:
            logger.error(f"Transcript error: {e}")
            return None

    def _split_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            if end < len(text):
                break_point = max(chunk.rfind("."), chunk.rfind(" "))
                if break_point > chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            chunks.append(chunk.strip())
            start = end - overlap
        return [c for c in chunks if c.strip()]

    def _get_collection_name(self, video_id: str) -> str:
        return f"video_{video_id.replace('-', '_')}"

    def load_video(self, video_id: str) -> bool:
        try:
            if self.current_video_id == video_id and self.current_collection:
                return True

            collection_name = self._get_collection_name(video_id)

            try:
                self.current_collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_fn
                )
                if self.current_collection.count() > 0:
                    self.current_video_id = video_id
                    return True
            except:
                pass

            transcript = self._fetch_transcript(video_id)
            if not transcript:
                return False

            chunks = self._split_text(transcript)
            if not chunks:
                return False

            logger.info(f"Processing {len(chunks)} chunks...")

            self.current_collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )

            self.current_collection.add(
                ids=[f"chunk_{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=[{"chunk_index": i} for i in range(len(chunks))]
            )

            self.current_video_id = video_id
            logger.info(f"Loaded video {video_id}")
            return True

        except Exception as e:
            logger.error(f"Load error: {e}")
            return False

    def query(self, question: str, k: int = 3) -> str:
        if not self.current_collection:
            return "No video loaded."

        try:
            results = self.current_collection.query(
                query_texts=[question],
                n_results=k
            )

            chunks = results["documents"][0] if results["documents"] else []
            if not chunks:
                return "No relevant information found."

            context = "\n\n".join(chunks)
            prompt = f"""Answer based on this video transcript:

{context}

Question: {question}

Respond in the same language as the question. Be concise and accurate."""

            return self._generate_content(prompt)

        except Exception as e:
            logger.error(f"Query error: {e}")
            return f"Error: {str(e)}"

    def delete_video(self, video_id: str) -> bool:
        try:
            self.client.delete_collection(name=self._get_collection_name(video_id))
            if self.current_video_id == video_id:
                self.current_video_id = None
                self.current_collection = None
            return True
        except:
            return False

    def list_videos(self) -> List[str]:
        try:
            return [c.name[6:].replace("_", "-") for c in self.client.list_collections() if c.name.startswith("video_")]
        except:
            return []
