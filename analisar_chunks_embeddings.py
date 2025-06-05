#!/usr/bin/env python3
"""
Script para analisar os chunks na tabela knowledge_embeddings
e verificar se há repetições ou problemas de segmentação
"""

import os
import sys
from collections import Counter
from typing import List, Dict, Any
import logging
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.supabase_handler import SupabaseHandler
from difflib import SequenceMatcher

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalisadorChunks:
    """Analisa chunks de texto para detectar problemas de segmentação"""
    
    def __init__(self):
        self.supabase = SupabaseHandler()
        
    def listar_primeiros_chunks(self, documento_id: str = None, limite: int = 15) -> List[Dict]:
        """Lista os primeiros chunks com detalhes"""
        try:
            query = self.supabase.client.table('knowledge_embeddings').select(
                'id, doc_id, chunk_index, chunk_text'
            )
            
            if documento_id:
                query = query.eq('doc_id', documento_id)
                
            query = query.order('doc_id').order('chunk_index').limit(limite)
            
            response = query.execute()
            chunks = response.data or []
            
            # Adicionar tamanho do chunk calculado
            for chunk in chunks:
                chunk['chunk_size'] = len(chunk['chunk_text']) if chunk['chunk_text'] else 0
            
            return chunks
            
        except Exception as e:
            logger.error(f"Erro ao listar chunks: {e}")
            return []
    
    def analisar_repeticoes(self, documento_id: str = None) -> Dict[str, Any]:
        """Analisa repetições e sobreposições nos chunks"""
        try:
            # Buscar todos os chunks
            query = self.supabase.client.table('knowledge_embeddings').select(
                'id, doc_id, chunk_index, chunk_text'
            )
            
            if documento_id:
                query = query.eq('doc_id', documento_id)
            
            response = query.execute()
            chunks = response.data or []
            
            # Adicionar tamanho do chunk calculado
            for chunk in chunks:
                chunk['chunk_size'] = len(chunk['chunk_text']) if chunk['chunk_text'] else 0
            
            logger.info(f"Total de chunks encontrados: {len(chunks)}")
            
            # Análise de repetições
            analise = {
                'total_chunks': len(chunks),
                'chunks_identicos': [],
                'chunks_similares': [],
                'estatisticas_tamanho': {},
                'sobreposicoes': []
            }
            
            # Agrupar por documento
            chunks_por_doc = {}
            for chunk in chunks:
                doc_id = chunk['doc_id']
                if doc_id not in chunks_por_doc:
                    chunks_por_doc[doc_id] = []
                chunks_por_doc[doc_id].append(chunk)
            
            # Ordenar chunks por índice dentro de cada documento
            for doc_id in chunks_por_doc:
                chunks_por_doc[doc_id].sort(key=lambda x: x['chunk_index'])
            
            # Análise por documento
            for doc_id, doc_chunks in chunks_por_doc.items():
                logger.info(f"\nAnalisando documento {doc_id}: {len(doc_chunks)} chunks")
                
                # Verificar chunks idênticos
                textos_vistos = {}
                for i, chunk in enumerate(doc_chunks):
                    texto = chunk['chunk_text']
                    if texto in textos_vistos:
                        analise['chunks_identicos'].append({
                            'documento': doc_id,
                            'indices': [textos_vistos[texto], chunk['chunk_index']],
                            'texto_preview': texto[:100] + '...' if len(texto) > 100 else texto
                        })
                    else:
                        textos_vistos[texto] = chunk['chunk_index']
                
                # Verificar sobreposições entre chunks consecutivos
                for i in range(len(doc_chunks) - 1):
                    chunk_atual = doc_chunks[i]['chunk_text']
                    chunk_proximo = doc_chunks[i + 1]['chunk_text']
                    
                    # Calcular similaridade
                    similarity = SequenceMatcher(None, chunk_atual, chunk_proximo).ratio()
                    
                    if similarity > 0.3:  # 30% de similaridade
                        # Encontrar a sobreposição exata
                        sobreposicao = self._encontrar_sobreposicao(chunk_atual, chunk_proximo)
                        
                        analise['sobreposicoes'].append({
                            'documento': doc_id,
                            'chunks': [doc_chunks[i]['chunk_index'], doc_chunks[i + 1]['chunk_index']],
                            'similaridade': round(similarity * 100, 2),
                            'tamanho_sobreposicao': len(sobreposicao),
                            'preview_sobreposicao': sobreposicao[:100] + '...' if len(sobreposicao) > 100 else sobreposicao
                        })
            
            # Estatísticas de tamanho
            tamanhos = [chunk['chunk_size'] for chunk in chunks]
            if tamanhos:
                analise['estatisticas_tamanho'] = {
                    'min': min(tamanhos),
                    'max': max(tamanhos),
                    'media': sum(tamanhos) / len(tamanhos),
                    'total_caracteres': sum(tamanhos)
                }
            
            return analise
            
        except Exception as e:
            logger.error(f"Erro na análise de repetições: {e}")
            return {}
    
    def _encontrar_sobreposicao(self, texto1: str, texto2: str) -> str:
        """Encontra a parte do texto que se sobrepõe entre dois chunks"""
        # Procurar o final de texto1 no início de texto2
        max_overlap = min(len(texto1), len(texto2))
        
        for i in range(max_overlap, 0, -1):
            if texto1[-i:] == texto2[:i]:
                return texto1[-i:]
        
        return ""
    
    def recuperar_documento_original(self, documento_id: str) -> Dict[str, Any]:
        """Recupera o documento original da knowledge_base"""
        try:
            response = self.supabase.client.table('knowledge_base').select(
                'id, title, content_full, content_summary'
            ).eq('id', documento_id).execute()
            
            if response.data:
                doc = response.data[0]
                return {
                    'id': doc['id'],
                    'titulo': doc['title'],
                    'tamanho_completo': len(doc['content_full']) if doc['content_full'] else 0,
                    'resumo': doc['content_summary'][:200] + '...' if doc['content_summary'] and len(doc['content_summary']) > 200 else doc['content_summary'],
                    'preview_conteudo': doc['content_full'][:500] + '...' if doc['content_full'] and len(doc['content_full']) > 500 else doc['content_full']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar documento: {e}")
            return None
    
    def gerar_relatorio_completo(self):
        """Gera relatório completo da análise"""
        print("\n" + "="*80)
        print("ANÁLISE DE CHUNKS NA TABELA KNOWLEDGE_EMBEDDINGS")
        print("="*80)
        
        # 1. Listar primeiros chunks
        print("\n📋 PRIMEIROS 15 CHUNKS:")
        print("-"*80)
        
        chunks = self.listar_primeiros_chunks(limite=15)
        
        if not chunks:
            print("❌ Nenhum chunk encontrado na tabela!")
            return
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk #{i}:")
            print(f"  ID: {chunk['id']}")
            print(f"  Documento: {chunk['doc_id']}")
            print(f"  Índice: {chunk['chunk_index']}")
            print(f"  Tamanho: {chunk['chunk_size']} caracteres")
            print(f"  Preview: {chunk['chunk_text'][:150]}...")
            
        # 2. Análise de repetições
        print("\n\n📊 ANÁLISE DE REPETIÇÕES E SOBREPOSIÇÕES:")
        print("-"*80)
        
        analise = self.analisar_repeticoes()
        
        print(f"\nTotal de chunks: {analise.get('total_chunks', 0)}")
        
        if analise.get('estatisticas_tamanho'):
            stats = analise['estatisticas_tamanho']
            print(f"\nEstatísticas de tamanho:")
            print(f"  - Menor chunk: {stats['min']} caracteres")
            print(f"  - Maior chunk: {stats['max']} caracteres")
            print(f"  - Média: {stats['media']:.2f} caracteres")
            print(f"  - Total de caracteres: {stats['total_caracteres']:,}")
        
        if analise.get('chunks_identicos'):
            print(f"\n⚠️  CHUNKS IDÊNTICOS ENCONTRADOS: {len(analise['chunks_identicos'])}")
            for item in analise['chunks_identicos'][:5]:  # Mostrar apenas os 5 primeiros
                print(f"  - Documento {item['documento']}, índices {item['indices']}")
                print(f"    Preview: {item['texto_preview']}")
        
        if analise.get('sobreposicoes'):
            print(f"\n🔄 SOBREPOSIÇÕES ENCONTRADAS: {len(analise['sobreposicoes'])}")
            
            # Ordenar por similaridade
            sobreposicoes_ordenadas = sorted(
                analise['sobreposicoes'], 
                key=lambda x: x['similaridade'], 
                reverse=True
            )
            
            for item in sobreposicoes_ordenadas[:10]:  # Top 10 sobreposições
                print(f"\n  - Documento {item['documento']}, chunks {item['chunks']}")
                print(f"    Similaridade: {item['similaridade']}%")
                print(f"    Tamanho da sobreposição: {item['tamanho_sobreposicao']} caracteres")
                print(f"    Preview: {item['preview_sobreposicao']}")
        
        # 3. Comparar com documento original
        print("\n\n📄 COMPARAÇÃO COM DOCUMENTOS ORIGINAIS:")
        print("-"*80)
        
        # Pegar IDs únicos de documentos
        doc_ids = list(set(chunk['doc_id'] for chunk in chunks))
        
        for doc_id in doc_ids[:3]:  # Analisar os 3 primeiros documentos
            doc_original = self.recuperar_documento_original(doc_id)
            
            if doc_original:
                print(f"\nDocumento: {doc_original['titulo']}")
                print(f"  ID: {doc_original['id']}")
                print(f"  Tamanho original: {doc_original['tamanho_completo']:,} caracteres")
                print(f"  Resumo: {doc_original['resumo']}")
                
                # Contar chunks deste documento
                chunks_doc = [c for c in chunks if c['doc_id'] == doc_id]
                print(f"  Total de chunks gerados: {len(chunks_doc)}")
                
                if chunks_doc and doc_original['tamanho_completo'] > 0:
                    taxa_expansao = (sum(c['chunk_size'] for c in chunks_doc) / doc_original['tamanho_completo']) * 100
                    print(f"  Taxa de expansão: {taxa_expansao:.1f}% (devido ao overlap)")
                    
                    # Análise detalhada do problema
                    print(f"\n  🔍 ANÁLISE DETALHADA DOS CHUNKS:")
                    print(f"  Preview do documento original (últimos 500 chars):")
                    if doc_original['tamanho_completo'] > 500:
                        print(f"  ...{doc_original['preview_conteudo'][-500:]}")
                    else:
                        print(f"  {doc_original['preview_conteudo']}")
                    
                    # Mostrar chunks problemáticos
                    chunks_repetidos = [c for c in chunks_doc if c['chunk_index'] >= 7]
                    if chunks_repetidos:
                        print(f"\n  ⚠️  PROBLEMA DETECTADO: {len(chunks_repetidos)} chunks idênticos!")
                        print(f"  Conteúdo repetido: '{chunks_repetidos[0]['chunk_text'][:100]}...'")
                        print(f"  Tamanho do conteúdo repetido: {chunks_repetidos[0]['chunk_size']} caracteres")
                        print(f"  Chunks afetados: índices {min(c['chunk_index'] for c in chunks_repetidos)} a {max(c['chunk_index'] for c in chunks_repetidos)}")


def main():
    """Função principal"""
    print("🔍 Iniciando análise de chunks...")
    
    analisador = AnalisadorChunks()
    
    # Verificar conexão
    if not analisador.supabase.testar_conexao():
        print("❌ Erro: Não foi possível conectar ao Supabase!")
        return
    
    # Gerar relatório completo
    analisador.gerar_relatorio_completo()
    
    print("\n\n✅ Análise concluída!")
    print("="*80)


if __name__ == "__main__":
    main()