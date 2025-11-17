"""Semantic Service for YouTube History with ChromaDB vector search"""

import os
import sys
import time
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import logger
# From src/services/semantic_service.py, go up to 05_src level (services -> src -> assignment_chat -> 05_src)
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '../../..'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)
from utils.logger import get_logger

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from chromadb import PersistentClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain.tools import tool

load_dotenv()
load_dotenv('.secrets')

logger = get_logger(__name__)


class SemanticService:
    """Service for semantic search over YouTube history using ChromaDB"""
    
    def __init__(self, chroma_db_path: Optional[str] = None, collection_name: Optional[str] = None):
        """
        Initialize the semantic service.
        
        Args:
            chroma_db_path: Path to ChromaDB storage (default: from env)
            collection_name: ChromaDB collection name (default: from env)
        """
        self.chroma_db_path = chroma_db_path or os.getenv('CHROMA_DB_PATH', './src/data/chroma_db')
        self.collection_name = collection_name or os.getenv('CHROMA_COLLECTION_NAME', 'youtube_history')
        
        try:
            # Initialize ChromaDB client
            self.client = PersistentClient(path=self.chroma_db_path)
            
            # Get existing collection (assumes it was created with OpenAIEmbeddingFunction)
            self.collection = self.client.get_collection(name=self.collection_name)
            
            logger.info(f"Initialized SemanticService with collection '{self.collection_name}' at '{self.chroma_db_path}'")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def search_by_topic(
        self, 
        query: str, 
        n_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform semantic search by topic.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filters: Optional metadata filters (channel_id, date_from, date_to)
            
        Returns:
            List of result dictionaries with video information
        """
        start_time = time.time()
        logger.info(f"Semantic search: query='{query}', n_results={n_results}, filters={filters}")
        
        try:
            # Build where clause for ChromaDB metadata filters
            where_clause = self._build_where_clause(filters)
            
            # Query ChromaDB (embedding function handles query embedding automatically)
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2 if filters else n_results,  # Get more if we need to filter
                where=where_clause
            )
            
            # Process results
            processed_results = self._process_chromadb_results(results)
            
            # Apply post-query filters (e.g., date ranges)
            if filters:
                processed_results = self._apply_post_filters(processed_results, filters)
                processed_results = processed_results[:n_results]
            
            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"Semantic search completed: {len(processed_results)} results in {latency_ms:.2f}ms")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise
    
    def hybrid_search(
        self,
        query: str,
        n_results: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        channel_id: Optional[str] = None,
        channel_name: Optional[str] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[Dict]:
        """
        Perform hybrid semantic + metadata search.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            date_from: Start date filter (YYYY-MM-DD format)
            date_to: End date filter (YYYY-MM-DD format)
            channel_id: Filter by channel ID
            channel_name: Filter by channel name
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            
        Returns:
            List of result dictionaries with video information
        """
        filters = {}
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        if channel_id:
            filters['channel_id'] = channel_id
        if channel_name:
            filters['channel_name'] = channel_name
        if min_duration:
            filters['min_duration'] = min_duration
        if max_duration:
            filters['max_duration'] = max_duration
        
        return self.search_by_topic(query, n_results, filters)
    
    def find_similar_videos(self, video_id: str, n_results: int = 5) -> List[Dict]:
        """
        Find videos similar to a given video.
        
        Args:
            video_id: YouTube video ID to find similar videos for
            n_results: Number of similar videos to return
            
        Returns:
            List of similar video dictionaries
        """
        start_time = time.time()
        logger.info(f"Finding similar videos to video_id='{video_id}', n_results={n_results}")
        
        try:
            # Get the video's embedding/document from ChromaDB
            video_data = self.collection.get(ids=[video_id])
            
            if not video_data['ids'] or len(video_data['ids']) == 0:
                logger.warning(f"Video {video_id} not found in ChromaDB")
                return []
            
            # Get the document text for the video
            if video_data['documents'] and len(video_data['documents']) > 0:
                query_text = video_data['documents'][0]
            else:
                logger.warning(f"Video {video_id} has no document text")
                return []
            
            # Search for similar videos (excluding the original video)
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results + 1,  # Get one extra to exclude the original
                where={"video_id": {"$ne": video_id}}  # Exclude the original video
            )
            
            # Process results
            processed_results = self._process_chromadb_results(results)
            
            # Remove the original video if it somehow appears
            processed_results = [r for r in processed_results if r.get('video_id') != video_id]
            
            # Limit to n_results
            processed_results = processed_results[:n_results]
            
            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"Found {len(processed_results)} similar videos in {latency_ms:.2f}ms")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error finding similar videos: {e}")
            raise
    
    def format_results(self, results: List[Dict]) -> str:
        """
        Format search results as natural language string.
        
        Args:
            results: List of result dictionaries from search
            
        Returns:
            Natural language formatted string
        """
        if not results:
            return "I couldn't find any videos matching your search."
        
        formatted_parts = [f"I found {len(results)} video{'s' if len(results) != 1 else ''} that match your search:\n"]
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Unknown Video')
            channel = result.get('channel_name', 'Unknown Channel')
            video_id = result.get('video_id', '')
            watched_at = result.get('watched_at', '')
            distance = result.get('distance', None)
            
            # Format watched time
            time_str = ""
            if watched_at:
                try:
                    watched_dt = datetime.fromisoformat(watched_at.replace('Z', '+00:00'))
                    now = datetime.now(watched_dt.tzinfo)
                    diff = now - watched_dt
                    
                    if diff.days == 0:
                        hours = diff.seconds // 3600
                        if hours == 0:
                            minutes = diff.seconds // 60
                            time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                        else:
                            time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
                    elif diff.days == 1:
                        time_str = "yesterday"
                    elif diff.days < 7:
                        time_str = f"{diff.days} days ago"
                    elif diff.days < 30:
                        weeks = diff.days // 7
                        time_str = f"{weeks} week{'s' if weeks != 1 else ''} ago"
                    else:
                        months = diff.days // 30
                        time_str = f"{months} month{'s' if months != 1 else ''} ago"
                except Exception:
                    time_str = ""
            
            # Build result line
            result_line = f"{i}. {title}"
            if channel:
                result_line += f" from {channel}"
            if time_str:
                result_line += f" (watched {time_str})"
            if distance is not None:
                similarity = 1 - distance
                result_line += f" [relevance: {similarity:.2f}]"
            
            formatted_parts.append(result_line)
        
        return "\n".join(formatted_parts)
    
    def _build_where_clause(self, filters: Optional[Dict]) -> Optional[Dict]:
        """
        Build ChromaDB where clause from filters.
        
        Args:
            filters: Filter dictionary
            
        Returns:
            ChromaDB where clause or None
        """
        if not filters:
            return None
        
        where_clause = {}
        
        # Channel ID filter
        if filters.get('channel_id'):
            where_clause['channel_id'] = {"$eq": filters['channel_id']}
        
        # Channel name filter
        if filters.get('channel_name'):
            where_clause['channel_name'] = {"$eq": filters['channel_name']}
        
        # Return None if empty, otherwise return the clause
        return where_clause if where_clause else None
    
    def _process_chromadb_results(self, results: Dict) -> List[Dict]:
        """
        Process ChromaDB query results into a list of dictionaries.
        
        Args:
            results: ChromaDB query results dictionary
            
        Returns:
            List of processed result dictionaries
        """
        processed = []
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return processed
        
        ids = results['ids'][0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        documents = results.get('documents', [[]])[0]
        
        for i, video_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            
            result_dict = {
                'video_id': video_id,
                'title': metadata.get('title', 'Unknown'),
                'channel_id': metadata.get('channel_id', ''),
                'channel_name': metadata.get('channel_name', 'Unknown Channel'),
                'watched_at': metadata.get('watched_at', ''),
                'distance': distance,
                'metadata': metadata
            }
            
            processed.append(result_dict)
        
        return processed
    
    def _apply_post_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply post-query filters (e.g., date ranges, duration).
        
        Args:
            results: List of result dictionaries
            filters: Filter dictionary
            
        Returns:
            Filtered list of results
        """
        filtered = results
        
        # Date range filtering
        if filters.get('date_from') or filters.get('date_to'):
            filtered = self._filter_by_date_range(filtered, filters.get('date_from'), filters.get('date_to'))
        
        # Duration filtering
        if filters.get('min_duration') or filters.get('max_duration'):
            filtered = self._filter_by_duration(filtered, filters.get('min_duration'), filters.get('max_duration'))
        
        return filtered
    
    def _filter_by_date_range(self, results: List[Dict], date_from: Optional[str], date_to: Optional[str]) -> List[Dict]:
        """
        Filter results by date range.
        
        Args:
            results: List of result dictionaries
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            Filtered results
        """
        filtered = []
        
        for result in results:
            watched_at = result.get('watched_at', '')
            if not watched_at:
                continue
            
            try:
                watched_dt = datetime.fromisoformat(watched_at.replace('Z', '+00:00'))
                watched_date = watched_dt.date()
                
                if date_from:
                    from_date = datetime.fromisoformat(date_from).date()
                    if watched_date < from_date:
                        continue
                
                if date_to:
                    to_date = datetime.fromisoformat(date_to).date()
                    if watched_date > to_date:
                        continue
                
                filtered.append(result)
            except Exception as e:
                logger.warning(f"Error parsing date '{watched_at}': {e}")
                continue
        
        return filtered
    
    def _filter_by_duration(self, results: List[Dict], min_duration: Optional[int], max_duration: Optional[int]) -> List[Dict]:
        """
        Filter results by duration.
        
        Args:
            results: List of result dictionaries
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            
        Returns:
            Filtered results
        """
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            duration_seconds = metadata.get('duration_seconds')
            
            if duration_seconds is None:
                # If duration not in metadata, skip filtering for this result
                filtered.append(result)
                continue
            
            if min_duration and duration_seconds < min_duration:
                continue
            
            if max_duration and duration_seconds > max_duration:
                continue
            
            filtered.append(result)
        
        return filtered


# Initialize service instance for tools
_semantic_service: Optional[SemanticService] = None


def get_semantic_service() -> SemanticService:
    """Get or create global semantic service instance"""
    global _semantic_service
    if _semantic_service is None:
        _semantic_service = SemanticService()
    return _semantic_service


@tool
def search_videos_by_topic(
    query: str,
    n_results: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    channel_id: Optional[str] = None,
    channel_name: Optional[str] = None
) -> str:
    """
    Search for videos by topic, subject, or theme using semantic search. Use this when the user asks about videos on a specific topic, wants to find videos about something, or asks 'what videos did I watch about X'. This finds videos by meaning, not just keywords.
    
    Args:
        query: The topic or subject to search for (e.g., 'machine learning', 'Python tutorials', 'cooking recipes')
        n_results: Number of results to return (default: 10)
        date_from: Optional: Filter by start date (YYYY-MM-DD format)
        date_to: Optional: Filter by end date (YYYY-MM-DD format)
        channel_id: Optional: Filter by channel ID
        channel_name: Optional: Filter by channel name
    """
    try:
        service = get_semantic_service()
        results = service.hybrid_search(
            query=query,
            n_results=n_results,
            date_from=date_from,
            date_to=date_to,
            channel_id=channel_id,
            channel_name=channel_name
        )
        return service.format_results(results)
    except Exception as e:
        logger.error(f"Error in search_videos_by_topic: {e}")
        return f"I encountered an issue searching for videos. Please try again later."


@tool
def find_similar_videos(video_id: str, n_results: int = 5) -> str:
    """
    Find videos similar to a specific video. Use this when the user asks for videos similar to one they mention, or wants recommendations based on a video they watched.
    
    Args:
        video_id: YouTube video ID to find similar videos for
        n_results: Number of similar videos to return (default: 5)
    """
    try:
        service = get_semantic_service()
        results = service.find_similar_videos(video_id=video_id, n_results=n_results)
        return service.format_results(results)
    except Exception as e:
        logger.error(f"Error in find_similar_videos: {e}")
        return f"I encountered an issue finding similar videos. Please try again later."


def get_semantic_tools():
    """Get list of semantic tools for LangChain"""
    return [
        search_videos_by_topic,
        find_similar_videos
    ]

