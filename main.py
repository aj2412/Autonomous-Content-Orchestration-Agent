import os
from dotenv import load_dotenv
from youtube_fetcher import fetch_recent_videos, get_video_transcript
from memory_manager import is_concept_used, log_concept
from email_sender import send_daily_brief
from transcript_service import fetch_transcript
from rag_engine import RagEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from .env
# Ensure we load from the script's directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv() # Fallback

def run_daily_workflow():
    logger.info("Starting Morning LinkedIn Content Strategist Workflow...")
    
    query = os.getenv("YOUTUBE_SEARCH_QUERY", "AI Business Growth")
    channels_env = os.getenv("YOUTUBE_CHANNELS", "")
    channels = [c.strip() for c in channels_env.split(',') if c.strip()] if channels_env else None

    # Step 1: YouTube Subscriptions & Fresh Data Extraction
    logger.info(f"Fetching recent videos for query '{query}'...")
    videos = fetch_recent_videos(query, channels, max_results=20) # Fetch a few extra to account for duplicates

    if not videos:
        logger.warning("No videos found. Aborting.")
        return

    rag_engine = RagEngine()

    # Step 2: Persistent Memory & De-duplication Check
    selected_videos = []
    for video in videos:
        if len(selected_videos) >= 1:
            break
            
        video_id = video.get('video_id')
        if not video_id:
            continue
            
        if not is_concept_used(video_id):
            logger.info(f"Selected fresh video: {video.get('title')}")
            
            # RAG UPGRADE: Fetch full transcript
            full_transcript = fetch_transcript(video.get('url'))
            
            success = False
            if full_transcript:
                logger.info("Found full transcript! Initializing RAG processing...")
                success = rag_engine.process_transcript(full_transcript)
                if not success:
                    logger.warning("RAG processing failed. Falling back to description.")
            else:
                logger.warning("No transcript available. Falling back to video description.")
                if len(video.get('description', '')) < 50:
                    fallback_transcript = get_video_transcript(video.get('url'))
                    if fallback_transcript:
                        video['description'] += "\n" + fallback_transcript
            
            video['rag_success'] = success
            selected_videos.append(video)
            log_concept(video_id, video.get('title'), video.get('url'))
        else:
            logger.info(f"Skipping already used concept: {video.get('title')}")

    if not selected_videos:
        logger.warning("No fresh concepts found today.")
        return

    # Step 3: Content Engineering & Post Structuring
    logger.info("Generating LinkedIn posts...")
    compiled_brief = "Good morning! Here is your daily LinkedIn Content Brief.\n\n"
    compiled_brief += "="*60 + "\n\n"
    
    for i, video in enumerate(selected_videos, 1):
        logger.info(f"Generating post {i}/1...")
        compiled_brief += f"## Idea {i}: {video.get('title')}\n"
        compiled_brief += f"Source: {video.get('url')}\n\n"
        
        active_rag_engine = rag_engine if video.get('rag_success') else None
        post_content = generate_linkedin_post(video, rag_engine=active_rag_engine)
        compiled_brief += post_content + "\n\n"
        compiled_brief += "="*60 + "\n\n"

    # Step 4: Automated Delivery Protocol
    logger.info("Sending email brief...")
    send_daily_brief(compiled_brief)
    logger.info("Workflow complete!")

if __name__ == "__main__":
    run_daily_workflow()
