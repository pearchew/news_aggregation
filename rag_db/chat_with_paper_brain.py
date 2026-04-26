import os
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.memory import ChatMemoryBuffer
from research_paper_rag_logic import setup_settings, get_storage_context

def start_chat():
    # 1. Boot up the models
    setup_settings()
    storage_context = get_storage_context()
    
    # 2. Connect to the existing Brain
    # Note: We don't use from_documents here because we are LOADING, not creating.
    index = VectorStoreIndex.from_vector_store(
        storage_context.vector_store, 
        storage_context=storage_context
    )

    # 3. Initialize the Chat Engine with Memory
    # Buffer keeps the last 3900 tokens of conversation in mind
    memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
    
    # chat_engine = index.as_chat_engine(
    # llm=Ollama(model="llama3.2:3b"), # Picking a different model here
    # chat_mode="context",
    # system_prompt=(
    #         "You are a specialized research assistant for a financial expert. "
    #         "You have access to a 'Paper Brain' containing HKMA, SFC, and BIS documents. "
    #         "Always cite the 'file_name' when you mention a specific paper. "
    #         "If you don't know the answer based on the brain, say so—don't hallucinate."
    #     )
    
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        system_prompt=(
            "You are a specialized research assistant for a financial expert. "
            "You have access to a 'Paper Brain' containing HKMA, SFC, BIS, Cambridge Judge Business School, and Taylor Wessing Law Firm articles and documents. "
            "Always cite the 'file_name' when you mention a specific paper. "
            "If you don't know the answer based on the brain, say that you can't answer that question —don't hallucinate."
        )
    )

    print("\n" + "="*50)
    print("CONNECTION ESTABLISHED: YOUR PAPER BRAIN IS ONLINE")
    print("Type 'exit' to close the link.")
    print("="*50 + "\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            break
        
        # Stream the response for that 'typing' feel
        response = chat_engine.chat(user_input)
        print(f"\nBrain: {response}\n")
        
        # Optional: Print the sources used for this specific answer
        if response.source_nodes:
            print("Sources used:")
            for node in response.source_nodes:
                print(f"- {node.metadata.get('file_name', 'Unknown Source')} (Relevance: {node.score:.2f})")
            print("\n")

if __name__ == "__main__":
    start_chat()