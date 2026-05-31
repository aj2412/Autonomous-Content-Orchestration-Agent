import yt_dlp
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def fetch_recent_videos(query, channels=None, max_results=10):
    """
    Fetches recent videos using yt-dlp based on a search query or a list of channels.
    Returns a list of dicts: {video_id, title, url, description, upload_date}
    """
    results = []
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': True,
        'ignoreerrors': True,
    }

    urls_to_search = []
    
    if channels:
        # If channels are provided, we look at their recent videos
        urls_to_search.extend(channels)
    
    if query:
        # Also do a general search
        urls_to_search.append(f"ytsearch{max_results * 2}:{query}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls_to_search:
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if not entry:
                            continue
                        
                        # yt-dlp might not fetch full descriptions in flat extract, 
                        # but it gets basic metadata.
                        results.append({
                            'video_id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': entry.get('url'),
                            'description': entry.get('description', ''),
                            'upload_date': entry.get('upload_date', '') # format YYYYMMDD
                        })
                else:
                    results.append({
                        'video_id': info.get('id'),
                        'title': info.get('title'),
                        'url': info.get('webpage_url'),
                        'description': info.get('description', ''),
                        'upload_date': info.get('upload_date', '')
                    })
            except Exception as e:
                logger.error(f"Error fetching from {url}: {e}")

    # Deduplicate by video_id
    unique_results = {}
    for res in results:
        if res['video_id'] and res['video_id'] not in unique_results:
            unique_results[res['video_id']] = res

    # Sort or filter if needed, here we just return the top N
    final_list = list(unique_results.values())
    return final_list[:max_results]

def get_video_transcript(video_url):
    """
    Attempt to get subtitles/auto-captions for a video to use as context.
    If none exist, returns the description or empty string.
    """
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'vtt',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Simple fallback to description if we don't parse the VTT here
            # In a full production app, you might parse the downloaded VTT.
            # Here we will rely on description if transcript parsing is complex,
            # or we can use the `google-genai` model to summarize based on description.
            return info.get('description', '')
    except Exception as e:
        logger.error(f"Error fetching transcript for {video_url}: {e}")
        return ""
