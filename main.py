"""
AURALIS Backend Integration
Main module that bridges the frontend GUI with the AI agent system
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
from threading import Thread
import json

# Import agent system
from src.agentes.sistema_agentes import SistemaAgentes
from src.database.supabase_handler import SupabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AURALISBackend:
    """
    Main backend class that integrates all AURALIS components.
    Handles authentication, message processing, and database operations.
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize AURALIS backend.
        
        Args:
            mock_mode: Force mock mode (None = auto-detect based on environment)
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine mode
        if mock_mode is None:
            mock_mode = not os.getenv("OPENAI_API_KEY") or os.getenv("DEBUG_MODE") == "True"
        
        self.mock_mode = mock_mode
        self.logger.info(f"Initializing AURALIS Backend (mock_mode={mock_mode})")
        
        # Initialize components
        self.sistema_agentes = SistemaAgentes(modo_debug=True)
        self.db_handler = SupabaseHandler(mock_mode=mock_mode)
        
        # Current session state
        self.current_user = None
        self.current_meeting_context = None
        self.session_start = datetime.now()
        
        # Cache for frequent operations
        self.response_cache = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "messages_processed": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_response_time": 0
        }
    
    # ==================== Authentication ====================
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user through database.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User profile dict or None if authentication fails
        """
        try:
            user = self.db_handler.authenticate_user(username, password)
            
            if user:
                self.current_user = user
                self.logger.info(f"User {username} authenticated successfully")
                
                # Update agent context with user info
                self.sistema_agentes.atualizar_contexto_global({
                    "usuario_atual": user,
                    "area_usuario": user.get('area', 'geral'),
                    "preferencias": user.get('preferences', {})
                })
                
                # Log session start
                self.db_handler.log_agent_interaction({
                    'user_id': user['id'],
                    'agent_id': self._get_orchestrator_agent_id(),
                    'interaction_type': 'session_start',
                    'input_text': f"Login: {username}",
                    'output_text': "Sessão iniciada",
                    'context': {"timestamp": datetime.now().isoformat()}
                })
            
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            self.stats["errors"] += 1
            return None
    
    def logout(self):
        """Logout current user and clean up session"""
        if self.current_user:
            # Log session end
            self.db_handler.log_agent_interaction({
                'user_id': self.current_user['id'],
                'agent_id': self._get_orchestrator_agent_id(),
                'interaction_type': 'session_end',
                'input_text': "Logout",
                'output_text': "Sessão encerrada",
                'context': {
                    "session_duration": str(datetime.now() - self.session_start),
                    "messages_processed": self.stats["messages_processed"]
                }
            })
            
            self.logger.info(f"User {self.current_user['username']} logged out")
        
        # Clear session data
        self.current_user = None
        self.current_meeting_context = None
        self.response_cache.clear()
        self.sistema_agentes.atualizar_contexto_global({})
    
    # ==================== Meeting Management ====================
    
    def get_meeting_history(self, limit: int = 10) -> List[Dict]:
        """
        Get meeting history for current user.
        
        Args:
            limit: Maximum number of meetings to return
            
        Returns:
            List of meeting dictionaries
        """
        if not self.current_user:
            return []
        
        try:
            meetings = self.db_handler.get_user_meetings(
                self.current_user['id'], 
                limit
            )
            
            # Format meetings for frontend display
            formatted_meetings = []
            for meeting in meetings:
                formatted_meetings.append({
                    'id': meeting['id'],
                    'titulo': meeting['title'],
                    'data': self._format_date(meeting['scheduled_start']),
                    'hora': self._format_time(meeting['scheduled_start']),
                    'duracao': self._format_duration(meeting.get('duration_seconds', 0)),
                    'status': meeting.get('status', 'completed'),
                    'participantes': self._get_participant_names(meeting)
                })
            
            return formatted_meetings
            
        except Exception as e:
            self.logger.error(f"Error fetching meeting history: {e}")
            self.stats["errors"] += 1
            return []
    
    def get_meeting_details(self, meeting_id: str) -> Optional[Dict]:
        """Get detailed meeting information including transcription"""
        try:
            meeting = self.db_handler.get_meeting_by_id(meeting_id)
            if not meeting:
                return None
            
            # Get transcription
            transcription = self.db_handler.get_meeting_transcription(meeting_id)
            
            # Format for frontend
            return {
                'meeting': meeting,
                'transcription': transcription,
                'formatted_text': self._format_transcription(transcription) if transcription else None
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching meeting details: {e}")
            return None
    
    def save_meeting(self, meeting_data: Dict) -> Optional[str]:
        """Save a new meeting"""
        if not self.current_user:
            return None
        
        try:
            # Add organizer and timestamps
            meeting_data['organizer_id'] = self.current_user['id']
            meeting_data['created_at'] = datetime.now().isoformat()
            meeting_data['status'] = 'scheduled'
            
            meeting_id = self.db_handler.save_meeting(meeting_data)
            
            if meeting_id:
                self.logger.info(f"Meeting saved with ID: {meeting_id}")
            
            return meeting_id
            
        except Exception as e:
            self.logger.error(f"Error saving meeting: {e}")
            return None
    
    # ==================== AI Message Processing ====================
    
    def process_user_message(self, message: str, 
                           meeting_context: Optional[str] = None,
                           use_cache: bool = True) -> str:
        """
        Process user message through agent system.
        
        Args:
            message: User message
            meeting_context: Optional meeting context
            use_cache: Whether to use response cache
            
        Returns:
            AI response string
        """
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = f"{message}_{meeting_context or 'general'}"
            if use_cache and cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                cache_age = (datetime.now() - cached_response['timestamp']).total_seconds()
                
                if cache_age < self.cache_ttl_seconds:
                    self.stats["cache_hits"] += 1
                    self.logger.info("Returning cached response")
                    return cached_response['response']
            
            # Build complete context
            context = self._build_context(meeting_context)
            
            # Process through agents
            self.logger.info(f"Processing message: {message[:50]}...")
            response = self.sistema_agentes.processar_mensagem_usuario(
                message, 
                context
            )
            
            # Cache response
            if use_cache:
                self.response_cache[cache_key] = {
                    'response': response,
                    'timestamp': datetime.now()
                }
            
            # Log interaction
            self._log_interaction(message, response, context)
            
            # Update statistics
            self.stats["messages_processed"] += 1
            response_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_response_time"] += response_time
            
            self.logger.info(f"Message processed in {response_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.stats["errors"] += 1
            
            # Return friendly error message
            return self._get_error_response(str(e))
    
    def process_voice_command(self, audio_text: str) -> str:
        """
        Process voice command (transcribed text).
        
        Args:
            audio_text: Transcribed voice command
            
        Returns:
            AI response
        """
        # Add voice command marker for context
        return self.process_user_message(
            f"[Comando de voz] {audio_text}",
            self.current_meeting_context
        )
    
    # ==================== Context and Analysis ====================
    
    def analyze_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Analyze a specific meeting using AI agents.
        
        Args:
            meeting_id: Meeting ID to analyze
            
        Returns:
            Analysis results
        """
        try:
            # Get meeting details
            meeting_data = self.get_meeting_details(meeting_id)
            if not meeting_data:
                return {"error": "Reunião não encontrada"}
            
            meeting = meeting_data['meeting']
            transcription = meeting_data.get('transcription')
            
            # Set meeting context
            self.current_meeting_context = meeting['title']
            
            # Prepare analysis prompts
            analysis_tasks = [
                ("Resumir os principais pontos discutidos", "summary"),
                ("Listar todas as decisões tomadas", "decisions"),
                ("Identificar ações pendentes e responsáveis", "actions"),
                ("Analisar riscos ou preocupações mencionadas", "risks")
            ]
            
            results = {}
            
            for prompt, key in analysis_tasks:
                response = self.process_user_message(
                    prompt,
                    meeting_context=meeting['title'],
                    use_cache=True
                )
                results[key] = response
            
            # Compile complete analysis
            analysis = {
                "meeting_id": meeting_id,
                "meeting_title": meeting['title'],
                "analysis_timestamp": datetime.now().isoformat(),
                "results": results,
                "statistics": {
                    "duration_minutes": meeting.get('duration_seconds', 0) / 60,
                    "participants": len(meeting.get('meeting_participants', [])),
                    "has_transcription": transcription is not None
                }
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing meeting: {e}")
            return {"error": str(e)}
    
    def get_contextual_suggestions(self) -> List[str]:
        """
        Get contextual suggestions based on current state.
        
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        if self.current_meeting_context:
            # Meeting-specific suggestions
            suggestions.extend([
                "Resumir principais decisões desta reunião",
                "Listar ações pendentes",
                "Identificar participantes mencionados",
                "Analisar sentimento geral da reunião",
                "Gerar email de follow-up"
            ])
        else:
            # General suggestions
            suggestions.extend([
                "Buscar reuniões recentes",
                "Mostrar minhas tarefas pendentes",
                "Analisar tendências das últimas reuniões",
                "Gerar relatório semanal",
                "Sugerir pauta para próxima reunião"
            ])
        
        # Add user-specific suggestions based on role
        if self.current_user:
            role = self.current_user.get('role', 'user')
            if role == 'admin':
                suggestions.extend([
                    "Mostrar estatísticas da equipe",
                    "Analisar produtividade geral"
                ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    # ==================== Statistics and Analytics ====================
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        avg_response_time = 0
        if self.stats["messages_processed"] > 0:
            avg_response_time = self.stats["total_response_time"] / self.stats["messages_processed"]
        
        return {
            "session_duration": str(datetime.now() - self.session_start),
            "messages_processed": self.stats["messages_processed"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": self.stats["cache_hits"] / max(1, self.stats["messages_processed"]),
            "errors": self.stats["errors"],
            "average_response_time": f"{avg_response_time:.2f}s",
            "current_user": self.current_user['username'] if self.current_user else None
        }
    
    def get_user_analytics(self) -> Dict[str, Any]:
        """Get user analytics from database"""
        if not self.current_user:
            return {}
        
        return self.db_handler.get_user_statistics(self.current_user['id'])
    
    # ==================== Helper Methods ====================
    
    def _build_context(self, meeting_context: Optional[str] = None) -> Dict[str, Any]:
        """Build complete context for agent processing"""
        context = {
            "usuario": self.current_user,
            "timestamp": datetime.now().isoformat(),
            "session_info": {
                "duration": str(datetime.now() - self.session_start),
                "messages_count": self.stats["messages_processed"]
            }
        }
        
        # Add meeting context if available
        if meeting_context:
            context["reuniao_contexto"] = meeting_context
            
            # Try to load meeting data
            meetings = self.db_handler.search_meetings_by_title(
                meeting_context, 
                self.current_user['id']
            )
            
            if meetings:
                meeting = meetings[0]
                context["dados_reuniao"] = {
                    "id": meeting['id'],
                    "titulo": meeting['title'],
                    "data": meeting['scheduled_start'],
                    "participantes": self._get_participant_names(meeting)
                }
                
                # Add transcription if available
                transcription = self.db_handler.get_meeting_transcription(meeting['id'])
                if transcription:
                    context["transcricao"] = transcription['full_text']
        
        return context
    
    def _log_interaction(self, input_text: str, output_text: str, context: Dict):
        """Log interaction to database"""
        if not self.current_user:
            return
        
        try:
            interaction_data = {
                'user_id': self.current_user['id'],
                'agent_id': self._get_orchestrator_agent_id(),
                'interaction_type': 'chat',
                'input_text': input_text[:1000],  # Limit text size
                'output_text': output_text[:5000],  # Limit text size
                'context': json.dumps(context, ensure_ascii=False),
                'tokens_used': self._estimate_tokens(input_text + output_text)
            }
            
            self.db_handler.log_agent_interaction(interaction_data)
            
        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")
    
    def _get_orchestrator_agent_id(self) -> str:
        """Get orchestrator agent ID (cached)"""
        if not hasattr(self, '_orchestrator_id'):
            agent = self.db_handler.get_agent_by_name('Orquestrador AURALIS')
            self._orchestrator_id = agent['id'] if agent else 'default-orchestrator'
        return self._orchestrator_id
    
    def _get_error_response(self, error: str) -> str:
        """Get user-friendly error response"""
        error_responses = {
            "connection": "Desculpe, estou com problemas de conexão. Tente novamente em instantes.",
            "timeout": "A operação demorou muito. Por favor, tente novamente.",
            "api": "Serviço temporariamente indisponível. Usando respostas simuladas.",
            "default": "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
        }
        
        # Determine error type
        error_type = "default"
        if "connection" in error.lower() or "network" in error.lower():
            error_type = "connection"
        elif "timeout" in error.lower():
            error_type = "timeout"
        elif "api" in error.lower() or "openai" in error.lower():
            error_type = "api"
        
        return error_responses[error_type]
    
    def _format_date(self, datetime_str: str) -> str:
        """Format datetime string to date"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m")
        except:
            return datetime_str[:10]
    
    def _format_time(self, datetime_str: str) -> str:
        """Format datetime string to time"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return datetime_str[11:16] if len(datetime_str) > 16 else "00:00"
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable"""
        if seconds < 60:
            return f"{seconds} seg"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} min"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}min"
            return f"{hours}h"
    
    def _get_participant_names(self, meeting: Dict) -> List[str]:
        """Extract participant names from meeting data"""
        participants = []
        
        # Add organizer
        if 'organizer' in meeting:
            participants.append(meeting['organizer'].get('full_name', 'Organizador'))
        
        # Add participants
        if 'meeting_participants' in meeting:
            for participant in meeting['meeting_participants']:
                if 'user' in participant:
                    participants.append(participant['user'].get('full_name', 'Participante'))
        
        return participants
    
    def _format_transcription(self, transcription: Dict) -> str:
        """Format transcription for display"""
        if not transcription:
            return "Transcrição não disponível"
        
        formatted = []
        
        # Add segments if available
        if 'transcription_segments' in transcription:
            for segment in transcription['transcription_segments']:
                speaker = segment.get('speaker_name', 'Desconhecido')
                text = segment.get('text', '')
                formatted.append(f"{speaker}: {text}")
        else:
            # Use full text
            formatted.append(transcription.get('full_text', ''))
        
        return '\n\n'.join(formatted)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4


