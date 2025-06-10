"""
Sistema de teste para Busca Híbrida RAG com Supabase
Combina busca por palavras-chave (full-text) com busca semântica
"""

import os
from typing import List, Dict, Tuple, Optional
import numpy as np
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime
import time

# Carregar variáveis de ambiente
load_dotenv()

class HybridSearchRAG:
    def __init__(self, supabase_url: str, supabase_key: str, openai_api_key: str):
        """Inicializa o sistema de busca híbrida RAG"""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        self.chat_model = "gpt-4.1-mini"
        
    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding para um texto usando OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                dimensions=512  # Usando 512 dimensões para otimizar performance
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Erro ao gerar embedding: {e}")
            return []
    
    def add_document(self, content: str, metadata: Optional[Dict] = None) -> Dict:
        """Adiciona um documento ao banco com seu embedding"""
        embedding = self.generate_embedding(content)
        
        if not embedding:
            return {"error": "Falha ao gerar embedding"}
        
        # Converter embedding para formato PostgreSQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        try:
            # Chamar função SQL para inserir documento
            result = self.supabase.rpc(
                'insert_document_with_embedding',
                {
                    'doc_content': content,
                    'doc_embedding': embedding_str,
                    'doc_metadata': json.dumps(metadata) if metadata else None
                }
            ).execute()
            
            return {
                "success": True,
                "document_id": result.data,
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            }
        except Exception as e:
            return {"error": str(e)}
    
    def hybrid_search(
        self, 
        query: str, 
        match_count: int = 10,
        full_text_weight: float = 1.0,
        semantic_weight: float = 1.0
    ) -> List[Dict]:
        """Realiza busca híbrida combinando full-text e semântica"""
        # Gerar embedding da query
        query_embedding = self.generate_embedding(query)
        
        if not query_embedding:
            print("Erro ao gerar embedding da query")
            return []
        
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        try:
            # Executar busca híbrida
            results = self.supabase.rpc(
                'hybrid_search',
                {
                    'query_text': query,
                    'query_embedding': embedding_str,
                    'match_count': match_count,
                    'full_text_weight': full_text_weight,
                    'semantic_weight': semantic_weight
                }
            ).execute()
            
            return results.data
        except Exception as e:
            print(f"Erro na busca híbrida: {e}")
            return []
    
    def generate_rag_response(
        self, 
        query: str, 
        search_results: List[Dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """Gera resposta usando RAG com os resultados da busca"""
        if not search_results:
            return "Desculpe, não encontrei informações relevantes para responder sua pergunta."
        
        # Preparar contexto dos documentos encontrados
        context = "\n\n".join([
            f"Documento {i+1} (Score: {doc.get('score', 0):.3f}):\n{doc['content']}"
            for i, doc in enumerate(search_results[:5])  # Usar top 5 resultados
        ])
        
        # Prompt do sistema
        if not system_prompt:
            system_prompt = """Você é um assistente útil que responde perguntas baseando-se no contexto fornecido.
            Use apenas as informações do contexto para responder. Se a informação não estiver no contexto,
            diga que não tem essa informação disponível."""
        
        # Criar mensagens para o chat
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Contexto:\n{context}\n\nPergunta: {query}\n\nResponda com base no contexto fornecido."""}
        ]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao gerar resposta: {e}"
    
    def analyze_search_performance(self, query: str) -> Dict:
        """Analisa a performance dos diferentes tipos de busca"""
        query_embedding = self.generate_embedding(query)
        
        if not query_embedding:
            return {"error": "Falha ao gerar embedding"}
        
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        try:
            results = self.supabase.rpc(
                'analyze_search_performance',
                {
                    'query_text': query,
                    'query_embedding': embedding_str
                }
            ).execute()
            
            return {
                "analysis": results.data,
                "summary": self._summarize_performance(results.data)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _summarize_performance(self, performance_data: List[Dict]) -> str:
        """Cria um resumo da análise de performance"""
        summary = "Análise de Performance:\n"
        for item in performance_data:
            summary += f"\n- {item['search_type'].title()}: "
            summary += f"{item['result_count']} resultados em {item['execution_time']}"
        return summary
    
    def batch_add_documents(self, documents: List[Dict[str, any]]) -> List[Dict]:
        """Adiciona múltiplos documentos em lote"""
        results = []
        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            result = self.add_document(content, metadata)
            results.append(result)
            
            # Pequena pausa para evitar rate limiting
            time.sleep(0.1)
        
        return results


# Funções de teste e demonstração
def test_hybrid_search_system():
    """Função principal para testar o sistema de busca híbrida"""
    # Configurações (você precisa adicionar suas credenciais do Supabase)
    SUPABASE_URL = "YOUR_SUPABASE_URL"  # Substitua com sua URL
    SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"  # Substitua com sua chave
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Inicializar sistema
    rag_system = HybridSearchRAG(SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)
    
    # Exemplos de documentos para teste
    test_documents = [
        {
            "content": "Python é uma linguagem de programação de alto nível, interpretada e de propósito geral. É conhecida por sua sintaxe clara e legibilidade.",
            "metadata": {"category": "programming", "language": "pt-br"}
        },
        {
            "content": "Machine Learning é um subcampo da inteligência artificial que permite que sistemas aprendam e melhorem com experiência sem serem explicitamente programados.",
            "metadata": {"category": "ai", "language": "pt-br"}
        },
        {
            "content": "A busca híbrida combina busca por palavras-chave com busca semântica, oferecendo resultados mais precisos e contextuais.",
            "metadata": {"category": "search", "language": "pt-br"}
        },
        {
            "content": "PostgreSQL é um sistema de gerenciamento de banco de dados relacional objeto-relacional poderoso e de código aberto.",
            "metadata": {"category": "database", "language": "pt-br"}
        },
        {
            "content": "Vetores de embedding são representações numéricas de texto que capturam significado semântico em espaço multidimensional.",
            "metadata": {"category": "nlp", "language": "pt-br"}
        }
    ]
    
    print("=== Teste do Sistema de Busca Híbrida RAG ===\n")
    
    # 1. Adicionar documentos
    print("1. Adicionando documentos de teste...")
    add_results = rag_system.batch_add_documents(test_documents)
    for i, result in enumerate(add_results):
        if result.get("success"):
            print(f"   ✓ Documento {i+1} adicionado: ID {result['document_id']}")
        else:
            print(f"   ✗ Erro no documento {i+1}: {result.get('error')}")
    
    print("\n2. Testando diferentes tipos de busca...")
    
    # Queries de teste
    test_queries = [
        {
            "query": "o que é busca híbrida?",
            "weights": {"full_text": 1.0, "semantic": 1.0}
        },
        {
            "query": "programação e inteligência artificial",
            "weights": {"full_text": 0.3, "semantic": 1.5}
        },
        {
            "query": "banco de dados PostgreSQL",
            "weights": {"full_text": 1.5, "semantic": 0.5}
        }
    ]
    
    for test in test_queries:
        query = test["query"]
        weights = test["weights"]
        
        print(f"\n   Query: '{query}'")
        print(f"   Pesos: Full-text={weights['full_text']}, Semântico={weights['semantic']}")
        
        # Realizar busca híbrida
        results = rag_system.hybrid_search(
            query, 
            match_count=3,
            full_text_weight=weights['full_text'],
            semantic_weight=weights['semantic']
        )
        
        print(f"   Resultados encontrados: {len(results)}")
        for i, doc in enumerate(results[:3]):
            print(f"   {i+1}. Score: {doc.get('score', 0):.3f} - {doc['content'][:80]}...")
        
        # Gerar resposta RAG
        print("\n   Resposta RAG:")
        rag_response = rag_system.generate_rag_response(query, results)
        print(f"   {rag_response}")
        
        # Análise de performance
        print("\n   Análise de Performance:")
        perf_analysis = rag_system.analyze_search_performance(query)
        if "summary" in perf_analysis:
            print(f"   {perf_analysis['summary']}")
    
    print("\n=== Teste Concluído ===")


# Script para comparação de métodos de busca
def compare_search_methods():
    """Compara a eficácia dos diferentes métodos de busca"""
    print("\n=== Comparação de Métodos de Busca ===\n")
    
    comparisons = {
        "Busca Full-Text": {
            "vantagens": [
                "Rápida para palavras-chave exatas",
                "Ótima para termos técnicos específicos",
                "Baixo custo computacional"
            ],
            "desvantagens": [
                "Não entende contexto ou sinônimos",
                "Falha com erros de digitação",
                "Limitada a correspondências literais"
            ]
        },
        "Busca Semântica": {
            "vantagens": [
                "Entende significado e contexto",
                "Encontra conteúdo relacionado",
                "Funciona com sinônimos"
            ],
            "desvantagens": [
                "Mais cara computacionalmente",
                "Pode perder termos exatos importantes",
                "Requer embeddings pré-calculados"
            ]
        },
        "Busca Híbrida": {
            "vantagens": [
                "Combina precisão e contexto",
                "Flexível com pesos ajustáveis",
                "Melhor cobertura de resultados"
            ],
            "desvantagens": [
                "Mais complexa de implementar",
                "Requer ajuste fino dos pesos",
                "Custo computacional moderado"
            ]
        }
    }
    
    for method, details in comparisons.items():
        print(f"{method}:")
        print("  Vantagens:")
        for v in details["vantagens"]:
            print(f"    • {v}")
        print("  Desvantagens:")
        for d in details["desvantagens"]:
            print(f"    • {d}")
        print()


if __name__ == "__main__":
    # Executar teste do sistema
    test_hybrid_search_system()
    
    # Mostrar comparação de métodos
    compare_search_methods()