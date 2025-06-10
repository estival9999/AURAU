#!/usr/bin/env python3
"""
Assistente RAG com Fallback para Busca Full-Text
Funciona mesmo quando a API do OpenAI está indisponível
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import json
import time

# Adicionar diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_search_rag_test import HybridSearchRAG

# Carregar variáveis de ambiente
load_dotenv()

class AssistenteRAGComFallback(HybridSearchRAG):
    def __init__(self, supabase_url: str, supabase_key: str, openai_api_key: str):
        super().__init__(supabase_url, supabase_key, openai_api_key)
        self.modo_fallback = False
        self.embeddings_cache = {}
        
    def generate_embedding(self, text: str):
        """Tenta gerar embedding com fallback para busca por palavras-chave"""
        # Verificar cache primeiro
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
            
        try:
            # Tentar gerar embedding normalmente
            embedding = super().generate_embedding(text)
            if embedding:
                self.embeddings_cache[text] = embedding
                return embedding
        except Exception as e:
            print(f"\n⚠️ API OpenAI indisponível: {str(e)}")
            print("🔄 Alternando para modo de busca por palavras-chave...")
            self.modo_fallback = True
            
        # Retornar vetor vazio para forçar busca full-text
        return [0.0] * 512
    
    def buscar_apenas_fulltext(self, query: str, match_count: int = 5):
        """Busca usando apenas full-text quando API está indisponível"""
        print("📝 Usando busca por palavras-chave (sem busca semântica)...")
        
        try:
            # Executar query SQL diretamente para busca full-text
            query_sql = """
            SELECT id, content, metadata, 
                   ts_rank(fts, plainto_tsquery('portuguese', %s)) as score
            FROM documents
            WHERE fts @@ plainto_tsquery('portuguese', %s)
            ORDER BY score DESC
            LIMIT %s
            """
            
            response = self.supabase.rpc(
                'execute_sql',
                {
                    'query': query_sql,
                    'params': [query, query, match_count]
                }
            ).execute()
            
            if response.data:
                return response.data
        except:
            # Se falhar, tentar método alternativo
            pass
            
        # Método alternativo: buscar por substring
        try:
            response = self.supabase.table('documents').select(
                'id', 'content', 'metadata'
            ).ilike('content', f'%{query}%').limit(match_count).execute()
            
            if response.data:
                # Adicionar score baseado em ocorrências
                for item in response.data:
                    content_lower = item['content'].lower()
                    query_lower = query.lower()
                    score = content_lower.count(query_lower) / len(content_lower) * 100
                    item['score'] = score
                    
                # Ordenar por score
                response.data.sort(key=lambda x: x['score'], reverse=True)
                return response.data
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            
        return []
    
    def hybrid_search(self, query: str, match_count: int = 5, 
                     full_text_weight: float = 1.0, 
                     semantic_weight: float = 1.0):
        """Busca híbrida com fallback para full-text apenas"""
        if self.modo_fallback:
            return self.buscar_apenas_fulltext(query, match_count)
        else:
            try:
                return super().hybrid_search(
                    query, match_count, full_text_weight, semantic_weight
                )
            except Exception as e:
                print(f"\n⚠️ Erro na busca híbrida: {e}")
                print("🔄 Tentando busca por palavras-chave...")
                self.modo_fallback = True
                return self.buscar_apenas_fulltext(query, match_count)
    
    def generate_rag_response(self, query: str, search_results, 
                            system_prompt: str = None):
        """Gera resposta com fallback para resposta baseada em template"""
        if not search_results:
            return "Desculpe, não encontrei informações sobre isso na base de conhecimento."
            
        if self.modo_fallback:
            # Resposta simplificada sem GPT
            print("📄 Gerando resposta sem IA (modo economia)...")
            
            resposta = f"Encontrei {len(search_results)} documento(s) relacionado(s) a '{query}':\n\n"
            
            for i, doc in enumerate(search_results[:3], 1):
                content = doc.get('content', '')
                # Extrair trecho relevante
                palavras_query = query.lower().split()
                
                # Encontrar primeira ocorrência de palavra da query
                inicio = 0
                for palavra in palavras_query:
                    pos = content.lower().find(palavra)
                    if pos != -1:
                        inicio = max(0, pos - 100)
                        break
                
                trecho = content[inicio:inicio + 300]
                if inicio > 0:
                    trecho = "..." + trecho
                if inicio + 300 < len(content):
                    trecho = trecho + "..."
                    
                resposta += f"{i}. {trecho}\n\n"
            
            # Adicionar contexto sobre o ponto focal se for a query
            if "ponto focal" in query.lower():
                resposta += "\n💡 Informação encontrada: "
                for doc in search_results:
                    content = doc.get('content', '').lower()
                    if "ponto focal" in content:
                        # Extrair contexto ao redor de "ponto focal"
                        pos = content.find("ponto focal")
                        if pos != -1:
                            inicio = max(0, pos - 50)
                            fim = min(len(content), pos + 100)
                            contexto = doc['content'][inicio:fim]
                            resposta += f"\n'{contexto}'"
                            break
            
            return resposta
        else:
            try:
                return super().generate_rag_response(query, search_results, system_prompt)
            except Exception as e:
                print(f"\n⚠️ Erro ao gerar resposta com IA: {e}")
                self.modo_fallback = True
                return self.generate_rag_response(query, search_results, system_prompt)


class AssistenteFallback:
    def __init__(self):
        """Inicializa o assistente com fallback"""
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        print("🤖 Inicializando Assistente RAG com Fallback...")
        self.rag_system = AssistenteRAGComFallback(SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)
        self.historico = []
        
    def processar_pergunta(self, pergunta):
        """Processa uma pergunta com fallback automático"""
        # Buscar documentos
        print("\n🔍 Buscando informações...")
        
        # Sempre tentar busca híbrida primeiro
        results = self.rag_system.hybrid_search(
            pergunta,
            match_count=5,
            full_text_weight=1.5,  # Mais peso para full-text no fallback
            semantic_weight=0.5
        )
        
        if not results:
            return {
                "resposta": "Desculpe, não encontrei informações sobre isso.",
                "fontes": [],
                "documentos": 0,
                "modo": "nenhum resultado"
            }
        
        print(f"✅ Encontrei {len(results)} documentos relevantes")
        
        # Gerar resposta
        if self.rag_system.modo_fallback:
            print("💭 Processando resposta (modo economia)...")
        else:
            print("💭 Processando resposta com IA...")
        
        resposta = self.rag_system.generate_rag_response(pergunta, results)
        
        # Extrair fontes
        fontes = []
        for doc in results[:3]:
            if isinstance(doc, dict):
                metadata = doc.get('metadata', {})
                if isinstance(metadata, dict):
                    fonte = metadata.get('fonte', 'Documento')
                    chunk = metadata.get('chunk_number', '?')
                    fontes.append(f"{fonte} - Seção {chunk}")
        
        return {
            "resposta": resposta,
            "fontes": list(set(fontes)),
            "documentos": len(results),
            "modo": "fallback" if self.rag_system.modo_fallback else "híbrido"
        }
    
    def chat_interativo(self):
        """Interface de chat com indicação do modo"""
        print("\n" + "="*70)
        print("💬 ASSISTENTE RAG - COM FALLBACK AUTOMÁTICO")
        print("="*70)
        
        print("\n⚡ Este assistente funciona mesmo sem acesso à API OpenAI!")
        print("   • Modo Híbrido: Busca completa com IA")
        print("   • Modo Fallback: Busca por palavras-chave")
        
        print("\n📚 Base de Conhecimento:")
        print("   • Manual AURALIS")
        print("   • Manual Cooperativa Pantaneta")
        print("   • Sistema de Cadastro")
        
        print("\n" + "-"*70)
        
        while True:
            try:
                print("\n❓ Sua pergunta:")
                pergunta = input(">>> ").strip()
                
                if pergunta.lower() in ['sair', 'exit', 'quit', 'q']:
                    print("\n👋 Até logo!")
                    break
                
                if not pergunta:
                    continue
                
                # Processar
                resultado = self.processar_pergunta(pergunta)
                
                # Exibir resposta
                print("\n" + "="*70)
                modo = resultado['modo']
                if modo == "fallback":
                    print("🤖 RESPOSTA (Modo Economia - Sem IA):")
                else:
                    print("🤖 RESPOSTA:")
                print("="*70)
                print(resultado["resposta"])
                print("="*70)
                
                # Metadados
                print(f"\n📊 Informações:")
                print(f"   • Modo: {modo}")
                print(f"   • Documentos analisados: {resultado['documentos']}")
                if resultado["fontes"]:
                    print(f"   • Fontes:")
                    for fonte in resultado["fontes"]:
                        print(f"     - {fonte}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrompido")
                break
            except Exception as e:
                print(f"\n❌ Erro: {str(e)}")


def main():
    """Função principal"""
    try:
        assistente = AssistenteFallback()
        assistente.chat_interativo()
    except Exception as e:
        print(f"❌ Erro ao inicializar: {str(e)}")


if __name__ == "__main__":
    main()