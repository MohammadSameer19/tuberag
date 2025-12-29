import json
import requests
from typing import Dict, List
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
import logging

logger = logging.getLogger(__name__)


class SentimentEngine:
    """
    Sentiment analysis engine using Perplexity API for LLM.
    Uses youtube-comment-downloader to fetch comments (no API key needed).
    """

    def __init__(self, perplexity_api_key: str):
        self.perplexity_api_key = perplexity_api_key
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.downloader = YoutubeCommentDownloader()

    def _generate_content(self, prompt: str) -> str:
        """Generate content using Perplexity API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 2048,
            }

            response = requests.post(self.perplexity_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Error: {str(e)}"

    def _fetch_comments(self, video_id: str, max_results: int = 10) -> List[str]:
        """Fetch top comments from YouTube video using youtube-comment-downloader."""
        try:
            comments = []
            count = 0

            # Get comments sorted by popularity
            for comment in self.downloader.get_comments_from_url(
                f"https://www.youtube.com/watch?v={video_id}",
                sort_by=SORT_BY_POPULAR,
            ):
                if count >= max_results:
                    break
                text = comment.get("text", "")
                if text:
                    comments.append(text)
                    count += 1

            logger.info(f"Fetched {len(comments)} comments for video {video_id}")
            return comments

        except Exception as e:
            logger.error(f"Error fetching comments for video {video_id}: {str(e)}")
            return []

    def _analyze_with_llm(self, comments: List[str]) -> Dict:
        """Analyze comments using Perplexity API."""
        try:
            comments_text = "\n".join([f"- {comment}" for comment in comments[:3]])

            prompt = f"""Analyze the following YouTube video comments and provide a comprehensive sentiment analysis.

Comments:
{comments_text}

Please provide your analysis in the following JSON format:
{{
    "worth_watching_score": <number between 0-100>,
    "overall_sentiment": "<positive/negative/mixed>",
    "summary": "<brief summary of overall opinion>",
    "pros": ["<positive aspect 1>", "<positive aspect 2>", "<positive aspect 3>"],
    "cons": ["<negative aspect 1>", "<negative aspect 2>", "<negative aspect 3>"],
    "key_themes": ["<theme 1>", "<theme 2>", "<theme 3>"],
    "confidence_level": "<high/medium/low>"
}}

Guidelines:
- worth_watching_score: 0-30 (not recommended), 31-60 (mixed/average), 61-100 (recommended)
- Focus on content quality, educational value, entertainment value
- Be objective and balanced in your analysis

Respond with ONLY the JSON object, no additional text."""

            response = self._generate_content(prompt)

            # Parse JSON response
            try:
                clean_response = response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.startswith("```"):
                    clean_response = clean_response[3:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()

                analysis = json.loads(clean_response)
                return analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
                return {
                    "worth_watching_score": 50,
                    "overall_sentiment": "mixed",
                    "summary": "Unable to analyze comments properly",
                    "pros": ["Analysis unavailable"],
                    "cons": ["Analysis unavailable"],
                    "key_themes": ["Analysis unavailable"],
                    "confidence_level": "low",
                }

        except Exception as e:
            logger.error(f"Error analyzing comments: {str(e)}")
            return {
                "worth_watching_score": 50,
                "overall_sentiment": "unknown",
                "summary": f"Error during analysis: {str(e)}",
                "pros": ["Analysis failed"],
                "cons": ["Analysis failed"],
                "key_themes": ["Error occurred"],
                "confidence_level": "low",
            }


def analyze_video_sentiment(video_id: str, perplexity_api_key: str) -> Dict:
    """
    Main function to analyze video sentiment from comments.

    Args:
        video_id: YouTube video ID
        perplexity_api_key: Perplexity API key for LLM

    Returns:
        Dictionary containing sentiment analysis results
    """
    try:
        engine = SentimentEngine(perplexity_api_key)

        comments = engine._fetch_comments(video_id)

        if not comments:
            return {
                "worth_watching_score": 50,
                "overall_sentiment": "unknown",
                "summary": "No comments available for analysis. Comments may be disabled for this video.",
                "pros": ["No comments found"],
                "cons": ["Cannot assess video quality"],
                "key_themes": ["Insufficient data"],
                "confidence_level": "low",
                "error": "No comments available",
            }

        analysis = engine._analyze_with_llm(comments)
        analysis["total_comments_analyzed"] = len(comments)
        analysis["video_id"] = video_id

        return analysis

    except Exception as e:
        logger.error(f"Error in analyze_video_sentiment: {str(e)}")
        return {
            "worth_watching_score": 50,
            "overall_sentiment": "error",
            "summary": f"Analysis failed: {str(e)}",
            "pros": ["Analysis unavailable"],
            "cons": ["Technical error occurred"],
            "key_themes": ["Error"],
            "confidence_level": "low",
            "error": str(e),
        }
