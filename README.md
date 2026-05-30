# Autonomous Content Orchestration Agent 🤖📈

An autonomous AI agent that seamlessly bridges the gap between raw video data and polished professional content. This project automatically scouts YouTube for trending business videos, downloads transcripts, performs Semantic Vector Search using a local ChromaDB instance, and generates factually-grounded LinkedIn posts using Google's Gemini LLM.

## ✨ Features

- **Retrieval-Augmented Generation (RAG):** Eliminates AI hallucinations by grounding every post in the actual, verified quotes spoken in the video using ChromaDB.
- **Autonomous Subtitle Extraction:** Bypasses YouTube UI limits to securely extract raw `.vtt` subtitles (with automatic on-the-fly translation for non-English videos!).
- **Smart Memory Bank:** Maintains a persistent local JSON state (`memory_bank.json`) so the agent never generates content for the same video twice.
- **Automated Delivery:** Compiles a formatted Markdown brief and automatically dispatches it directly to an executive's email inbox via SMTP.
- **Proxy Support:** Built-in `youtube-transcript-api` proxy rotation to bypass aggressive IP scraping blocks.

## 🏗️ Architecture Flow

1. **Scraper (`youtube_fetcher.py`)**: Uses `yt-dlp` to fetch the latest video metadata from YouTube.
2. **Gatekeeper (`memory_manager.py`)**: Checks the persistent memory bank to ensure absolute novelty. 
3. **Data Miner (`transcript_service.py`)**: Extracts transcripts and dynamically handles translation if required.
4. **Vector Brain (`rag_engine.py`)**: Chunks the transcript, embeds the text using `text-embedding-004`, and indexes it in `ChromaDB`.
5. **Synthesizer (`content_engine.py`)**: Semantically queries the vector database for actionable frameworks and forces the LLM to write the post using *only* the retrieved facts.
6. **Delivery (`email_sender.py`)**: Packages the output and dispatches the brief.

## 🚀 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR-USERNAME/autonomous-content-agent.git
cd autonomous-content-agent
```

### 2. Create the Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and add the following keys:
```env
# AI Engine
GEMINI_API_KEY="your_google_gemini_api_key"

# YouTube Configuration
YOUTUBE_SEARCH_QUERY="AI Business Growth"
YOUTUBE_CHANNELS="" # Optional: comma separated channel IDs
# YOUTUBE_PROXY_URL="http://username:password@proxy-domain:port" # Uncomment to bypass IP bans

# Email Delivery (Must use Gmail App Passwords, NOT your standard password)
EMAIL_SENDER="your-email@gmail.com"
EMAIL_PASSWORD="your-16-digit-app-password"
RECEIVER_EMAIL="executive-email@gmail.com"
```

## 🛠️ Usage

Simply execute the main orchestration script:
```bash
./run.sh
```
*Note: To run this completely autonomously, you can configure a macOS `cron` job to execute this script on a set schedule (e.g., every Monday and Wednesday at 6:00 AM).*

## ⚠️ Notes on IP Blocking
If you run the script too aggressively during testing, YouTube may temporarily block your IP from accessing transcripts (`HTTP 429 Too Many Requests`). If this happens, you can either:
1. Wait 24 hours for the block to lift.
2. Connect your machine to a Mobile Hotspot (which provides a fresh residential IP).
3. Configure a residential proxy in your `.env` file (`YOUTUBE_PROXY_URL`).