# ==================== Async Wrapper Functions ====================

def create_backend(mock_mode: bool = None) -> AURALISBackend:
    """Create and initialize AURALIS backend"""
    return AURALISBackend(mock_mode=mock_mode)


def process_message_async(backend: AURALISBackend, message: str, 
                         callback: callable, error_callback: callable = None):
    """
    Process message asynchronously in a thread.
    
    Args:
        backend: AURALIS backend instance
        message: User message
        callback: Function to call with response
        error_callback: Optional function to call on error
    """
    def _process():
        try:
            response = backend.process_user_message(message)
            callback(response)
        except Exception as e:
            if error_callback:
                error_callback(str(e))
            else:
                callback(f"Erro: {str(e)}")
    
    thread = Thread(target=_process)
    thread.daemon = True
    thread.start()


# ==================== Testing ====================

if __name__ == "__main__":
    # Test backend functionality
    print("Testing AURALIS Backend...")
    
    # Create backend in mock mode
    backend = create_backend(mock_mode=True)
    
    # Test authentication
    print("\n1. Testing authentication...")
    user = backend.authenticate("admin", "password")
    print(f"Authenticated: {user['username'] if user else 'Failed'}")
    
    # Test message processing
    print("\n2. Testing message processing...")
    response = backend.process_user_message("Olá, como posso usar o sistema?")
    print(f"Response: {response[:100]}...")
    
    # Test meeting history
    print("\n3. Testing meeting history...")
    meetings = backend.get_meeting_history()
    print(f"Found {len(meetings)} meetings")
    
    # Test suggestions
    print("\n4. Testing suggestions...")
    suggestions = backend.get_contextual_suggestions()
    print(f"Suggestions: {suggestions}")
    
    # Test statistics
    print("\n5. Testing statistics...")
    stats = backend.get_session_statistics()
    print(f"Session stats: {stats}")
    
    print("\nAll tests completed!")