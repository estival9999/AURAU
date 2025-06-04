"""
Supabase Database Handler for AURALIS System
Manages all database operations including authentication, meetings, and AI interactions
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
import logging

# For development/testing without actual Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

@dataclass
class CachedQuery:
    """Cached query result with timestamp"""
    data: Any
    timestamp: datetime
    ttl_minutes: int = 60
    
    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        age = datetime.now() - self.timestamp
        return age < timedelta(minutes=self.ttl_minutes)


class SupabaseHandler:
    """
    Handles all database operations for the AURALIS system.
    Includes caching, error handling, and mock mode for testing.
    """
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize Supabase handler.
        
        Args:
            mock_mode: Use mock data instead of real database
        """
        self.mock_mode = mock_mode or not SUPABASE_AVAILABLE
        self.cache: Dict[str, CachedQuery] = {}
        self.logger = logging.getLogger(__name__)
        
        if not self.mock_mode:
            try:
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_ANON_KEY")
                
                if not url or not key:
                    self.logger.warning("Supabase credentials not found, using mock mode")
                    self.mock_mode = True
                else:
                    self.client: Client = create_client(url, key)
                    self.logger.info("Supabase client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Supabase: {e}")
                self.mock_mode = True
        
        if self.mock_mode:
            self.logger.info("Running in mock mode")
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock data for testing"""
        self.mock_users = [
            {
                "id": "mock-user-1",
                "username": "admin",
                "full_name": "Administrador",
                "email": "admin@auralis.com",
                "area": "geral",
                "role": "admin",
                "preferences": {"theme": "dark", "language": "pt-BR"}
            },
            {
                "id": "mock-user-2",
                "username": "teste",
                "full_name": "Usuário Teste",
                "email": "teste@auralis.com",
                "area": "desenvolvimento",
                "role": "user",
                "preferences": {"theme": "dark", "language": "pt-BR"}
            }
        ]
        
        self.mock_meetings = [
            {
                "id": "meet-1",
                "title": "Planejamento Q1 2024",
                "scheduled_start": "2024-01-15T14:00:00",
                "scheduled_end": "2024-01-15T15:30:00",
                "duration_seconds": 5400,
                "organizer_id": "mock-user-1",
                "status": "completed",
                "meeting_participants": [
                    {"user_id": "mock-user-1", "role": "host"},
                    {"user_id": "mock-user-2", "role": "participant"}
                ]
            },
            {
                "id": "meet-2",
                "title": "Daily Standup",
                "scheduled_start": "2024-01-14T10:00:00",
                "scheduled_end": "2024-01-14T10:15:00",
                "duration_seconds": 900,
                "organizer_id": "mock-user-1",
                "status": "completed"
            },
            {
                "id": "meet-3",
                "title": "Revisão Sprint AURALIS",
                "scheduled_start": "2024-01-12T15:30:00",
                "scheduled_end": "2024-01-12T17:00:00",
                "duration_seconds": 5400,
                "organizer_id": "mock-user-2",
                "status": "completed"
            }
        ]
        
        self.mock_agents = [
            {
                "id": "agent-1",
                "name": "Orquestrador AURALIS",
                "type": "orchestrator",
                "model": "gpt-4",
                "is_active": True
            },
            {
                "id": "agent-2",
                "name": "Consultor Inteligente AURALIS",
                "type": "query",
                "model": "gpt-3.5-turbo",
                "is_active": True
            },
            {
                "id": "agent-3",
                "name": "Agente Criativo AURALIS",
                "type": "brainstorm",
                "model": "gpt-4",
                "is_active": True
            }
        ]
    
    # ==================== Authentication ====================
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user and return profile.
        
        Args:
            username: Username
            password: Password (ignored in mock mode)
            
        Returns:
            User profile dict or None if authentication fails
        """
        if self.mock_mode:
            # Mock authentication - accept any password
            for user in self.mock_users:
                if user["username"] == username:
                    self.logger.info(f"Mock authentication successful for {username}")
                    return user
            return None
        
        try:
            # Real Supabase authentication would go here
            # For now, we'll do a simple username lookup
            response = self.client.table('users')\
                .select('*')\
                .eq('username', username)\
                .single()\
                .execute()
            
            if response.data:
                return response.data
            return None
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None
    
    # ==================== Meeting Management ====================
    
    def get_user_meetings(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent meetings for user.
        
        Args:
            user_id: User ID
            limit: Maximum number of meetings to return
            
        Returns:
            List of meeting dictionaries
        """
        cache_key = f"user_meetings_{user_id}_{limit}"
        
        # Check cache
        if cache_key in self.cache and self.cache[cache_key].is_valid():
            return self.cache[cache_key].data
        
        if self.mock_mode:
            # Return mock meetings for the user
            user_meetings = [m for m in self.mock_meetings 
                           if m["organizer_id"] == user_id][:limit]
            
            # Cache result
            self.cache[cache_key] = CachedQuery(user_meetings, datetime.now())
            return user_meetings
        
        try:
            response = self.client.table('meetings')\
                .select('*, meeting_participants(*)')\
                .or_(f'organizer_id.eq.{user_id},meeting_participants.user_id.eq.{user_id}')\
                .order('scheduled_start', desc=True)\
                .limit(limit)\
                .execute()
            
            meetings = response.data
            
            # Cache result
            self.cache[cache_key] = CachedQuery(meetings, datetime.now())
            return meetings
            
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {e}")
            return []
    
    def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict]:
        """Get meeting details by ID"""
        if self.mock_mode:
            for meeting in self.mock_meetings:
                if meeting["id"] == meeting_id:
                    return meeting
            return None
        
        try:
            response = self.client.table('meetings')\
                .select('*, meeting_participants(*)')\
                .eq('id', meeting_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error fetching meeting {meeting_id}: {e}")
            return None
    
    def search_meetings_by_title(self, title_query: str, user_id: str) -> List[Dict]:
        """Search meetings by title"""
        if self.mock_mode:
            results = []
            for meeting in self.mock_meetings:
                if title_query.lower() in meeting["title"].lower():
                    results.append(meeting)
            return results
        
        try:
            response = self.client.table('meetings')\
                .select('*')\
                .ilike('title', f'%{title_query}%')\
                .or_(f'organizer_id.eq.{user_id},meeting_participants.user_id.eq.{user_id}')\
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error searching meetings: {e}")
            return []
    
    def save_meeting(self, meeting_data: Dict) -> Optional[str]:
        """
        Save a new meeting to database.
        
        Args:
            meeting_data: Meeting information
            
        Returns:
            Meeting ID if successful, None otherwise
        """
        if self.mock_mode:
            # Generate mock meeting ID
            meeting_id = f"meet-{len(self.mock_meetings) + 1}"
            meeting = {
                "id": meeting_id,
                **meeting_data,
                "created_at": datetime.now().isoformat()
            }
            self.mock_meetings.append(meeting)
            return meeting_id
        
        try:
            response = self.client.table('meetings')\
                .insert(meeting_data)\
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            self.logger.error(f"Error saving meeting: {e}")
            return None
    
    # ==================== Transcription Management ====================
    
    def get_meeting_transcription(self, meeting_id: str) -> Optional[Dict]:
        """
        Get meeting transcription with segments.
        
        Args:
            meeting_id: Meeting ID
            
        Returns:
            Transcription data or None
        """
        if self.mock_mode:
            # Return mock transcription
            return {
                "id": f"trans-{meeting_id}",
                "meeting_id": meeting_id,
                "full_text": "Esta é uma transcrição simulada da reunião...",
                "duration_seconds": 3600,
                "transcription_segments": [
                    {
                        "speaker_name": "João",
                        "text": "Vamos começar a reunião de planejamento.",
                        "start_time": 0,
                        "end_time": 5
                    },
                    {
                        "speaker_name": "Maria",
                        "text": "Ótimo, temos muitos pontos para discutir hoje.",
                        "start_time": 5,
                        "end_time": 10
                    }
                ]
            }
        
        try:
            response = self.client.table('meeting_transcriptions')\
                .select('*, transcription_segments(*)')\
                .eq('meeting_id', meeting_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error fetching transcription: {e}")
            return None
    
    def save_transcription(self, meeting_id: str, transcription_data: Dict) -> bool:
        """Save meeting transcription"""
        if self.mock_mode:
            self.logger.info(f"Mock: Saved transcription for meeting {meeting_id}")
            return True
        
        try:
            # Save main transcription
            trans_response = self.client.table('meeting_transcriptions')\
                .insert({
                    "meeting_id": meeting_id,
                    "full_text": transcription_data.get("full_text", ""),
                    "duration_seconds": transcription_data.get("duration_seconds", 0)
                })\
                .execute()
            
            if not trans_response.data:
                return False
            
            trans_id = trans_response.data[0]['id']
            
            # Save segments
            segments = transcription_data.get("segments", [])
            if segments:
                segment_data = [
                    {
                        "transcription_id": trans_id,
                        **segment
                    }
                    for segment in segments
                ]
                
                self.client.table('transcription_segments')\
                    .insert(segment_data)\
                    .execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving transcription: {e}")
            return False
    
    # ==================== AI Agent Interactions ====================
    
    def get_agent_by_name(self, agent_name: str) -> Optional[Dict]:
        """Get AI agent configuration by name"""
        if self.mock_mode:
            for agent in self.mock_agents:
                if agent["name"] == agent_name:
                    return agent
            return None
        
        try:
            response = self.client.table('ai_agents')\
                .select('*')\
                .eq('name', agent_name)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error fetching agent: {e}")
            return None
    
    def log_agent_interaction(self, interaction_data: Dict) -> Optional[str]:
        """
        Log an interaction with AI agents.
        
        Args:
            interaction_data: Interaction details
            
        Returns:
            Interaction ID if successful
        """
        if self.mock_mode:
            self.logger.info(f"Mock: Logged agent interaction")
            return "mock-interaction-1"
        
        try:
            interaction = {
                **interaction_data,
                'created_at': datetime.now().isoformat()
            }
            
            response = self.client.table('agent_interactions')\
                .insert(interaction)\
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")
            return None
    
    def get_agent_interactions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent agent interactions for user"""
        if self.mock_mode:
            # Return mock interactions
            return [
                {
                    "id": "interaction-1",
                    "user_id": user_id,
                    "agent_id": "agent-1",
                    "input_text": "Buscar reuniões sobre planejamento",
                    "output_text": "Encontrei 3 reuniões sobre planejamento...",
                    "created_at": datetime.now().isoformat()
                }
            ]
        
        try:
            response = self.client.table('agent_interactions')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error fetching interactions: {e}")
            return []
    
    # ==================== Semantic Search ====================
    
    def semantic_search_meetings(self, query_embedding: List[float], 
                               user_id: str, limit: int = 5) -> List[Dict]:
        """
        Search meetings using vector similarity.
        
        Args:
            query_embedding: Query vector embedding
            user_id: User ID for filtering
            limit: Maximum results
            
        Returns:
            List of similar meetings
        """
        if self.mock_mode:
            # Return mock search results
            return self.mock_meetings[:limit]
        
        try:
            # Using pgvector similarity search via RPC
            response = self.client.rpc(
                'search_meetings_semantic',
                {
                    'query_embedding': query_embedding,
                    'user_id': user_id,
                    'match_threshold': 0.7,
                    'match_count': limit
                }
            ).execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
    
    # ==================== Analytics ====================
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics and analytics"""
        if self.mock_mode:
            return {
                "total_meetings": len([m for m in self.mock_meetings 
                                     if m["organizer_id"] == user_id]),
                "total_duration_hours": 12.5,
                "meetings_this_month": 3,
                "most_frequent_participants": ["Maria Santos", "João Silva"],
                "average_meeting_duration_minutes": 45
            }
        
        try:
            # Get aggregated statistics
            response = self.client.rpc(
                'get_user_meeting_stats',
                {'user_id': user_id}
            ).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            self.logger.error(f"Error fetching statistics: {e}")
            return {}
    
    # ==================== Cache Management ====================
    
    def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match cache keys
        """
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()
        
        self.logger.info(f"Cache cleared: {pattern or 'all'}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        valid_entries = sum(1 for entry in self.cache.values() if entry.is_valid())
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries
        }