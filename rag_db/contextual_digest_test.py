import os
import pandas as pd
from pathlib import Path
from research_paper_rag_logic import (
    setup_settings, 
    get_storage_context, 
    process_single_paper, 
    generate_contextual_digest,
    PAPERS_DIR,
    RAG_DB_DIR
)

def run_test_on_single_file():
    print("--- STARTING RAG PIPELINE TEST ---")
    
    # 1. Initialize local models (Ollama must be running!)
    print("Initializing Qwen 2.5 3B and Nomic Embed...")
    setup_settings()
    
    # 2. Establish Database Connection
    print(f"Connecting to Brain at: {RAG_DB_DIR / 'paper_brain_db'}")
    storage_context = get_storage_context()
    
    # 3. Path Verification
    # Let's find the FIRST PDF or Markdown file available in any of your folders
    target_label = "CC_Judge"
    
    # Build the full, exact path to the file using pathlib
    target_file = PAPERS_DIR / "hkma_papers" / "03 December 2025_The Stabilising Effect of Domestic Investor Participation in Equity Fund Markets.pdf"

    # Quick safety check to make sure you typed the name perfectly
    if not target_file.exists():
        print(f"ERROR: Could not find the file at {target_file}")
        return

    print(f"Test Subject Found: {target_file} (Source: {target_label})")
    print("-" * 30)

    try:
        # 4. Phase 1: Extraction & CSV Saving
        print("Step 1: Extracting insights to CSV...")
        extracted_data = process_single_paper(target_file, target_label, storage_context)
        print(f"Title: {extracted_data['paper_title']}")
        print(f"Insight 1: {extracted_data['insight_1'][:100]}...")
        
        # 5. Phase 2: Contextual Digest (The Brain Check)
        print("\nStep 2: Searching 'Brain' for related context and generating digest...")
        digest = generate_contextual_digest(extracted_data, storage_context)
        
        print("\n--- TEST DIGEST RESULT ---")
        print(digest)
        print("-" * 30)
        
        print(f"\nSUCCESS: Check {RAG_DB_DIR} for your CSV and Daily Digest text file.")

    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        print("Tip: Check if Ollama is running and you have pulled qwen2.5:3b and nomic-embed-text.")

if __name__ == "__main__":
    run_test_on_single_file()