#!/bin/bash

# Activate virtual environment
source lightrag_env/bin/activate

# Change to API directory
cd LightRAG/lightrag/api

# Start the API server
echo "🚀 Starting LightRAG API Server..."
echo "📊 Web interface will be available at: http://localhost:8000"
echo "📈 Graph visualization at: http://localhost:8000/graph"
echo ""

python lightrag_server.py