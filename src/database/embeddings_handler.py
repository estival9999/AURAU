"""
Handler para gerenciamento de embeddings e busca semântica.
Utiliza OpenAI para gerar embeddings e Supabase para armazenamento vetorial.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging
from openai import OpenAI
import numpy as np

# Configurar logging
logger = logging.getLogger(__name__)

class EmbeddingsHandler:
    """
    Gerencia a criação, armazenamento e busca de embeddings.
    
    Responsabilidades:
    - Gerar embeddings usando OpenAI
    - Armazenar embeddings no Supabase
    - Realizar buscas semânticas
    - Processar documentos em chunks
    """
    
    def __init__(self, supabase_client=None):
        """
        Inicializa o handler de embeddings.
        
        Args:
            supabase_client: Cliente Supabase (opcional)
        """
        # Inicializar OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY não configurada no ambiente")
        
        self.openai_client = OpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-3-small"  # Modelo mais eficiente
        
        # Cliente Supabase
        if supabase_client:
            self.supabase = supabase_client
        else:
            from .supabase_handler import SupabaseHandler
            self.supabase = SupabaseHandler()
        
        # Configurações
        self.chunk_size = 1000  # Caracteres por chunk
        self.chunk_overlap = 200  # Sobreposição entre chunks
        self.max_chunks_per_doc = 50  # Limite de chunks por documento
        
    def gerar_embedding(self, texto: str) -> List[float]:
        """
        Gera embedding para um texto usando OpenAI.
        
        Args:
            texto: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        try:
            # Limpar e preparar texto
            texto_limpo = texto.strip()
            if not texto_limpo:
                return []
            
            # Gerar embedding via OpenAI
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texto_limpo
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise RuntimeError(f"Falha ao gerar embedding: {e}")
    
    def processar_texto_em_chunks(self, texto: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Divide texto em chunks com sobreposição para processamento.
        
        Args:
            texto: Texto completo para dividir
            metadata: Metadados adicionais para cada chunk
            
        Returns:
            Lista de chunks com seus metadados
        """
        chunks = []
        texto_limpo = texto.strip()
        
        if not texto_limpo:
            return chunks
        
        # Dividir texto em chunks
        inicio = 0
        chunk_id = 0
        
        while inicio < len(texto_limpo) and chunk_id < self.max_chunks_per_doc:
            # Definir fim do chunk
            fim = min(inicio + self.chunk_size, len(texto_limpo))
            
            # Tentar quebrar em espaço para não cortar palavras
            if fim < len(texto_limpo):
                ultimo_espaco = texto_limpo.rfind(' ', inicio, fim)
                if ultimo_espaco > inicio:
                    fim = ultimo_espaco
            
            # Extrair chunk
            chunk_texto = texto_limpo[inicio:fim].strip()
            
            if chunk_texto:
                chunk_data = {
                    'chunk_id': chunk_id,
                    'text': chunk_texto,
                    'start_char': inicio,
                    'end_char': fim,
                    'embedding': None,  # Será preenchido depois
                    'metadata': metadata or {}
                }
                chunks.append(chunk_data)
                chunk_id += 1
            
            # Próximo chunk com sobreposição
            inicio = fim - self.chunk_overlap
            if inicio <= 0:
                inicio = fim
        
        return chunks
    
    def processar_reuniao_para_embeddings(self, reuniao_id: str, titulo: str, 
                                         transcricao: str, resumo: str = None,
                                         decisoes: List[str] = None) -> int:
        """
        Processa uma reunião completa gerando embeddings para busca.
        
        Args:
            reuniao_id: ID da reunião
            titulo: Título da reunião
            transcricao: Transcrição completa
            resumo: Resumo da reunião (opcional)
            decisoes: Lista de decisões tomadas
            
        Returns:
            Número de embeddings criados
        """
        embeddings_criados = 0
        
        try:
            # Criar texto consolidado para embedding principal
            texto_principal = f"Título: {titulo}\n"
            if resumo:
                texto_principal += f"Resumo: {resumo}\n"
            if decisoes:
                texto_principal += f"Decisões: {', '.join(decisoes)}\n"
            
            # Gerar embedding principal da reunião
            embedding_principal = self.gerar_embedding(texto_principal)
            
            # Armazenar embedding principal
            self.supabase.client.table('meeting_embeddings').insert({
                'meeting_id': reuniao_id,
                'chunk_index': -1,  # -1 indica embedding principal
                'chunk_text': texto_principal[:500],  # Primeiros 500 chars
                'embedding': embedding_principal,
                'metadata': {
                    'tipo': 'principal',
                    'titulo': titulo,
                    'tem_resumo': bool(resumo),
                    'num_decisoes': len(decisoes) if decisoes else 0
                }
            }).execute()
            embeddings_criados += 1
            
            # Processar transcrição em chunks se existir
            if transcricao and len(transcricao) > self.chunk_size:
                chunks = self.processar_texto_em_chunks(
                    transcricao,
                    metadata={'tipo': 'transcricao', 'meeting_id': reuniao_id}
                )
                
                # Gerar e armazenar embeddings para cada chunk
                for chunk in chunks[:self.max_chunks_per_doc]:
                    embedding = self.gerar_embedding(chunk['text'])
                    
                    self.supabase.client.table('meeting_embeddings').insert({
                        'meeting_id': reuniao_id,
                        'chunk_index': chunk['chunk_id'],
                        'chunk_text': chunk['text'][:500],
                        'embedding': embedding,
                        'metadata': chunk['metadata']
                    }).execute()
                    embeddings_criados += 1
            
            logger.info(f"Criados {embeddings_criados} embeddings para reunião {reuniao_id}")
            return embeddings_criados
            
        except Exception as e:
            logger.error(f"Erro ao processar embeddings da reunião: {e}")
            raise RuntimeError(f"Falha ao processar embeddings: {e}")
    
    def buscar_por_similaridade(self, query: str, limite: int = 5, 
                               filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Busca documentos similares usando embeddings.
        
        Args:
            query: Texto de busca
            limite: Número máximo de resultados
            filtros: Filtros adicionais (ex: user_id, date_range)
            
        Returns:
            Lista de resultados ordenados por similaridade
        """
        try:
            # Gerar embedding da query
            query_embedding = self.gerar_embedding(query)
            
            # Preparar parâmetros para função RPC
            params = {
                'query_embedding': query_embedding,
                'match_count': limite
            }
            
            # Adicionar filtros se fornecidos
            if filtros:
                if 'user_id' in filtros:
                    params['user_filter'] = filtros['user_id']
                if 'start_date' in filtros:
                    params['start_date'] = filtros['start_date']
                if 'end_date' in filtros:
                    params['end_date'] = filtros['end_date']
            
            # Executar busca por similaridade
            response = self.supabase.client.rpc(
                'buscar_reunioes_similares',
                params
            ).execute()
            
            # Processar e retornar resultados
            resultados = []
            for item in response.data:
                resultado = {
                    'meeting_id': item['meeting_id'],
                    'chunk_text': item['chunk_text'],
                    'similarity': item['similarity'],
                    'metadata': item.get('metadata', {}),
                    'meeting_data': None
                }
                
                # Buscar dados completos da reunião
                meeting = self.supabase.buscar_reuniao_por_id(item['meeting_id'])
                if meeting:
                    resultado['meeting_data'] = meeting
                
                resultados.append(resultado)
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {e}")
            # Fallback para busca textual tradicional
            return self._busca_textual_fallback(query, limite, filtros)
    
    def _busca_textual_fallback(self, query: str, limite: int, 
                               filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback para busca textual quando busca vetorial falha."""
        logger.warning("Usando busca textual como fallback")
        
        # Extrair termos da query
        termos = query.lower().split()
        
        # Usar busca textual existente
        return self.supabase.buscar_reunioes_por_texto(
            termos_busca=termos,
            user_id=filtros.get('user_id') if filtros else None,
            limit=limite
        )
    
    def processar_base_conhecimento(self, doc_id: str, titulo: str, 
                                   conteudo: str, tipo: str = 'manual',
                                   departamento: str = None) -> int:
        """
        Processa documento da base de conhecimento para embeddings.
        
        Args:
            doc_id: ID do documento
            titulo: Título do documento
            conteudo: Conteúdo completo
            tipo: Tipo do documento (manual, procedimento, etc)
            departamento: Departamento relacionado
            
        Returns:
            Número de embeddings criados
        """
        embeddings_criados = 0
        
        try:
            # Processar conteúdo em chunks
            chunks = self.processar_texto_em_chunks(
                conteudo,
                metadata={
                    'tipo': tipo,
                    'departamento': departamento,
                    'doc_id': doc_id
                }
            )
            
            # Gerar e armazenar embeddings
            for chunk in chunks:
                embedding = self.gerar_embedding(chunk['text'])
                
                self.supabase.client.table('knowledge_embeddings').insert({
                    'doc_id': doc_id,
                    'chunk_index': chunk['chunk_id'],
                    'chunk_text': chunk['text'][:500],
                    'embedding': embedding,
                    'metadata': {
                        'titulo': titulo,
                        'tipo': tipo,
                        'departamento': departamento,
                        'chunk_metadata': chunk['metadata']
                    }
                }).execute()
                embeddings_criados += 1
            
            logger.info(f"Criados {embeddings_criados} embeddings para documento {doc_id}")
            return embeddings_criados
            
        except Exception as e:
            logger.error(f"Erro ao processar embeddings do documento: {e}")
            raise RuntimeError(f"Falha ao processar embeddings: {e}")
    
    def atualizar_embeddings_reunioes_existentes(self, limite: int = 100) -> Dict[str, int]:
        """
        Atualiza embeddings para reuniões existentes sem embeddings.
        
        Args:
            limite: Número máximo de reuniões para processar
            
        Returns:
            Estatísticas do processamento
        """
        stats = {
            'processadas': 0,
            'embeddings_criados': 0,
            'erros': 0
        }
        
        try:
            # Buscar reuniões sem embeddings
            reunioes = self.supabase.client.table('meetings').select(
                'id, title, transcription_full, transcription_summary, decisions'
            ).limit(limite).execute()
            
            for reuniao in reunioes.data:
                try:
                    # Verificar se já tem embeddings
                    existe = self.supabase.client.table('meeting_embeddings').select(
                        'id'
                    ).eq('meeting_id', reuniao['id']).limit(1).execute()
                    
                    if not existe.data:
                        # Processar embeddings
                        num_embeddings = self.processar_reuniao_para_embeddings(
                            reuniao_id=reuniao['id'],
                            titulo=reuniao.get('title', ''),
                            transcricao=reuniao.get('transcription_full', ''),
                            resumo=reuniao.get('transcription_summary'),
                            decisoes=reuniao.get('decisions', [])
                        )
                        stats['embeddings_criados'] += num_embeddings
                        stats['processadas'] += 1
                        
                except Exception as e:
                    logger.error(f"Erro ao processar reunião {reuniao['id']}: {e}")
                    stats['erros'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao atualizar embeddings: {e}")
            raise RuntimeError(f"Falha ao atualizar embeddings: {e}")