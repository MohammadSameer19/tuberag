import requests
import re
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_transcript_new_api(video_id: str, include_timestamps: bool = False) -> Optional[str]:
    """Fetch transcript using youtube-transcript-api.
    
    Args:
        video_id: YouTube video ID
        include_timestamps: If True, includes [timestamp] before each text segment
    
    Returns:
        Transcript text with optional timestamps
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)
        
        if transcript_data:
            if include_timestamps:
                # Format: [0:00] text [0:05] more text
                text = ' '.join([f"[{int(entry.start//60)}:{int(entry.start%60):02d}] {entry.text}" 
                                for entry in transcript_data])
            else:
                text = ' '.join([entry.text for entry in transcript_data])
            
            logger.info(f"Fetched transcript via API for {video_id} ({len(text)} chars, timestamps={include_timestamps})")
            return text
        return None
    except Exception as e:
        logger.error(f"API transcript method failed for {video_id}: {str(e)}")
        return None

def get_transcript_manual(video_id: str) -> Optional[str]:
    """Manual transcript fetcher that scrapes YouTube's transcript data."""
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(video_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        
        # Find ytInitialPlayerResponse
        pattern = r'var ytInitialPlayerResponse = ({.*?});'
        match = re.search(pattern, html_content)
        
        if not match:
            pattern = r'ytInitialPlayerResponse\s*=\s*({.*?});'
            match = re.search(pattern, html_content)
        
        if not match:
            logger.error(f"Could not find ytInitialPlayerResponse for video {video_id}")
            return None
        
        try:
            player_response = json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.error(f"Could not parse ytInitialPlayerResponse for video {video_id}")
            return None
        
        captions = player_response.get('captions', {})
        caption_tracks = captions.get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
        
        if not caption_tracks:
            logger.error(f"No caption tracks found for video {video_id}")
            return None
        
        # Prefer English captions, fallback to first available
        english_track = next((t for t in caption_tracks if t.get('languageCode', '').startswith('en')), caption_tracks[0])
        
        transcript_url = english_track.get('baseUrl')
        if not transcript_url:
            logger.error(f"No transcript URL found for video {video_id}")
            return None
        
        transcript_url += '&fmt=json3' if '?' in transcript_url else '?fmt=json3'
        
        transcript_response = requests.get(transcript_url, headers=headers)
        transcript_response.raise_for_status()
        
        # Try JSON format
        try:
            transcript_json = transcript_response.json()
            events = transcript_json.get('events', [])
            
            full_text = [seg.get('utf8', '').strip() 
                        for event in events 
                        for seg in event.get('segs', []) 
                        if seg.get('utf8', '').strip()]
            
            if full_text:
                result = ' '.join(full_text)
                logger.info(f"Fetched manual transcript (JSON) for {video_id} ({len(result)} chars)")
                return result
        except Exception:
            pass
        
        # Fallback to XML
        matches = re.findall(r'<text[^>]*>(.*?)</text>', transcript_response.text, re.DOTALL)
        
        if matches:
            full_text = []
            for match in matches:
                clean_text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', match)
                clean_text = re.sub(r'<[^>]+>', '', clean_text).strip()
                if clean_text:
                    full_text.append(clean_text)
            
            if full_text:
                result = ' '.join(full_text)
                logger.info(f"Fetched manual transcript (XML) for {video_id} ({len(result)} chars)")
                return result
        
        return None
        
    except Exception as e:
        logger.error(f"Error in manual transcript fetch for video {video_id}: {str(e)}")
        return None

def get_transcript_fallback(video_id: str, include_timestamps: bool = False) -> Optional[str]:
    """Fetch transcript using API, fallback to manual scraping.
    
    Args:
        video_id: YouTube video ID
        include_timestamps: If True, includes [timestamp] before each text segment
    
    Returns:
        Transcript text with optional timestamps
    """
    result = get_transcript_new_api(video_id, include_timestamps)
    if result:
        return result
    
    logger.info(f"Trying manual transcript fetch for {video_id}")
    # Note: Manual scraping doesn't support timestamps
    return get_transcript_manual(video_id)