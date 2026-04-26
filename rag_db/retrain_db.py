import shutil
import os
import pandas as pd
from pathlib import Path
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# Import your core logic functions from the previous script
from research_paper_rag_logic import (
    get_storage_context, 
    process_single_paper, 
    PROJECT_ROOT, 
    RAG_DB_DIR, 
    PAPERS_DIR
)

def retrain_database(new_llm_model="qwen2.5:3b", new_embed_model="nomic-embed-text"):
    """
    Completely wipes the existing brain and CSV, then re-processes 
    every file in the source folders using the specified models.
    """
    print(f"--- STARTING DATABASE RETRAIN ---")
    print(f"Target LLM: {new_llm_model}")
    print(f"Target Embedding: {new_embed_model}")

    # 1. Update Global Settings for the NEW models
    Settings.llm = Ollama(model=new_llm_model, request_timeout=600.0, temperature=0.1)
    Settings.embed_model = OllamaEmbedding(model_name=new_embed_model)

    # 2. WIPE EXISTING DATA
    # We must delete the old vector folder because embedding math is model-specific
    db_folder = RAG_DB_DIR / "paper_brain_db"
    csv_path = RAG_DB_DIR / "paper_insights_database.csv"
    digest_path = RAG_DB_DIR / "daily_digests.txt"

    if db_folder.exists():
        print(f"Deleting old database at {db_folder}...")
        shutil.rmtree(db_folder)
    
    if csv_path.exists():
        print(f"Archiving old CSV...")
        csv_path.rename(RAG_DB_DIR / "paper_insights_database_OLD.csv")

    # 3. Re-initialize a fresh Storage Context
    storage_context = get_storage_context()

    # 4. Define subfolders to scan (same as main script)
    folders_to_scan = {
        "hkma_papers": "HKMA", 
        "sfc_papers": "SFC", 
        "bis_research_papers": "BIS",
        "cc_judge_insights": "CC_Judge", 
        "taylorwessing_insights": "TaylorWessing"
    }

    # 5. The Full Re-scan Loop (Ignoring history)
    total_files = 0
    for folder_name, label in folders_to_scan.items():
        folder_path = PAPERS_DIR / folder_name
        if not folder_path.exists():
            continue

        print(f"\nRe-indexing {label} papers...")
        
        # We don't check 'processed_files' here because we want a clean slate
        for file_path in folder_path.iterdir():
            if file_path.suffix.lower() not in ['.pdf', '.md', '.txt']:
                continue

            print(f"  -> Processing: {file_path.name}")
            try:
                # Process and save (this function handles the CSV appending)
                process_single_paper(file_path, label, storage_context)
                total_files += 1
            except Exception as e:
                print(f"  [!] Error on {file_path.name}: {e}")

    print(f"\n--- RETRAIN COMPLETE ---")
    print(f"Successfully re-indexed {total_files} files into the new brain.")
    print(f"Location: {RAG_DB_DIR}")

if __name__ == "__main__":
    # You can change these models here whenever you want to upgrade your brain
    retrain_database(
        new_llm_model="qwen2.5:3b", 
        new_embed_model="nomic-embed-text"
    )