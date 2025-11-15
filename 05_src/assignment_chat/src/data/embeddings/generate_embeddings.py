#!/usr/bin/env python3
"""
Generate embeddings for YouTube history videos and store in ChromaDB.

This script:
1. Fetches videos from YouTube History API
2. Generates embeddings using OpenAI API
3. Stores embeddings in ChromaDB with metadata
4. Includes transcripts in embeddings when available
"""

import os
import sys
import argparse
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add parent directories to path for logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
from utils.logger import get_logger

# Add src directory to path for API client
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import API client
from src.utils.api_client import YouTubeHistoryAPIClient

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


def prepare_text_for_embedding(video: Dict, transcript: Optional[str] = None) -> str:
    """
    Prepare text for embedding by combining title, description, channel name, and transcript.
    
    Args:
        video: Video dictionary with title, description, channel_name
        transcript: Optional transcript text
        
    Returns:
        Combined text string for embedding
    """
    parts = []
    
    # Add title
    if video.get('title'):
        parts.append(f"Title: {video['title']}")
    
    # Add channel name as context
    if video.get('channel_name'):
        parts.append(f"Channel: {video['channel_name']}")
    
    # Add description if available
    if video.get('description'):
        parts.append(f"Description: {video['description']}")
    
    # Add transcript if available
    if transcript:
        parts.append(f"Transcript: {transcript}")
    
    return "\n\n".join(parts)


def estimate_data_size(num_videos: int, avg_text_length: int = 1000) -> float:
    """
    Estimate total data size in MB.
    
    Args:
        num_videos: Number of videos
        avg_text_length: Average text length per video
        
    Returns:
        Estimated size in MB
    """
    # Embedding: 1536 dimensions × 4 bytes = 6144 bytes per video
    # Metadata: ~500 bytes per video (rough estimate)
    # Text: avg_text_length bytes per video
    embedding_size = num_videos * 6144
    metadata_size = num_videos * 500
    text_size = num_videos * avg_text_length
    
    total_bytes = embedding_size + metadata_size + text_size
    total_mb = total_bytes / (1024 * 1024)
    
    return total_mb


