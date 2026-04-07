import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
import requests
import json

logger = logging.getLogger(__name__)


class NotesGenerator:
    """
    Generate structured notes from video transcripts using semantic clustering.
    """

    def __init__(self, api_key: str, api_provider: str = "github"):
        self.api_key = api_key
        self.api_provider = api_provider
        
        # API endpoint based on provider
        if api_provider == "github":
            self.api_url = "https://models.github.ai/inference/chat/completions"
            self.model = "openai/gpt-4o"
        else:  # perplexity
            self.api_url = "https://api.perplexity.ai/chat/completions"
            self.model = "sonar-pro"

    def _generate_content(self, prompt: str, max_tokens: int = 2048) -> str:
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
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Error: {str(e)}"

    def cluster_chunks(
        self, 
        chunks: List[str], 
        embeddings: List[List[float]], 
        n_clusters: Optional[int] = None
    ) -> Dict[int, List[Tuple[int, str]]]:
        """
        Cluster chunks by semantic similarity using embeddings.
        Returns dict of cluster_id -> [(chunk_index, chunk_text), ...]
        """
        if len(chunks) == 0 or len(embeddings) == 0:
            return {}

        # Auto-determine optimal number of clusters
        if n_clusters is None:
            n_chunks = len(chunks)
            if n_chunks < 10:
                n_clusters = 2
            elif n_chunks < 30:
                n_clusters = 3
            elif n_chunks < 50:
                n_clusters = 5
            else:
                n_clusters = min(8, n_chunks // 10)

        n_clusters = min(n_clusters, len(chunks))

        try:
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_array)
            
            # Group chunks by cluster
            clusters = defaultdict(list)
            for idx, (chunk, label) in enumerate(zip(chunks, cluster_labels)):
                clusters[int(label)].append((idx, chunk))
            
            logger.info(f"Clustered {len(chunks)} chunks into {n_clusters} topics")
            return dict(clusters)
            
        except Exception as e:
            logger.error(f"Error clustering chunks: {e}")
            # Fallback: return all chunks in one cluster
            return {0: [(i, chunk) for i, chunk in enumerate(chunks)]}

    def summarize_topic(self, chunks: List[str], topic_num: int) -> Dict[str, str]:
        """
        Summarize a topic cluster into structured notes.
        Returns dict with title, summary, and key points.
        """
        # Select representative chunks - take from beginning, middle, and end
        if len(chunks) <= 3:
            representative_chunks = chunks
        elif len(chunks) <= 6:
            # Take first 2, middle 1, last 1
            mid = len(chunks) // 2
            representative_chunks = [chunks[0], chunks[1], chunks[mid], chunks[-1]]
        else:
            # Take first, two from middle, last
            mid = len(chunks) // 2
            representative_chunks = [chunks[0], chunks[mid-1], chunks[mid], chunks[-1]]
        
        combined_text = "\n\n".join(representative_chunks)
        
        prompt = f"""You are creating educational notes from a video transcript. Analyze this section and provide clear, explanatory notes.

Transcript Section:
{combined_text}

Provide your response in EXACTLY this format:

TITLE: [A clear, descriptive topic title in 5-8 words]

SUMMARY: [Write 2-4 sentences explaining what this section covers. Focus on concepts, explanations, and context - not just events or facts. Make it educational and informative.]

KEY POINTS:
- [First key concept or explanation]
- [Second key concept or explanation]
- [Third key concept or explanation]
- [Fourth key concept or explanation]
- [Fifth key concept or explanation]

Focus on explaining WHY and HOW things work, not just listing WHAT happened. Make the notes educational and easy to understand."""

        try:
            response = self._generate_content(prompt, max_tokens=1000)
            
            # Parse response with improved logic
            lines = response.strip().split('\n')
            title = f"Topic {topic_num + 1}"
            summary = ""
            key_points = []
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if line.upper().startswith('TITLE:'):
                    title = line.split(':', 1)[1].strip()
                    current_section = 'title'
                elif line.upper().startswith('SUMMARY:'):
                    summary = line.split(':', 1)[1].strip()
                    current_section = 'summary'
                elif line.upper().startswith('KEY POINTS:'):
                    current_section = 'keypoints'
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    # Extract key point
                    point = line.lstrip('-•* ').strip()
                    if point and len(point) > 5:
                        key_points.append(point)
                elif current_section == 'summary' and len(line) > 20:
                    # Continue summary if multi-line
                    summary += " " + line
            
            # Clean up title - remove numbering if present
            title = title.lstrip('0123456789. ').strip()
            if not title or len(title) < 3:
                title = f"Topic {topic_num + 1}"
            
            # Ensure we have content
            if not summary or len(summary) < 20:
                summary = "This section covers important concepts and information from the video."
            
            if not key_points:
                key_points = ["Key concepts and explanations from this section"]
            
            return {
                "title": title,
                "summary": summary.strip(),
                "key_points": key_points[:8],  # Limit to 8 points
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error summarizing topic: {e}")
            return {
                "title": f"Topic {topic_num + 1}",
                "summary": "Content from this section of the video.",
                "key_points": ["Key information discussed"],
                "chunk_count": len(chunks)
            }

    def format_notes(
        self, 
        topics: List[Dict[str, str]], 
        video_id: str,
        format_type: str = "markdown",
        include_timestamps: bool = True
    ) -> str:
        """
        Format topic summaries into final notes.
        """
        if format_type == "markdown":
            return self._format_markdown(topics, video_id, include_timestamps)
        elif format_type == "text":
            return self._format_text(topics, video_id, include_timestamps)
        else:
            return self._format_markdown(topics, video_id, include_timestamps)

    def _format_markdown(
        self, 
        topics: List[Dict[str, str]], 
        video_id: str,
        include_timestamps: bool
    ) -> str:
        """Format notes as Markdown."""
        lines = []
        
        # Header
        lines.append(f"# Video Notes: {video_id}")
        lines.append("")
        lines.append(f"**Generated:** {self._get_timestamp()}")
        lines.append(f"**Topics Covered:** {len(topics)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Table of Contents
        lines.append("## 📑 Table of Contents")
        lines.append("")
        for i, topic in enumerate(topics):
            lines.append(f"{i + 1}. [{topic['title']}](#{self._slugify(topic['title'])})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Detailed Notes
        lines.append("## 📝 Detailed Notes")
        lines.append("")
        
        for i, topic in enumerate(topics):
            lines.append(f"### {i + 1}. {topic['title']}")
            lines.append("")
            lines.append(f"**Summary:** {topic['summary']}")
            lines.append("")
            
            if topic.get('key_points'):
                lines.append("**Key Points:**")
                for point in topic['key_points']:
                    lines.append(f"- {point}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Footer
        lines.append("## 💡 Quick Reference")
        lines.append("")
        lines.append("**Main Takeaways:**")
        for i, topic in enumerate(topics[:3]):  # Top 3 topics
            lines.append(f"{i + 1}. {topic['title']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated by TubeRAG - Video ID: {video_id}*")
        
        return "\n".join(lines)

    def _format_text(
        self, 
        topics: List[Dict[str, str]], 
        video_id: str,
        include_timestamps: bool
    ) -> str:
        """Format notes as plain text."""
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"VIDEO NOTES: {video_id}".center(60))
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Generated: {self._get_timestamp()}")
        lines.append(f"Topics Covered: {len(topics)}")
        lines.append("")
        
        # Detailed Notes
        lines.append("-" * 60)
        lines.append("DETAILED NOTES")
        lines.append("-" * 60)
        lines.append("")
        
        for i, topic in enumerate(topics):
            lines.append(f"{i + 1}. {topic['title'].upper()}")
            lines.append("")
            lines.append(f"   Summary: {topic['summary']}")
            lines.append("")
            
            if topic.get('key_points'):
                lines.append("   Key Points:")
                for point in topic['key_points']:
                    lines.append(f"   • {point}")
                lines.append("")
            
            lines.append("")
        
        lines.append("=" * 60)
        lines.append(f"Generated by TubeRAG - Video ID: {video_id}")
        lines.append("=" * 60)
        
        return "\n".join(lines)

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        return text.lower().replace(' ', '-').replace(':', '').replace(',', '')

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_notes(
        self,
        video_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        format_type: str = "markdown",
        detail_level: str = "standard",
        include_timestamps: bool = True
    ) -> Dict[str, any]:
        """
        Main method to generate notes from video chunks.
        
        Args:
            video_id: YouTube video ID
            chunks: List of transcript chunks
            embeddings: List of embedding vectors for chunks
            format_type: "markdown" or "text"
            detail_level: "brief", "standard", or "detailed"
            include_timestamps: Include timestamp information
            
        Returns:
            Dict with notes content and metadata
        """
        try:
            logger.info(f"Generating notes for video {video_id}")
            
            # Determine number of clusters based on detail level
            n_clusters = None
            if detail_level == "brief":
                n_clusters = max(1, min(3, len(chunks) // 15 or 2))
            elif detail_level == "detailed":
                n_clusters = max(1, min(10, len(chunks) // 5 or 5))
            # standard uses auto-detection
            
            # Ensure n_clusters doesn't exceed number of chunks
            if n_clusters is not None:
                n_clusters = min(n_clusters, len(chunks))
            
            # Step 1: Cluster chunks by topic
            clusters = self.cluster_chunks(chunks, embeddings, n_clusters)
            
            # Step 2: Summarize each topic cluster
            topics = []
            for cluster_id, cluster_chunks in sorted(clusters.items()):
                chunk_texts = [chunk for _, chunk in cluster_chunks]
                topic_summary = self.summarize_topic(chunk_texts, cluster_id)
                topics.append(topic_summary)
            
            # Step 3: Format into final notes
            notes_content = self.format_notes(
                topics, 
                video_id, 
                format_type,
                include_timestamps
            )
            
            # Step 4: Generate metadata
            metadata = {
                "video_id": video_id,
                "format": format_type,
                "detail_level": detail_level,
                "topics_count": len(topics),
                "chunks_processed": len(chunks),
                "generated_at": self._get_timestamp(),
                "includes_timestamps": include_timestamps
            }
            
            logger.info(f"Successfully generated notes with {len(topics)} topics")
            
            return {
                "success": True,
                "notes": notes_content,
                "metadata": metadata,
                "topics": topics
            }
            
        except Exception as e:
            logger.error(f"Error generating notes: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notes": "",
                "metadata": {}
            }
