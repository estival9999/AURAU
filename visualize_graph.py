#!/usr/bin/env python3
import os
import networkx as nx
from pyvis.network import Network
import webbrowser
from pathlib import Path

def visualize_knowledge_graph():
    """Create an interactive visualization of the knowledge graph."""
    WORKING_DIR = "./lightrag_workdir"
    graphml_path = Path(WORKING_DIR) / "graph_chunk_entity_relation.graphml"
    
    if not graphml_path.exists():
        print("❌ Graph file not found at:", graphml_path)
        print("Please run the LightRAG system first to generate the knowledge graph.")
        return None
    
    print("📊 Loading knowledge graph...")
    
    try:
        # Load the graph
        G = nx.read_graphml(str(graphml_path))
        print(f"✅ Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Create PyVis network
        net = Network(
            height="800px",
            width="100%",
            bgcolor="#222222",
            font_color="white",
            notebook=False,
            select_menu=True,
            filter_menu=True,
            neighborhood_highlight=True,
            directed=True
        )
        
        # Configure physics
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -50000,
              "centralGravity": 0.3,
              "springLength": 200,
              "springConstant": 0.04,
              "damping": 0.09,
              "avoidOverlap": 0.5
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "barnesHut",
            "stabilization": {
              "enabled": true,
              "iterations": 1000,
              "updateInterval": 100
            }
          },
          "nodes": {
            "font": {
              "size": 14,
              "face": "Arial",
              "color": "white"
            },
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "shape": "dot"
          },
          "edges": {
            "font": {
              "size": 10,
              "align": "middle",
              "color": "white"
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.5
              }
            },
            "smooth": {
              "type": "continuous"
            },
            "color": {
              "color": "#848484",
              "highlight": "#ffffff"
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "hideEdgesOnDrag": true,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)
        
        # Define node colors based on type
        node_colors = {
            'entity': '#ff6b6b',      # Red
            'chunk': '#4ecdc4',       # Teal
            'relation': '#45b7d1',    # Blue
            'document': '#f7dc6f',    # Yellow
            'concept': '#bb8fce',     # Purple
            'default': '#95a5a6'      # Gray
        }
        
        # Add nodes with enhanced styling
        for node_id, node_data in G.nodes(data=True):
            node_type = node_data.get('node_type', 'default')
            color = node_colors.get(node_type, node_colors['default'])
            
            # Create title with all node attributes
            title_parts = [f"<b>{node_id}</b>"]
            title_parts.append(f"Type: {node_type}")
            
            for key, value in node_data.items():
                if key != 'node_type' and value:
                    title_parts.append(f"{key}: {value}")
            
            title = "<br>".join(title_parts)
            
            # Determine node size based on connections
            node_size = 20 + (G.degree(node_id) * 3)
            node_size = min(node_size, 50)  # Cap the maximum size
            
            net.add_node(
                node_id,
                label=node_id[:30] + "..." if len(node_id) > 30 else node_id,
                color=color,
                title=title,
                size=node_size,
                borderWidth=2,
                borderWidthSelected=4
            )
        
        # Add edges with labels
        for source, target, edge_data in G.edges(data=True):
            weight = edge_data.get('weight', 1)
            edge_type = edge_data.get('edge_type', '')
            
            edge_title = f"Weight: {weight}"
            if edge_type:
                edge_title += f"<br>Type: {edge_type}"
            
            net.add_edge(
                source, 
                target, 
                value=weight,
                title=edge_title,
                width=weight * 2 if weight < 5 else 10
            )
        
        # Add legend
        legend_html = """
        <div style='position: fixed; top: 10px; right: 10px; background-color: rgba(0,0,0,0.8); 
                    padding: 10px; border-radius: 5px; color: white; font-family: Arial;'>
            <h4 style='margin: 0 0 10px 0;'>Legend</h4>
            <div style='display: flex; align-items: center; margin: 5px 0;'>
                <div style='width: 20px; height: 20px; background-color: #ff6b6b; 
                            border-radius: 50%; margin-right: 10px;'></div>
                <span>Entity</span>
            </div>
            <div style='display: flex; align-items: center; margin: 5px 0;'>
                <div style='width: 20px; height: 20px; background-color: #4ecdc4; 
                            border-radius: 50%; margin-right: 10px;'></div>
                <span>Chunk</span>
            </div>
            <div style='display: flex; align-items: center; margin: 5px 0;'>
                <div style='width: 20px; height: 20px; background-color: #45b7d1; 
                            border-radius: 50%; margin-right: 10px;'></div>
                <span>Relation</span>
            </div>
            <div style='display: flex; align-items: center; margin: 5px 0;'>
                <div style='width: 20px; height: 20px; background-color: #f7dc6f; 
                            border-radius: 50%; margin-right: 10px;'></div>
                <span>Document</span>
            </div>
        </div>
        """
        
        # Save the visualization
        output_path = "knowledge_graph_interactive.html"
        net.save_graph(output_path)
        
        # Add legend to the saved file
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Insert legend before closing body tag
        html_content = html_content.replace('</body>', legend_html + '</body>')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Interactive graph saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating visualization: {str(e)}")
        return None

if __name__ == "__main__":
    graph_path = visualize_knowledge_graph()
    if graph_path:
        print(f"\n🌐 Opening graph in browser...")
        webbrowser.open(f"file://{os.path.abspath(graph_path)}")