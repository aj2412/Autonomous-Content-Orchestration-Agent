import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
import logging

logger = logging.getLogger(__name__)
import urllib.parse

def get_video_id(url):
    """Extracts the video ID from a standard YouTube URL."""
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = urllib.parse.parse_qs(parsed_url.query)
            return p.get('v', [None])[0]
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    return None

def fetch_transcript(video_url):
    """
    Attempts to fetch the full transcript for a given YouTube URL.
    Returns the full combined text, or None if transcripts are disabled.
    """
    video_id = get_video_id(video_url)
    if not video_id:
        print(f"Could not parse video ID from {video_url}")
        return None

    try:
        # Check if user has configured a proxy in .env
        proxy_url = os.getenv("YOUTUBE_PROXY_URL")
        
        if proxy_url:
            logger.info(f"Using proxy configuration to bypass IP blocks for video {video_id}")
            proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
            api = YouTubeTranscriptApi(proxy_config=proxy_config)
        else:
            api = YouTubeTranscriptApi()
            
        transcript_list = api.list(video_id)
        
        try:
            transcript = transcript_list.find_transcript(['en'])
        except Exception:
            # If no english, get the first available
            transcript = next(iter(transcript_list))
            try:
                transcript = transcript.translate('en')
            except Exception:
                # If it's not translatable, just use the original language
                # Gemini will naturally translate it when generating the post
                pass

        # Combine all text pieces into a single string
        # .fetch() returns a list of FetchedTranscriptSnippet objects which have a .text attribute
        full_text = " ".join([t.text if hasattr(t, 'text') else t.get('text', '') for t in transcript.fetch()])
        return full_text
    except Exception as e:
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        return None