def main():
    """Main function to generate embeddings and store in ChromaDB."""
    parser = argparse.ArgumentParser(
        description='Generate embeddings for YouTube history videos'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for embedding generation (default: 100)'
    )
    parser.add_argument(
        '--include-transcripts',
        action='store_true',
        help='Include video transcripts in embeddings (slower, requires API calls)'
    )
    parser.add_argument(
        '--max-videos',
        type=int,
        default=None,
        help='Maximum number of videos to process (default: all)'
    )
    parser.add_argument(
        '--limit-per-page',
        type=int,
        default=500,
        help='Number of videos per API page (default: 500)'
    )
    parser.add_argument(
        '--chroma-db-path',
        type=str,
        default=None,
        help='Path to ChromaDB storage (default: from .env)'
    )
    parser.add_argument(
        '--collection-name',
        type=str,
        default=None,
        help='ChromaDB collection name (default: from .env)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        sys.exit(1)
    
    embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    chroma_db_path = args.chroma_db_path or os.getenv('CHROMA_DB_PATH', './src/data/chroma_db')
    collection_name = args.collection_name or os.getenv('CHROMA_COLLECTION_NAME', 'youtube_history')
    
    print("Starting embedding generation...")
    
    # Initialize clients
    api_client = YouTubeHistoryAPIClient()
    
    # Fetch videos
    try:
        videos = api_client.get_all_videos_paginated(
            limit=args.limit_per_page,
            max_videos=args.max_videos
        )
        print(f"✓ Fetched {len(videos)} videos")
    except Exception as e:
        logger.error(f"Failed to fetch videos: {e}")
        sys.exit(1)
    
    if not videos:
        logger.warning("No videos found")
        sys.exit(0)
    
    # Estimate data size
    estimated_size = estimate_data_size(len(videos))
    if estimated_size > 40:
        logger.warning(f"Estimated size ({estimated_size:.2f} MB) exceeds 40MB limit!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted by user")
            sys.exit(0)
    
    # Fetch transcripts if requested
    transcripts = {}
    if args.include_transcripts:
        for video in tqdm(videos, desc="Fetching transcripts", unit="video"):
            video_id = video['video_id']
            try:
                transcript_data = api_client.get_video_transcript(video_id)
                if transcript_data:
                    transcripts[video_id] = transcript_data.get('transcript_text', '')
            except Exception as e:
                logger.warning(f"Failed to fetch transcript for {video_id}: {e}")
                transcripts[video_id] = None
        
        transcript_count = sum(1 for t in transcripts.values() if t)
        print(f"✓ Fetched {transcript_count} transcripts")
    
    # Deduplicate videos (keep most recent watch)
    print("Deduplicating videos...")
    seen_videos = {}
    for video in videos:
        video_id = video['video_id']
        watched_at = video.get('watched_at', '')
        if video_id not in seen_videos or watched_at > seen_videos[video_id].get('watched_at', ''):
            seen_videos[video_id] = video
    
    unique_videos = list(seen_videos.values())
    print(f"✓ Deduplicated: {len(videos)} -> {len(unique_videos)} unique videos")
    
    # Initialize text splitter (following lab guidance)
    # Using 7000 characters ≈ 1750 tokens (safe under 8192 token limit)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=7000,  # Characters (≈1750 tokens, safe under 8192 limit)
        chunk_overlap=200,  # Characters overlap for context
        length_function=len,
        add_start_index=True
    )
    
    # Prepare texts for embedding with chunking
    print("Preparing texts for embedding...")
    video_texts = []
    video_metadata = []
    video_ids = []
    
    for video in unique_videos:
        video_id = video['video_id']
        transcript = transcripts.get(video_id) if args.include_transcripts else None
        text = prepare_text_for_embedding(video, transcript)
        
        # Split into chunks using LangChain's text splitter
        chunks = text_splitter.create_documents([text])
        
        for chunk_idx, chunk_doc in enumerate(chunks):
            # Create unique ID for each chunk
            chunk_id = f"{video_id}_chunk_{chunk_idx}" if len(chunks) > 1 else video_id
            
            video_texts.append(chunk_doc.page_content)
            video_ids.append(chunk_id)
            video_metadata.append({
                'video_id': video_id,
                'chunk_index': str(chunk_idx),
                'total_chunks': str(len(chunks)),
                'start_index': str(chunk_doc.metadata.get('start_index', 0)),
                'channel_id': video.get('channel_id', ''),
                'channel_name': video.get('channel_name', ''),
                'watched_at': video.get('watched_at', ''),
                'title': video.get('title', ''),
                'has_transcript': str(transcript is not None).lower()
            })
    
    print(f"✓ Prepared {len(video_texts)} chunks from {len(unique_videos)} videos")
    
    # Initialize ChromaDB
    print("Initializing ChromaDB...")
    try:
        chroma_client = PersistentClient(path=chroma_db_path)
        
        # Delete existing collection if it exists (to ensure correct embedding function)
        # Following lab pattern: delete and recreate to ensure correct embedding dimensions
        try:
            chroma_client.delete_collection(name=collection_name)
            print(f"✓ Deleted existing collection '{collection_name}'")
        except Exception:
            # Collection doesn't exist, which is fine
            pass
        
        # Create collection with OpenAI embedding function
        collection = chroma_client.create_collection(
            name=collection_name,
            embedding_function=OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name=embedding_model
            )
        )
        print(f"✓ Created collection '{collection_name}' with {embedding_model}")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        sys.exit(1)
    
    # Generate embeddings in batches and add to ChromaDB
    print("Generating embeddings...")
    
    # Create progress bar for batches
    pbar = tqdm(total=len(video_texts), desc="Generating embeddings", unit="chunk")
    
    for i in range(0, len(video_texts), args.batch_size):
        batch_texts = video_texts[i:i + args.batch_size]
        batch_ids = video_ids[i:i + args.batch_size]
        batch_metadata = video_metadata[i:i + args.batch_size]
        
        batch_num = (i // args.batch_size) + 1
        
        try:
            # Use upsert to handle duplicates gracefully (embeddings generated automatically by OpenAIEmbeddingFunction)
            collection.upsert(
                documents=batch_texts,
                ids=batch_ids,
                metadatas=batch_metadata
            )
            
            # Update progress bar
            pbar.update(len(batch_texts))
            
            # Small delay to avoid rate limiting
            if i + args.batch_size < len(video_texts):
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Failed to process batch {batch_num}: {e}")
            logger.error("Continuing with next batch...")
            # Still update progress bar even on error
            pbar.update(len(batch_texts))
            continue
    
    pbar.close()
    print(f"✓ Complete! Processed {len(video_texts)} chunks from {len(unique_videos)} videos")
    print(f"  Collection: {collection_name}")
    print(f"  ChromaDB path: {chroma_db_path}")


if __name__ == '__main__':
    main()

