import requests
import re
import json
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

def get_transcript_new_api(video_id: str) -> Optional[str]:
    """
    Fetch transcript using the new youtube-transcript-api (v1.2.3+).
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # New API: use fetch() method
        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)
        
        if transcript_data:
            text = ' '.join([entry.text for entry in transcript_data])
            logger.info(f"Got transcript via new API for {video_id} ({len(text)} chars)")
            return text
        
        return None
        
    except Exception as e:
        logger.error(f"New API transcript method failed for {video_id}: {str(e)}")
        return None

def get_transcript_manual(video_id: str) -> Optional[str]:
    """
    Manual transcript fetcher that bypasses youtube-transcript-api issues.
    Directly scrapes YouTube's transcript data.
    """
    try:
        # Get the video page
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(video_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        
        # Find the ytInitialPlayerResponse
        pattern = r'var ytInitialPlayerResponse = ({.*?});'
        match = re.search(pattern, html_content)
        
        if not match:
            # Try alternative pattern
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
        
        # Navigate to captions
        captions = player_response.get('captions', {})
        caption_tracks = captions.get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
        
        if not caption_tracks:
            logger.error(f"No caption tracks found for video {video_id}")
            return None
        
        # Find English captions
        english_track = None
        for track in caption_tracks:
            if track.get('languageCode', '').startswith('en'):
                english_track = track
                break
        
        if not english_track:
            english_track = caption_tracks[0]
        
        # Get the transcript URL
        transcript_url = english_track.get('baseUrl')
        if not transcript_url:
            logger.error(f"No transcript URL found for video {video_id}")
            return None
        
        # Add format parameter for JSON
        if '?' in transcript_url:
            transcript_url += '&fmt=json3'
        else:
            transcript_url += '?fmt=json3'
        
        # Fetch the transcript
        transcript_response = requests.get(transcript_url, headers=headers)
        transcript_response.raise_for_status()
        
        # Try JSON format first
        try:
            transcript_json = transcript_response.json()
            events = transcript_json.get('events', [])
            
            full_text = []
            for event in events:
                segs = event.get('segs', [])
                for seg in segs:
                    text = seg.get('utf8', '')
                    if text and text.strip():
                        full_text.append(text.strip())
            
            if full_text:
                result = ' '.join(full_text)
                logger.info(f"Successfully fetched manual transcript (JSON) for video {video_id} ({len(result)} characters)")
                return result
        except:
            pass
        
        # Fallback to XML parsing
        transcript_xml = transcript_response.text
        text_pattern = r'<text[^>]*>(.*?)</text>'
        matches = re.findall(text_pattern, transcript_xml, re.DOTALL)
        
        if matches:
            full_text = []
            for match in matches:
                clean_text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', match)
                clean_text = re.sub(r'<[^>]+>', '', clean_text)
                clean_text = clean_text.strip()
                if clean_text:
                    full_text.append(clean_text)
            
            if full_text:
                result = ' '.join(full_text)
                logger.info(f"Successfully fetched manual transcript (XML) for video {video_id} ({len(result)} characters)")
                return result
        
        logger.error(f"No text found in transcript for video {video_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error in manual transcript fetch for video {video_id}: {str(e)}")
        return None

def get_transcript_fallback(video_id: str) -> Optional[str]:
    """
    Fallback transcript fetcher using multiple methods.
    """
    # Try 1: New youtube-transcript-api (v1.2.3+)
    result = get_transcript_new_api(video_id)
    if result:
        return result
    
    # Try 2: Manual scraping method
    logger.info(f"Trying manual transcript fetch for {video_id}")
    result = get_transcript_manual(video_id)
    if result:
        return result
    
    logger.error(f"All transcript methods failed for {video_id}")
    return None