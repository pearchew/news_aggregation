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

# --- 1. GLOBAL CONFIGURATION & PATHING ---

# This finds "news_aggregation" by going up from "website_scraping_workflow"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAG_DB_DIR = PROJECT_ROOT / "rag_db"
PAPERS_DIR = PROJECT_ROOT / "website_scraping_workflow"

# Ensure the rag_db folder exists
RAG_DB_DIR.mkdir(exist_ok=True)

def setup_settings():
    """Optimized for 8GB VRAM/16GB RAM"""
    Settings.llm = Ollama(model="qwen2.5:3b", request_timeout=360.0, temperature=0.1)
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
    Settings.text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=150)

class PaperInsights(BaseModel):
    paper_title: str = Field(description="The exact title of the research paper.")
    insight_1: str = Field(description="The overarching conclusion of the paper")
    insight_2: str = Field(description="The effects this paper has on policy or economics and why it matters.")
    insight_3: str = Field(description="The methods or analytical approach used. Focus on the approach.")
    insight_4: str = Field(description="The potential applications and who benefits.")

# --- 2. CORE FUNCTIONS ---

def get_storage_context():
    """Connects to ChromaDB inside the rag_db folder."""
    db_path = RAG_DB_DIR / "paper_brain_db"
    db = chromadb.PersistentClient(path=str(db_path))
    chroma_collection = db.get_or_create_collection("regulatory_papers")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return StorageContext.from_defaults(vector_store=vector_store)

def process_single_paper(file_path, source_label, storage_context):
    """Processes a single file in isolation, appends to CSV, then adds to Brain."""
    csv_path = RAG_DB_DIR / "paper_insights_database.csv"
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
    
    # 4. Append to CSV
    df = pd.DataFrame([data_dict])
    ordered_columns = [
        'source_org', 'file_name', 'paper_title', 
        'insight_1', 'insight_2', 'insight_3', 'insight_4'
    ]
    df = df[ordered_columns]
    df.to_csv(csv_path, mode='a', header=not csv_path.exists(), index=False)
    
    # --- 5. NOW ADD TO THE PERSISTENT BRAIN ---
    # We connect to the giant database and insert the document so the Digest can find it later
    persistent_index = VectorStoreIndex.from_vector_store(
        storage_context.vector_store, 
        storage_context=storage_context
    )
    for doc in documents:
        persistent_index.insert(doc)
    
    return data_dict

def generate_contextual_digest(new_paper_data, storage_context):
    """Compares new paper to the brain and appends to daily_digests.txt in rag_db."""
    output_path = RAG_DB_DIR / "daily_digests.txt"
    
    index = VectorStoreIndex.from_vector_store(storage_context.vector_store, storage_context=storage_context)
    query_engine = index.as_query_engine(similarity_top_k=3) 
    
    digest_prompt = f"""
    New Paper: "{new_paper_data['paper_title']}"
    Main Insight: {new_paper_data['insight_1']}
    
    Write a 'digest' paragraph summarizing this finding and connecting it to previous papers in our database. Limit it to 2000 characters.
    """
    
    response = query_engine.query(digest_prompt)
    
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"\n--- DIGEST: {new_paper_data['file_name']} ---\n{str(response)}\n")
    
    return str(response)

# --- 3. THE ORCHESTRATOR ---

def run_full_pipeline():
    setup_settings()
    storage_context = get_storage_context()
    csv_path = RAG_DB_DIR / "paper_insights_database.csv"

    # Define subfolders within website_scraping_workflow
    folders_to_scan = {
        "hkma_papers": "HKMA", 
        "sfc_papers": "SFC", 
        "bis_research_papers": "BIS",
        "cc_judge_insights": "CC_Judge", 
        "taylorwessing_insights": "TaylorWessing"
    }

    # History check
    processed_files = set()
    if csv_path.exists():
        processed_files = set(pd.read_csv(csv_path)['file_name'].dropna().tolist())

    for folder_name, label in folders_to_scan.items():
        folder_path = PAPERS_DIR / folder_name
        if not folder_path.exists(): continue

        for file_path in folder_path.iterdir():
            if file_path.suffix.lower() not in ['.pdf', '.md', '.txt'] or file_path.name in processed_files:
                continue

            print(f"[{label}] Processing: {file_path.name}...")
            try:
                # Part 1: Extract
                extracted_data = process_single_paper(file_path, label, storage_context)
                # Part 2: Connect to Brain
                generate_contextual_digest(extracted_data, storage_context)
                print("Success.")
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    run_full_pipeline()