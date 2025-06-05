"""
Supabase Handler - Integração centralizada com banco de dados
Sistema AURALIS - Implementação com ULTRATHINKS

Este módulo centraliza todas as operações com o banco Supabase,
fornecendo métodos otimizados para os agentes do sistema.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json
from functools import lru_cache
import logging

from supabase import create_client, Client
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class SupabaseHandler:
    """
    Classe centralizada para gerenciar todas as operações com Supabase.
    Implementa padrão Singleton para garantir única instância.
    """
    
    _instance = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseHandler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa conexão com Supabase apenas uma vez."""
        if self._client is None:
            try:
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_ANON_KEY")
                
                if not url or not key:
                    raise ValueError("Credenciais Supabase não encontradas no .env")
                
                self._client = create_client(url, key)
                logger.info("✅ Conexão com Supabase estabelecida com sucesso")
                
            except Exception as e:
                logger.error(f"❌ Erro ao conectar com Supabase: {e}")
                raise
    
    @property
    def client(self) -> Client:
        """Retorna cliente Supabase."""
        if self._client is None:
            raise RuntimeError("Cliente Supabase não inicializado")
        return self._client
    
    # ========================== MÉTODOS DE USUÁRIO ==========================
    
    def autenticar_usuario(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autentica usuário (simulado - em produção usar Supabase Auth).
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            Dict com dados do usuário ou None se falhar
        """
        try:
            # Em produção, usar Supabase Auth
            # Por ora, busca usuário por username (mock auth)
            response = self.client.table('users').select("*").eq('username', username).execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                # Em produção, verificar hash da senha
                if password == "senha123":  # Mock para teste
                    # Atualizar último login
                    self.client.table('users').update({
                        'last_login': datetime.now(timezone.utc).isoformat()
                    }).eq('id', user['id']).execute()
                    
                    return user
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None
    
    def obter_usuario_por_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados completos do usuário."""
        try:
            response = self.client.table('users').select("*").eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Erro ao obter usuário: {e}")
            return None
    
    # ========================== MÉTODOS DE REUNIÃO ==========================
    
    def criar_reuniao(self, user_id: str, titulo: str, observacoes: str = "") -> Optional[str]:
        """
        Cria nova reunião no banco.
        
        Returns:
            ID da reunião criada ou None se falhar
        """
        try:
            dados = {
                'user_id': user_id,
                'title': titulo,
                'start_time': datetime.now(timezone.utc).isoformat(),
                'status': 'recording',
                'observations': observacoes
            }
            
            response = self.client.table('meetings').insert(dados).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Erro ao criar reunião: {e}")
            return None
    
    def finalizar_reuniao(self, meeting_id: str, transcricao: str, 
                         resumo: str = "", pontos_chave: List[str] = None,
                         decisoes: List[str] = None, action_items: List[Dict] = None) -> bool:
        """
        Finaliza reunião salvando transcrição e análise.
        
        Returns:
            True se sucesso, False se falhar
        """
        try:
            # Calcular duração
            meeting = self.client.table('meetings').select('start_time').eq('id', meeting_id).execute()
            if not meeting.data:
                return False
            
            start_time = datetime.fromisoformat(meeting.data[0]['start_time'].replace('Z', '+00:00'))
            end_time = datetime.now(timezone.utc)
            duration_seconds = int((end_time - start_time).total_seconds())
            
            # Atualizar reunião
            dados = {
                'end_time': end_time.isoformat(),
                'duration_seconds': duration_seconds,
                'status': 'completed',
                'transcription_full': transcricao,
                'transcription_summary': resumo,
                'key_points': pontos_chave or [],
                'decisions': decisoes or [],
                'action_items': action_items or []
            }
            
            response = self.client.table('meetings').update(dados).eq('id', meeting_id).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Erro ao finalizar reunião: {e}")
            return False
    
    def buscar_reunioes_usuario(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca reuniões recentes do usuário."""
        try:
            response = self.client.table('meetings').select("*").eq(
                'user_id', user_id
            ).order('start_time', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Erro ao buscar reuniões: {e}")
            return []
    
    def buscar_reunioes_por_texto(self, termos_busca: List[str], user_id: Optional[str] = None, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca reuniões por texto usando função SQL.
        
        Args:
            termos_busca: Lista de termos para buscar
            user_id: Filtrar por usuário (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de reuniões relevantes
        """
        try:
            query_text = ' '.join(termos_busca)
            
            # Usar função RPC do Supabase com parâmetros corretos
            # A função espera os parâmetros como argumentos diretos
            response = self.client.rpc('search_meetings_text', {
                'query_text': query_text,
                'user_filter': user_id if user_id else None,
                'limit_results': limit
            }).execute()
            
            # Enriquecer resultados com dados completos
            if response.data:
                meeting_ids = [r['meeting_id'] for r in response.data]
                
                # Buscar dados completos das reuniões
                full_meetings = self.client.table('meetings').select("*").in_(
                    'id', meeting_ids
                ).execute()
                
                # Mapear relevância aos dados completos
                relevance_map = {r['meeting_id']: r['relevance'] for r in response.data}
                
                for meeting in full_meetings.data:
                    meeting['relevance'] = relevance_map.get(meeting['id'], 0)
                
                # Ordenar por relevância
                return sorted(full_meetings.data, key=lambda x: x['relevance'], reverse=True)
            
            return []
            
        except Exception as e:
            logger.error(f"Erro na busca textual: {e}")
            # Fallback para busca simples se função RPC não existir
            return self._busca_simples_reunioes(termos_busca, user_id, limit)
    
    def _busca_simples_reunioes(self, termos: List[str], user_id: Optional[str], 
                               limit: int) -> List[Dict[str, Any]]:
        """Fallback para busca simples se funções SQL não estiverem disponíveis."""
        try:
            query = self.client.table('meetings').select("*")
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            # Buscar todas e filtrar localmente (não ideal para grandes volumes)
            response = query.order('start_time', desc=True).limit(100).execute()
            
            resultados = []
            for meeting in response.data:
                # Busca simples nos campos de texto
                texto_completo = ' '.join([
                    meeting.get('title', ''),
                    meeting.get('transcription_summary', ''),
                    ' '.join(meeting.get('key_points', [])),
                    ' '.join(meeting.get('decisions', []))
                ]).lower()
                
                # Verificar se algum termo está presente
                if any(termo.lower() in texto_completo for termo in termos):
                    resultados.append(meeting)
                    
                if len(resultados) >= limit:
                    break
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro na busca simples: {e}")
            return []
    
    # ========================== MÉTODOS DE KNOWLEDGE BASE ==========================
    
    def buscar_documentos(self, termos_busca: List[str], department: Optional[str] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca documentos na base de conhecimento.
        
        Args:
            termos_busca: Lista de termos para buscar
            department: Filtrar por departamento (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes
        """
        try:
            query = self.client.table('knowledge_base').select("*").eq('is_current', True)
            
            if department:
                query = query.eq('department', department)
            
            # Por ora, busca simples
            # TODO: Implementar busca por chunks quando disponível
            response = query.limit(50).execute()
            
            resultados = []
            for doc in response.data:
                # Busca nos campos de texto
                texto_busca = ' '.join([
                    doc.get('title', ''),
                    doc.get('content_summary', ''),
                    ' '.join(doc.get('tags', []))
                ]).lower()
                
                if any(termo.lower() in texto_busca for termo in termos_busca):
                    resultados.append(doc)
                    
                if len(resultados) >= limit:
                    break
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def buscar_por_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Busca documentos por tags específicas."""
        try:
            # Supabase suporta operador overlap para arrays
            response = self.client.table('knowledge_base').select("*").overlaps(
                'tags', tags
            ).eq('is_current', True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Erro ao buscar por tags: {e}")
            return []
    
    # ========================== MÉTODOS DE INTERAÇÕES IA ==========================
    
    def salvar_interacao_ia(self, user_id: str, mensagem: str, resposta: str,
                           contexto: Dict[str, Any], meeting_id: Optional[str] = None,
                           response_time_ms: int = 0, tokens_used: int = 0,
                           model_used: str = "gpt-3.5-turbo") -> bool:
        """
        Salva interação com o assistente IA.
        
        Returns:
            True se sucesso, False se falhar
        """
        try:
            dados = {
                'user_id': user_id,
                'user_message': mensagem,
                'ai_response': resposta,
                'context_used': contexto,
                'meeting_id': meeting_id,
                'response_time_ms': response_time_ms,
                'tokens_used': tokens_used,
                'model_used': model_used
            }
            
            response = self.client.table('ai_interactions').insert(dados).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Erro ao salvar interação IA: {e}")
            return False
    
    def obter_historico_conversas(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtém histórico de conversas do usuário."""
        try:
            response = self.client.table('ai_interactions').select("*").eq(
                'user_id', user_id
            ).order('created_at', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def buscar_ideias_anteriores(self, desafio: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca ideias geradas anteriormente para evitar repetição.
        
        Args:
            desafio: Descrição do desafio/problema
            limit: Número máximo de resultados
            
        Returns:
            Lista de interações anteriores relacionadas
        """
        try:
            # Buscar interações que mencionam brainstorm ou ideias
            response = self.client.table('ai_interactions').select("*").or_(
                f"user_message.ilike.%brainstorm%,user_message.ilike.%ideia%,user_message.ilike.%{desafio}%"
            ).order('created_at', desc=True).limit(limit * 2).execute()
            
            # Filtrar apenas as relevantes
            relevantes = []
            for interacao in response.data:
                if 'brainstorm' in interacao['user_message'].lower() or \
                   'ideia' in interacao['user_message'].lower() or \
                   desafio.lower() in interacao['user_message'].lower():
                    relevantes.append(interacao)
                    
                if len(relevantes) >= limit:
                    break
            
            return relevantes
            
        except Exception as e:
            logger.error(f"Erro ao buscar ideias anteriores: {e}")
            return []
    
    # ========================== MÉTODOS DE ESTATÍSTICAS ==========================
    
    def obter_estatisticas_usuario(self, user_id: str) -> Dict[str, Any]:
        """Obtém estatísticas de uso do usuário."""
        try:
            # Usar view user_stats se disponível
            response = self.client.table('user_stats').select("*").eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            
            # Fallback: calcular manualmente
            stats = {
                'total_meetings': 0,
                'total_ai_interactions': 0,
                'last_meeting': None,
                'last_interaction': None
            }
            
            # Contar reuniões
            meetings = self.client.table('meetings').select('id, created_at').eq(
                'user_id', user_id
            ).execute()
            
            if meetings.data:
                stats['total_meetings'] = len(meetings.data)
                stats['last_meeting'] = max(m['created_at'] for m in meetings.data)
            
            # Contar interações
            interactions = self.client.table('ai_interactions').select('id, created_at').eq(
                'user_id', user_id
            ).execute()
            
            if interactions.data:
                stats['total_ai_interactions'] = len(interactions.data)
                stats['last_interaction'] = max(i['created_at'] for i in interactions.data)
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    # ========================== MÉTODOS DE CACHE ==========================
    
    @lru_cache(maxsize=100)
    def _cache_busca_reunioes(self, cache_key: str) -> List[Dict[str, Any]]:
        """Cache interno para buscas frequentes."""
        # Implementação depende da chave de cache
        return []
    
    def limpar_cache(self):
        """Limpa cache interno."""
        self._cache_busca_reunioes.cache_clear()
    
    # ========================== MÉTODOS AUXILIARES ==========================
    
    def testar_conexao(self) -> bool:
        """Testa se a conexão com Supabase está funcionando."""
        try:
            # Tenta uma query simples
            response = self.client.table('users').select('id').limit(1).execute()
            return True
        except:
            return False
    
    def obter_resumo_sistema(self) -> Dict[str, int]:
        """Obtém resumo geral do sistema."""
        try:
            resumo = {}
            
            # Total de usuários ativos
            users = self.client.table('users').select('id').eq('is_active', True).execute()
            resumo['usuarios_ativos'] = len(users.data) if users.data else 0
            
            # Total de reuniões
            meetings = self.client.table('meetings').select('id').eq('status', 'completed').execute()
            resumo['reunioes_completas'] = len(meetings.data) if meetings.data else 0
            
            # Total de documentos
            docs = self.client.table('knowledge_base').select('id').eq('is_current', True).execute()
            resumo['documentos_ativos'] = len(docs.data) if docs.data else 0
            
            # Interações hoje
            hoje = datetime.now(timezone.utc).date().isoformat()
            interactions = self.client.table('ai_interactions').select('id').gte(
                'created_at', f'{hoje}T00:00:00Z'
            ).execute()
            resumo['interacoes_hoje'] = len(interactions.data) if interactions.data else 0
            
            return resumo
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}


# Instância global para uso em todo o sistema
supabase_handler = SupabaseHandler()