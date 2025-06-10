#!/usr/bin/env python3
import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
import networkx as nx
from pyvis.network import Network
import webbrowser

# Load environment variables
load_dotenv()

# Configuration
WORKING_DIR = "./lightrag_workdir"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Ensure API key is set
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env file!")
    sys.exit(1)

# Create working directory if it doesn't exist
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

async def initialize_rag():
    """Initialize LightRAG with proper configuration."""
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=lambda texts: openai_embed(texts, model="text-embedding-3-small"),
        llm_model_func=openai_complete,
        llm_model_name=OPENAI_MODEL,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

async def insert_documents(rag):
    """Insert all documents into LightRAG."""
    print("\n📚 Inserting documents into LightRAG...")
    
    documents = [
        ("base_3.txt", "Transcrição da Reunião sobre Sistema de Cadastro"),
        ("base_2.txt", "Documento de Cadastro - Análise de Disfunções"),
        ("base_conhecimento.txt", "Manual de Procedimentos Operacionais")
    ]
    
    for filename, description in documents:
        filepath = Path(filename)
        if filepath.exists():
            print(f"\n📄 Processing {filename} - {description}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    await rag.ainsert(content)
                print(f"✅ {filename} processed successfully!")
            except Exception as e:
                print(f"❌ Error processing {filename}: {str(e)}")
        else:
            print(f"❌ Warning: {filename} not found!")

async def query_rag(rag, question, mode="hybrid"):
    """Query the RAG system."""
    print(f"\n🔍 Querying in {mode} mode...")
    try:
        result = await rag.aquery(
            question,
            param=QueryParam(mode=mode)
        )
        return result
    except Exception as e:
        return f"Error during query: {str(e)}"

def visualize_knowledge_graph():
    """Create an interactive visualization of the knowledge graph."""
    print("\n📊 Creating knowledge graph visualization...")
    
    graphml_path = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
    
    if not graphml_path.exists():
        print("❌ Graph file not found. Please insert documents first.")
        return None
    
    try:
        # Load the graph
        G = nx.read_graphml(str(graphml_path))
        
        # Create PyVis network
        net = Network(
            height="800px",
            width="100%",
            bgcolor="#f7f7f7",
            font_color="black",
            notebook=False,
            select_menu=True,
            filter_menu=True
        )
        
        # Configure physics
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -80000,
              "centralGravity": 0.3,
              "springLength": 250,
              "springConstant": 0.04,
              "damping": 0.09,
              "avoidOverlap": 0.1
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "barnesHut"
          },
          "nodes": {
            "font": {
              "size": 16,
              "face": "Arial"
            },
            "borderWidth": 2,
            "borderWidthSelected": 4
          },
          "edges": {
            "font": {
              "size": 12,
              "align": "middle"
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 1
              }
            },
            "smooth": {
              "type": "continuous"
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": true
          }
        }
        """)
        
        # Add nodes with different colors based on type
        node_colors = {
            'entity': '#ff9999',
            'chunk': '#99ccff',
            'relation': '#99ff99',
            'document': '#ffcc99'
        }
        
        for node_id, node_data in G.nodes(data=True):
            node_type = node_data.get('node_type', 'entity')
            color = node_colors.get(node_type, '#cccccc')
            
            net.add_node(
                node_id,
                label=node_id[:50] + "..." if len(node_id) > 50 else node_id,
                color=color,
                title=f"ID: {node_id}\nType: {node_type}",
                size=25
            )
        
        # Add edges
        for source, target, edge_data in G.edges(data=True):
            weight = edge_data.get('weight', 1)
            net.add_edge(source, target, value=weight)
        
        # Save the visualization
        output_path = "knowledge_graph.html"
        net.save_graph(output_path)
        print(f"✅ Graph visualization saved to {output_path}")
        
        return output_path
    except Exception as e:
        print(f"❌ Error creating visualization: {str(e)}")
        return None

async def interactive_query_session(rag):
    """Run an interactive query session."""
    print("\n🤖 LightRAG Agent Ready!")
    print("=" * 60)
    print("Available query modes:")
    print("  - naive: Basic RAG without knowledge graph")
    print("  - local: Uses local graph context around entities")
    print("  - global: Uses high-level community summaries")
    print("  - hybrid: Combines local and global approaches (recommended)")
    print("\nCommands:")
    print("  - 'mode <mode>': Change query mode (e.g., 'mode local')")
    print("  - 'graph': Visualize the knowledge graph")
    print("  - 'exit' or 'quit': Exit the session")
    print("=" * 60)
    
    current_mode = "hybrid"
    
    while True:
        try:
            question = input(f"\n💬 [{current_mode}] Your question: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
                
            if question.lower() == 'graph':
                graph_path = visualize_knowledge_graph()
                if graph_path:
                    print(f"Opening {graph_path} in browser...")
                    webbrowser.open(f"file://{os.path.abspath(graph_path)}")
                continue
                
            if question.lower().startswith('mode '):
                new_mode = question.split()[1]
                if new_mode in ['naive', 'local', 'global', 'hybrid']:
                    current_mode = new_mode
                    print(f"✅ Switched to {current_mode} mode")
                else:
                    print(f"❌ Invalid mode. Choose from: naive, local, global, hybrid")
                continue
            
            # Query the RAG
            answer = await query_rag(rag, question, current_mode)
            
            print(f"\n📝 Answer:\n{'-' * 60}")
            print(answer)
            print('-' * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

async def main():
    """Main function."""
    print("🚀 Starting LightRAG Agent...")
    
    rag = None
    try:
        # Initialize RAG instance
        rag = await initialize_rag()
        
        # Check if we need to insert documents
        graph_file = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
        if not graph_file.exists():
            await insert_documents(rag)
        else:
            print("\n✅ Using existing knowledge base")
        
        # Start interactive session
        await interactive_query_session(rag)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
    finally:
        if rag:
            await rag.finalize_storages()

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run the async main function
    asyncio.run(main())