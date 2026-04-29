import logging
import requests
import os
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field
from llama_index.core import SimpleDirectoryReader, Settings, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

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


def process_single_paper_no_rag(file_path, source_label):
    """Processes a single file in isolation"""
    prompt = "Analyze this specific document and extract the exact title and 4 linked findings. Do not hallucinate."
    
    # 1. Load the document
    documents = SimpleDirectoryReader(input_files=[str(file_path)]).load_data()
    
    # --- THE FIX: CREATE A TEMPORARY IN-MEMORY INDEX ---
    # We do NOT pass the storage_context here. This forces the AI to ONLY look at this one file.
    temp_index = VectorStoreIndex.from_documents(documents)
    
    # 2. Extract Structured Data from the isolated file
    query_engine = temp_index.as_query_engine(output_cls=PaperInsights, response_mode="tree_summarize")
    response = query_engine.query(prompt)
    
    # 3. Prepare metadata
    data_dict = response.response.model_dump()
    data_dict['source_org'] = source_label
    data_dict['file_name'] = file_path.name
    
    return data_dict
