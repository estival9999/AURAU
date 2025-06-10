#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

# Load environment variables
load_dotenv()

async def main():
    # Set API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        return
    
    print(f"API Key found: {api_key[:10]}...")
    
    # Create RAG instance
    rag = LightRAG(
        working_dir="./test_rag",
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
    )
    
    # Test with a simple document
    test_text = """
    This is a test document about LightRAG.
    LightRAG is a powerful tool for creating knowledge graphs from text.
    It uses advanced NLP techniques to extract entities and relationships.
    """
    
    print("Inserting test document...")
    await rag.ainsert(test_text)
    
    print("Querying...")
    result = await rag.aquery("What is LightRAG?")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())