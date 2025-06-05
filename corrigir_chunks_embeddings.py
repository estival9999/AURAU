#!/usr/bin/env python3
"""
Script para corrigir os chunks repetidos na tabela knowledge_embeddings
Reprocessa o documento com algoritmo corrigido
"""

import os
import sys
from typing import List, Dict, Any
import logging

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.supabase_handler import SupabaseHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def processar_texto_em_chunks_corrigido(texto: str, chunk_size: int = 500, 
                                       chunk_overlap: int = 100) -> List[Dict[str, Any]]:
    """
    Versão corrigida do processamento de chunks que evita repetições.
    
    Args:
        texto: Texto completo para dividir
        chunk_size: Tamanho de cada chunk
        chunk_overlap: Sobreposição entre chunks
        
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
    posicoes_usadas = set()  # Para rastrear posições já processadas
    
    while inicio < len(texto_limpo):
        # Definir fim do chunk
        fim = min(inicio + chunk_size, len(texto_limpo))
        
        # Tentar quebrar em espaço para não cortar palavras
        if fim < len(texto_limpo):
            ultimo_espaco = texto_limpo.rfind(' ', inicio, fim)
            if ultimo_espaco > inicio:
                fim = ultimo_espaco
        
        # Extrair chunk
        chunk_texto = texto_limpo[inicio:fim].strip()
        
        # Verificar se é um chunk novo (não repetido)
        if chunk_texto and (inicio, fim) not in posicoes_usadas:
            chunk_data = {
                'chunk_id': chunk_id,
                'text': chunk_texto,
                'start_char': inicio,
                'end_char': fim
            }
            chunks.append(chunk_data)
            posicoes_usadas.add((inicio, fim))
            chunk_id += 1
        
        # Calcular próximo início
        proximo_inicio = fim - chunk_overlap
        
        # CORREÇÃO: Se o próximo início não avança, forçar avanço
        if proximo_inicio <= inicio:
            proximo_inicio = fim
        
        # CORREÇÃO: Se chegamos ao final do texto, parar
        if fim >= len(texto_limpo):
            break
            
        inicio = proximo_inicio
    
    return chunks


def reprocessar_documento(doc_id: str):
    """Reprocessa um documento específico com o algoritmo corrigido"""
    
    supabase = SupabaseHandler()
    
    logger.info(f"Reprocessando documento {doc_id}...")
    
    try:
        # 1. Buscar documento original
        response = supabase.client.table('knowledge_base').select(
            'id, title, content_full'
        ).eq('id', doc_id).execute()
        
        if not response.data:
            logger.error(f"Documento {doc_id} não encontrado!")
            return
        
        doc = response.data[0]
        conteudo = doc['content_full']
        titulo = doc['title']
        
        logger.info(f"Documento: {titulo}")
        logger.info(f"Tamanho: {len(conteudo)} caracteres")
        
        # 2. Deletar chunks antigos
        logger.info("Deletando chunks antigos...")
        delete_response = supabase.client.table('knowledge_embeddings').delete().eq(
            'doc_id', doc_id
        ).execute()
        
        # 3. Criar novos chunks com algoritmo corrigido
        logger.info("Criando novos chunks...")
        chunks = processar_texto_em_chunks_corrigido(
            conteudo, 
            chunk_size=500,  # Tamanho menor para demonstração
            chunk_overlap=100
        )
        
        logger.info(f"Total de chunks gerados: {len(chunks)}")
        
        # 4. Inserir novos chunks (sem embeddings por enquanto)
        for chunk in chunks:
            # Preparar dados para inserção
            chunk_data = {
                'doc_id': doc_id,
                'chunk_index': chunk['chunk_id'],
                'chunk_text': chunk['text'],
                'metadata': {
                    'titulo': titulo,
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char']
                }
            }
            
            # Inserir chunk
            supabase.client.table('knowledge_embeddings').insert(chunk_data).execute()
        
        logger.info("✅ Reprocessamento concluído!")
        
        # 5. Verificar resultado
        verificar_chunks_documento(doc_id)
        
    except Exception as e:
        logger.error(f"Erro no reprocessamento: {e}")
        raise


def verificar_chunks_documento(doc_id: str):
    """Verifica os chunks após reprocessamento"""
    
    supabase = SupabaseHandler()
    
    # Buscar chunks do documento
    response = supabase.client.table('knowledge_embeddings').select(
        'chunk_index, chunk_text'
    ).eq('doc_id', doc_id).order('chunk_index').execute()
    
    chunks = response.data or []
    
    print(f"\n📊 VERIFICAÇÃO DOS CHUNKS REPROCESSADOS:")
    print(f"Total de chunks: {len(chunks)}")
    print("\nPrimeiros 5 chunks:")
    
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nChunk {chunk['chunk_index']}:")
        print(f"  Preview: {chunk['chunk_text'][:100]}...")
        print(f"  Tamanho: {len(chunk['chunk_text'])} caracteres")
    
    # Verificar se há repetições
    textos = [c['chunk_text'] for c in chunks]
    textos_unicos = set(textos)
    
    if len(textos) != len(textos_unicos):
        print(f"\n⚠️  AINDA HÁ REPETIÇÕES: {len(textos) - len(textos_unicos)} chunks idênticos")
    else:
        print("\n✅ Sem chunks idênticos!")
    
    # Verificar sobreposições
    print("\n🔍 Análise de sobreposições:")
    for i in range(min(3, len(chunks) - 1)):
        chunk_atual = chunks[i]['chunk_text']
        chunk_proximo = chunks[i + 1]['chunk_text']
        
        # Encontrar sobreposição
        sobreposicao = ""
        for j in range(min(len(chunk_atual), len(chunk_proximo))):
            if chunk_atual[-j:] == chunk_proximo[:j]:
                sobreposicao = chunk_atual[-j:]
        
        if sobreposicao:
            print(f"  Chunks {i} e {i+1}: {len(sobreposicao)} caracteres de sobreposição")


def main():
    """Função principal"""
    print("🔧 Script de Correção de Chunks Repetidos")
    print("="*60)
    
    # Documento problemático identificado
    doc_id = "e98bd2fe-beaa-428f-b6c6-5963f229e08a"
    
    # Verificar conexão
    supabase = SupabaseHandler()
    if not supabase.testar_conexao():
        print("❌ Erro: Não foi possível conectar ao Supabase!")
        return
    
    # Reprocessar documento
    reprocessar_documento(doc_id)
    
    print("\n✅ Processo concluído!")


if __name__ == "__main__":
    main()