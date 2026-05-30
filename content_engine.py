import os
from google import genai
import logging

logger = logging.getLogger(__name__)

def generate_linkedin_post(video_metadata, rag_engine=None):
    """
    Calls Gemini API to generate a LinkedIn post based on video metadata.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-gemini-api-key":
        return "Error: GEMINI_API_KEY not configured properly.\n\n[LINKEDIN POST START]\nPlaceholder Post\n[LINKEDIN POST END]\n\n[VISUAL ASSET PROMPT START]\nPlaceholder Prompt\n[VISUAL ASSET PROMPT END]"
        
    client = genai.Client(api_key=api_key)
    
    # Use RAG if available
    grounding_context = ""
    description = video_metadata.get('description', '')
    
    if not rag_engine:
        logger.warning("RAG engine not provided or processing failed. Relying strictly on video description.")
        grounding_context = f"Video Description: {description}"
    else:
        logger.info("Retrieving relevant facts from the transcript vector database...")
        q1 = "What is the primary thesis or core lesson of this video?"
        q2 = "What are the step-by-step actionable frameworks or tactics mentioned?"
        
        chunks_1 = rag_engine.semantic_search(q1, n_results=3)
        chunks_2 = rag_engine.semantic_search(q2, n_results=3)
        
        all_chunks = list(set(chunks_1 + chunks_2)) # deduplicate
        if all_chunks:
            grounding_context = "\n\n--- RETRIEVED VERIFIED TRANSCRIPT CHUNKS ---\n"
            for idx, chunk in enumerate(all_chunks, 1):
                grounding_context += f"[Chunk {idx}]:\n{chunk}\n\n"
            grounding_context += "--- END RETRIEVED CHUNKS ---\n"

    # Truncate description to prevent context overflow if it's too long
    if description and not grounding_context:
        description = description[:1500]

    prompt = f"""
    You are an elite, autonomous Content Strategist and LinkedIn Post Planner.
    Your task is to synthesize the following YouTube video concept into a high-converting, natural-sounding LinkedIn post.

    Video Title: {video_metadata.get('title')}
    Video Description/Context: {description}
    {grounding_context}

    Stylistic parameters:
    - Tone: Extremely encouraging, natural, conversational, and compelling. It must sound like an authentic human case study or observation, completely free of generic AI-clichés (avoid words like "delve," "landscape," "testament," "revolutionize," "moreover").
    - Structure:
      1. A pattern-interrupting primary Hook (1-2 lines optimized for mobile screens to force a click on "see more").
      2. The Context/Core Lesson (Breaking down the concept simply).
      3. Actionable Framework/Takeaways (Scannable, short paragraphs or bullet styling).
      4. Engaging Call-to-Action (An interactive question prompting comments).
      5. 3-5 hyper-relevant, targeted hashtags.
    
    CRITICAL GROUNDING CONSTRAINT:
    If "RETRIEVED VERIFIED TRANSCRIPT CHUNKS" are provided above, you MUST base your post entirely on the facts, frameworks, and stories found in those chunks. Do NOT hallucinate external frameworks. If the chunks do not contain a clear framework, adapt the post to focus on the main lesson instead of making up a framework.

    In addition to the post, please provide a vivid, detailed description text prompt for a custom visual graphic, chart, or candid scene that perfectly maps to this post's text.
    
    Format the output exactly as follows:
    
    [LINKEDIN POST START]
    <post content here>
    [LINKEDIN POST END]
    
    [VISUAL ASSET PROMPT START]
    <visual prompt here>
    [VISUAL ASSET PROMPT END]
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return f"Error generating content: {e}\n\n[LINKEDIN POST START]\nError Post\n[LINKEDIN POST END]\n\n[VISUAL ASSET PROMPT START]\nError Prompt\n[VISUAL ASSET PROMPT END]"
