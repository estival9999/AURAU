"""
Integração Backend AURALIS
Módulo principal que conecta a interface gráfica (GUI) com o sistema de agentes IA
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
from threading import Thread
import json

# Importar sistema de agentes
from src.agentes.sistema_agentes import SistemaAgentes
from src.database.supabase_handler import SupabaseHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AURALISBackend:
    """
    Classe backend principal que integra todos os componentes AURALIS.
    Gerencia autenticação, processamento de mensagens e operações de banco de dados.
    """
    
    def __init__(self):
        """
        Inicializa o backend AURALIS.
        APENAS Supabase na nuvem - sem mocks ou fallbacks locais.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando Backend AURALIS (APENAS Supabase)")
        
        # Inicializar componentes
        self.sistema_agentes = SistemaAgentes(modo_debug=True)
        
        # Inicializar handler do Supabase - OBRIGATÓRIO
        try:
            from src.database.supabase_handler import SupabaseHandler
            self.db_handler = SupabaseHandler()
            # Testar conexão
            if not self.db_handler.testar_conexao():
                raise Exception("Falha na conexão com Supabase")
            self.logger.info("Conexão com Supabase estabelecida")
        except Exception as e:
            self.logger.error(f"ERRO CRÍTICO: Não foi possível conectar ao Supabase: {e}")
            raise RuntimeError(f"Sistema requer Supabase. Configure as credenciais no .env: {e}")
        
        # Estado da sessão atual
        self.current_user = None
        self.current_meeting_context = None
        self.session_start = datetime.now()
        
        # Cache para operações frequentes
        self.response_cache = {}
        self.cache_ttl_seconds = 300  # 5 minutos
        
        # Estatísticas
        self.stats = {
            "messages_processed": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_response_time": 0
        }
    
    # ==================== Autenticação ====================
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Autentica usuário através do banco de dados.
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            Dicionário com perfil do usuário ou None se a autenticação falhar
        """
        try:
            # Usar APENAS autenticação Supabase
            if not self.db_handler:
                raise RuntimeError("Sistema requer conexão com Supabase")
            
            user = self.db_handler.autenticar_usuario(username, password)
            
            if user:
                self.current_user = user
                self.logger.info(f"Usuário {username} autenticado com sucesso")
                
                # Atualizar contexto dos agentes com informações do usuário
                self.sistema_agentes.atualizar_contexto_global({
                    "usuario_atual": user,
                    "area_usuario": user.get('area', 'geral'),
                    "preferencias": user.get('preferences', {})
                })
                
                # Registrar início da sessão
                self.db_handler.salvar_interacao_ia(
                        user_id=user['id'],
                        mensagem=f"Login: {username}",
                        resposta="Sessão iniciada",
                        contexto={"timestamp": datetime.now().isoformat()},
                        model_used="sistema"
                    )
            
            return user
            
        except Exception as e:
            self.logger.error(f"Erro de autenticação: {e}")
            self.stats["errors"] += 1
            return None
    
    def logout(self):
        """Faz logout do usuário atual e limpa a sessão"""
        if self.current_user:
            # Registrar fim da sessão
            if self.db_handler:
                self.db_handler.salvar_interacao_ia(
                    user_id=self.current_user['id'],
                    mensagem="Logout",
                    resposta="Sessão encerrada",
                    contexto={
                        "session_duration": str(datetime.now() - self.session_start),
                        "messages_processed": self.stats["messages_processed"]
                    },
                    model_used="sistema"
                )
            
            self.logger.info(f"Usuário {self.current_user['username']} fez logout")
        
        # Limpar dados da sessão
        self.current_user = None
        self.current_meeting_context = None
        self.response_cache.clear()
        self.sistema_agentes.atualizar_contexto_global({})
    
    # ==================== Gerenciamento de Reuniões ====================
    
    def get_meeting_history(self, limit: int = 10) -> List[Dict]:
        """
        Obtém histórico de reuniões do usuário atual.
        
        Args:
            limit: Número máximo de reuniões para retornar
            
        Returns:
            Lista de dicionários de reuniões
        """
        if not self.current_user:
            return []
        
        try:
            # Usar APENAS dados do Supabase
            if not self.db_handler:
                raise RuntimeError("Sistema requer conexão com Supabase")
            
            meetings = self.db_handler.buscar_reunioes_usuario(
                self.current_user['id'], 
                limit
            )
            
            # Formatar reuniões para exibição no frontend
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
            self.logger.error(f"Erro ao buscar histórico de reuniões: {e}")
            self.stats["errors"] += 1
            return []
    
    def get_meeting_details(self, meeting_id: str) -> Optional[Dict]:
        """Obtém informações detalhadas da reunião incluindo transcrição"""
        try:
            if not self.db_handler:
                raise RuntimeError("Sistema requer conexão com Supabase")
            
            # Buscar no banco
            meetings = self.db_handler.buscar_reunioes_usuario(self.current_user['id'])
            meeting = next((m for m in meetings if m['id'] == meeting_id), None)
            if not meeting:
                return None
            transcription = meeting.get('transcription_full')
            
            # Formatar para o frontend
            return {
                'meeting': meeting,
                'transcription': transcription,
                'formatted_text': self._format_transcription(transcription) if transcription else None
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar detalhes da reunião: {e}")
            return None
    
    def save_meeting(self, meeting_data: Dict) -> Optional[str]:
        """Salva uma nova reunião"""
        if not self.current_user:
            return None
        
        try:
            # Adicionar organizador e timestamps
            meeting_data['organizer_id'] = self.current_user['id']
            meeting_data['start_time'] = datetime.now().isoformat()
            meeting_data['status'] = 'scheduled'
            
            # Usar APENAS Supabase
            if not self.db_handler:
                raise RuntimeError("Sistema requer conexão com Supabase")
            
            meeting_id = self.db_handler.criar_reuniao(
                user_id=self.current_user['id'],
                titulo=meeting_data.get('title', 'Reunião'),
                observacoes=meeting_data.get('observations', '')
            )
            
            if meeting_id:
                self.logger.info(f"Reunião salva com ID: {meeting_id}")
            
            return meeting_id
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar reunião: {e}")
            return None
    
    # ==================== Processamento de Mensagens IA ====================
    
    def process_user_message(self, message: str, 
                           meeting_context: Optional[str] = None,
                           use_cache: bool = True) -> str:
        """
        Processa mensagem do usuário através do sistema de agentes.
        
        Args:
            message: Mensagem do usuário
            meeting_context: Contexto opcional da reunião
            use_cache: Se deve usar cache de respostas
            
        Returns:
            String com resposta da IA
        """
        start_time = datetime.now()
        
        try:
            # Verificar cache primeiro
            cache_key = f"{message}_{meeting_context or 'geral'}"
            if use_cache and cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                cache_age = (datetime.now() - cached_response['timestamp']).total_seconds()
                
                if cache_age < self.cache_ttl_seconds:
                    self.stats["cache_hits"] += 1
                    self.logger.info("Retornando resposta do cache")
                    return cached_response['response']
            
            # Construir contexto completo
            context = self._build_context(meeting_context)
            
            # Processar através dos agentes
            self.logger.info(f"Processando mensagem: {message[:50]}...")
            response = self.sistema_agentes.processar_mensagem_usuario(
                message, 
                context
            )
            
            # Armazenar resposta no cache
            if use_cache:
                self.response_cache[cache_key] = {
                    'response': response,
                    'timestamp': datetime.now()
                }
            
            # Registrar interação
            self._log_interaction(message, response, context)
            
            # Atualizar estatísticas
            self.stats["messages_processed"] += 1
            response_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_response_time"] += response_time
            
            self.logger.info(f"Mensagem processada em {response_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}")
            self.stats["errors"] += 1
            
            # Retornar mensagem de erro amigável
            return self._get_error_response(str(e))
    
    def process_voice_command(self, audio_text: str) -> str:
        """
        Processa comando de voz (texto transcrito).
        
        Args:
            audio_text: Comando de voz transcrito
            
        Returns:
            Resposta da IA
        """
        # Adicionar marcador de comando de voz para contexto
        return self.process_user_message(
            f"[Comando de voz] {audio_text}",
            self.current_meeting_context
        )
    
    # ==================== Contexto e Análise ====================
    
    def analyze_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Analisa uma reunião específica usando agentes IA.
        
        Args:
            meeting_id: ID da reunião para analisar
            
        Returns:
            Resultados da análise
        """
        try:
            # Obter detalhes da reunião
            meeting_data = self.get_meeting_details(meeting_id)
            if not meeting_data:
                return {"error": "Reunião não encontrada"}
            
            meeting = meeting_data['meeting']
            transcription = meeting_data.get('transcription')
            
            # Definir contexto da reunião
            self.current_meeting_context = meeting['title']
            
            # Preparar prompts de análise
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
            
            # Compilar análise completa
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
            self.logger.error(f"Erro ao analisar reunião: {e}")
            return {"error": str(e)}
    
    def get_contextual_suggestions(self) -> List[str]:
        """
        Obtém sugestões contextuais baseadas no estado atual.
        
        Returns:
            Lista de consultas sugeridas
        """
        suggestions = []
        
        if self.current_meeting_context:
            # Sugestões específicas da reunião
            suggestions.extend([
                "Resumir principais decisões desta reunião",
                "Listar ações pendentes",
                "Identificar participantes mencionados",
                "Analisar sentimento geral da reunião",
                "Gerar email de follow-up"
            ])
        else:
            # Sugestões gerais
            suggestions.extend([
                "Buscar reuniões recentes",
                "Mostrar minhas tarefas pendentes",
                "Analisar tendências das últimas reuniões",
                "Gerar relatório semanal",
                "Sugerir pauta para próxima reunião"
            ])
        
        # Adicionar sugestões específicas do usuário baseadas no papel
        if self.current_user:
            role = self.current_user.get('role', 'user')
            if role == 'admin':
                suggestions.extend([
                    "Mostrar estatísticas da equipe",
                    "Analisar produtividade geral"
                ])
        
        return suggestions[:5]  # Retornar as 5 principais sugestões
    
    # ==================== Estatísticas e Análise ====================
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas da sessão atual"""
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
        """Obtém análise de dados do usuário do banco de dados"""
        if not self.current_user or self.mock_mode or not self.db_handler:
            return {
                'total_meetings': 0,
                'total_ai_interactions': 0
            }
        
        return self.db_handler.obter_estatisticas_usuario(self.current_user['id'])
    
    # ==================== Métodos Auxiliares ====================
    
    def _build_context(self, meeting_context: Optional[str] = None) -> Dict[str, Any]:
        """Constrói contexto completo para processamento dos agentes"""
        context = {
            "usuario": self.current_user,
            "timestamp": datetime.now().isoformat(),
            "session_info": {
                "duration": str(datetime.now() - self.session_start),
                "messages_count": self.stats["messages_processed"]
            }
        }
        
        # Adicionar contexto da reunião se disponível
        if meeting_context:
            context["reuniao_contexto"] = meeting_context
            
            # Buscar dados da reunião APENAS no Supabase
            if not self.db_handler:
                raise RuntimeError("Sistema requer conexão com Supabase")
            
            # Buscar por título
            all_meetings = self.db_handler.buscar_reunioes_usuario(self.current_user['id'])
            meetings = [m for m in all_meetings if meeting_context.lower() in m.get('title', '').lower()]
            
            if meetings:
                meeting = meetings[0]
                context["dados_reuniao"] = {
                    "id": meeting['id'],
                    "titulo": meeting['title'],
                    "data": meeting['scheduled_start'],
                    "participantes": self._get_participant_names(meeting)
                }
                
                # Adicionar transcrição se disponível
                if 'transcription_full' in meeting:
                    context["transcricao"] = meeting['transcription_full']
        
        return context
    
    def _log_interaction(self, input_text: str, output_text: str, context: Dict):
        """Registra interação no banco de dados"""
        if not self.current_user or not self.db_handler:
            raise RuntimeError("Sistema requer conexão com Supabase e usuário autenticado")
        
        try:
            # Usar método correto do SupabaseHandler
            self.db_handler.salvar_interacao_ia(
                user_id=self.current_user['id'],
                mensagem=input_text[:1000],
                resposta=output_text[:5000],
                contexto=context,
                response_time_ms=100,  # Estimativa
                tokens_used=self._estimate_tokens(input_text + output_text),
                model_used="gpt-3.5-turbo"
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar interação: {e}")
    
    def _get_orchestrator_agent_id(self) -> str:
        """Obtém ID do agente orquestrador"""
        return 'orchestrator-001'  # ID fixo para simplificar
    
    def _get_error_response(self, error: str) -> str:
        """Obtém resposta de erro amigável ao usuário"""
        error_responses = {
            "connection": "Desculpe, estou com problemas de conexão. Tente novamente em instantes.",
            "timeout": "A operação demorou muito. Por favor, tente novamente.",
            "api": "Serviço temporariamente indisponível. Usando respostas simuladas.",
            "default": "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
        }
        
        # Determinar tipo de erro
        error_type = "default"
        if "connection" in error.lower() or "network" in error.lower():
            error_type = "connection"
        elif "timeout" in error.lower():
            error_type = "timeout"
        elif "api" in error.lower() or "openai" in error.lower():
            error_type = "api"
        
        return error_responses[error_type]
    
    def _format_date(self, datetime_str: str) -> str:
        """Formata string de datetime para data"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m")
        except:
            return datetime_str[:10]
    
    def _format_time(self, datetime_str: str) -> str:
        """Formata string de datetime para hora"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return datetime_str[11:16] if len(datetime_str) > 16 else "00:00"
    
    def _format_duration(self, seconds: int) -> str:
        """Formata duração em segundos para formato legível"""
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
        """Extrai nomes dos participantes dos dados da reunião"""
        participants = []
        
        # Adicionar organizador
        if 'organizer' in meeting:
            participants.append(meeting['organizer'].get('full_name', 'Organizador'))
        
        # Adicionar participantes
        if 'meeting_participants' in meeting:
            for participant in meeting['meeting_participants']:
                if 'user' in participant:
                    participants.append(participant['user'].get('full_name', 'Participante'))
        
        return participants
    
    def _format_transcription(self, transcription: Dict) -> str:
        """Formata transcrição para exibição"""
        if not transcription:
            return "Transcrição não disponível"
        
        formatted = []
        
        # Adicionar segmentos se disponíveis
        if 'transcription_segments' in transcription:
            for segment in transcription['transcription_segments']:
                speaker = segment.get('speaker_name', 'Desconhecido')
                text = segment.get('text', '')
                formatted.append(f"{speaker}: {text}")
        else:
            # Usar texto completo
            formatted.append(transcription.get('full_text', ''))
        
        return '\n\n'.join(formatted)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima contagem de tokens (aproximação)"""
        # Estimativa aproximada: 1 token ≈ 4 caracteres
        return len(text) // 4


