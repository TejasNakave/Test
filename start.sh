#!/bin/bash

# Render startup script for Trade Assistant RAG Chatbot

echo "🚀 Starting Trade Assistant RAG Chatbot on Render..."

# Create necessary directories if they don't exist
mkdir -p chroma_db
mkdir -p data
mkdir -p extracted_images

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH

# Start the application
python rag_server.py