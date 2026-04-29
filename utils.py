import logging
import requests
import os
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field
from llama_index.core import SimpleDirectoryReader, SummaryIndex
from llama_index.llms.ollama import Ollama

logger = logging.getLogger(__name__)

def send_to_discord(webhook_url: str, content: str, username: str = "Digest Bot", avatar_url: str = None) -> None:
    """
    Sends a message to a Discord channel via webhook.
    """
    if webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE" or not webhook_url:
        logger.warning("Skipping Discord notification (no valid webhook URL provided).")
        return

    logger.info(f"Sending summary to Discord as '{username}'...")

    # Discord has a 2000 character limit for the 'content' field.
    if len(content) > 2000:
        logger.warning("Digest exceeds 2000 characters. Truncating for Discord limit...")
        content = content[:1993] + "..."

    payload = {
        "content": content,
        "username": username,
    }
    
    if avatar_url:
        payload["avatar_url"] = avatar_url

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        logger.info("✅ Successfully posted to Discord!")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send to Discord: {e}")
        # If the response exists, it might contain helpful error info from Discord
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"Response content: {e.response.text}")

class PaperInsights(BaseModel):
    paper_title: str = Field(description="The exact title of the research paper.")
    insight_1: str = Field(description="The overarching conclusion of the paper")
    insight_2: str = Field(description="The effects this paper has on policy or economics and why it matters.")
    insight_3: str = Field(description="The methods or analytical approach used. Focus on the approach.")
    insight_4: str = Field(description="The potential applications and who benefits.")


def process_single_paper_no_rag(file_path, source_label, model_name="qwen3:8b"):
    """Processes a single file in isolation using a specified Ollama model."""
    prompt = "Analyze this specific document and extract the exact title and 4 linked findings. Do not hallucinate."
    
    # 1. Initialize the specific LLM requested by the function input
    # Increasing the timeout is recommended for local models processing large documents
    llm = Ollama(model=model_name, request_timeout=300.0) 
    
    # 2. Load the document
    # SimpleDirectoryReader just extracts raw text strings from your PDFs or Markdown files
    documents = SimpleDirectoryReader(input_files=[str(file_path)]).load_data()
    
    # 3. Create a SummaryIndex (Simplified from VectorStoreIndex)
    # By putting the document into a SummaryIndex (formerly called a ListIndex), you are explicitly telling the framework: 
    # "Do not try to search for the most relevant keywords. Read every single chunk of this document sequentially and 
    # summarize it." The index manages the complex task of passing those chunks to the LLM one by one and combining 
    # the answers into your final 4 structured insights.
    temp_index = SummaryIndex.from_documents(documents)
    
    # 4. Extract Structured Data
    # Pass the llm explicitly to the query engine to avoid relying on global Settings
    query_engine = temp_index.as_query_engine(
        llm=llm,
        output_cls=PaperInsights, 
        response_mode="tree_summarize"
    )
    
    response = query_engine.query(prompt)
    
    # 5. Prepare metadata
    data_dict = response.response.model_dump()
    data_dict['source_org'] = source_label
    data_dict['file_name'] = file_path.name
    
    return data_dict