# ==================== Funções de Wrapper Assíncrono ====================

def create_backend() -> AURALISBackend:
    """Cria e inicializa o backend AURALIS - APENAS com Supabase"""
    return AURALISBackend()


def process_message_async(backend: AURALISBackend, message: str, 
                         callback: callable, error_callback: callable = None):
    """
    Processa mensagem de forma assíncrona em uma thread.
    
    Args:
        backend: Instância do backend AURALIS
        message: Mensagem do usuário
        callback: Função para chamar com a resposta
        error_callback: Função opcional para chamar em caso de erro
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


# ==================== Testes ====================

if __name__ == "__main__":
    # Testar funcionalidade do backend
    print("Testando Backend AURALIS...")
    
    # Criar backend - REQUER Supabase configurado
    backend = create_backend()
    
    # Testar autenticação
    print("\n1. Testando autenticação...")
    user = backend.authenticate("admin", "password")
    print(f"Autenticado: {user['username'] if user else 'Falhou'}")
    
    # Testar processamento de mensagens
    print("\n2. Testando processamento de mensagens...")
    response = backend.process_user_message("Olá, como posso usar o sistema?")
    print(f"Resposta: {response[:100]}...")
    
    # Testar histórico de reuniões
    print("\n3. Testando histórico de reuniões...")
    meetings = backend.get_meeting_history()
    print(f"Encontradas {len(meetings)} reuniões")
    
    # Testar sugestões
    print("\n4. Testando sugestões...")
    suggestions = backend.get_contextual_suggestions()
    print(f"Sugestões: {suggestions}")
    
    # Testar estatísticas
    print("\n5. Testando estatísticas...")
    stats = backend.get_session_statistics()
    print(f"Estatísticas da sessão: {stats}")
    
    print("\nTodos os testes concluídos!")