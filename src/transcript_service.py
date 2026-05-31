import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from google import genai
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
    # Check if we should bypass YouTube and use a local file for testing
    use_local = os.getenv("USE_LOCAL_TRANSCRIPT", "false").lower() == "true"
    if use_local:
        local_path = os.getenv("LOCAL_TRANSCRIPT_PATH")
        if local_path and os.path.exists(local_path):
            logger.info(f"Using local transcript file: {local_path}")
            with open(local_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
                
            logger.info("Translating local transcript to English before returning...")
            try:
                # Use Gemini to translate the text to English before storing in Chroma
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    client = genai.Client(api_key=api_key)
                    # We use gemini-2.5-flash-lite which is the absolute lowest cost and fastest model available
                    response = client.models.generate_content(
                        model='gemini-2.5-flash-lite',
                        contents=f"Translate the following transcript to English. Return ONLY the English translation, nothing else:\n\n{raw_text}"
                    )
                    return response.text
                else:
                    return raw_text
            except Exception as e:
                logger.error(f"Error translating local transcript: {e}")
                return raw_text
        else:
            logger.error(f"Local transcript file not found at path: {local_path}")
            return None

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
