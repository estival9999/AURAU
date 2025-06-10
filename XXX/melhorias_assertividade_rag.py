"""
Melhorias de Assertividade para o Sistema RAG
Implementa técnicas avançadas para aumentar a precisão das respostas
"""

import os
import sys
from typing import List, Dict, Tuple
import re
from collections import Counter
import numpy as np
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hybrid_search_rag_test import HybridSearchRAG

load_dotenv()

class RAGAprimorado(HybridSearchRAG):
    """Versão aprimorada do sistema RAG com melhorias de assertividade"""
    
    def __init__(self, supabase_url: str, supabase_key: str, openai_api_key: str):
        super().__init__(supabase_url, supabase_key, openai_api_key)
        
        # Configurações avançadas
        self.MIN_SCORE_THRESHOLD = 0.01  # Score mínimo para considerar resultado
        self.MAX_CHUNK_DISTANCE = 3      # Distância máxima entre chunks relacionados
        self.CONTEXT_WINDOW_SIZE = 2     # Chunks adjacentes para contexto
        
    def preprocessar_query(self, query: str) -> Dict:
        """Pré-processa a query para melhor busca"""
        # Normalizar texto
        query_normalizada = query.lower().strip()
        
        # Extrair entidades importantes
        entidades = {
            "sistemas": ["auralis", "cadastro", "sistema"],
            "organizacoes": ["pantaneta", "cooperativa"],
            "documentos": ["cpf", "rg", "cep"],
            "processos": ["validação", "gravação", "reunião", "cadastramento"]
        }
        
        entidades_encontradas = []
        for categoria, termos in entidades.items():
            for termo in termos:
                if termo in query_normalizada:
                    entidades_encontradas.append((categoria, termo))
        
        # Identificar intenção
        intencao = "informacional"  # padrão
        if any(q in query_normalizada for q in ["como", "qual o processo", "quais os passos"]):
            intencao = "procedural"
        elif any(q in query_normalizada for q in ["por que", "qual o motivo", "causa"]):
            intencao = "explicativa"
        elif any(q in query_normalizada for q in ["problemas", "falhas", "erros", "dificuldades"]):
            intencao = "diagnostica"
        
        # Expandir query com sinônimos
        expansoes = {
            "auralis": ["auralis", "sistema de gravação", "gestão de reuniões"],
            "cadastro": ["cadastro", "registro", "cadastramento"],
            "validação": ["validação", "verificação", "conferência"],
            "cpf": ["cpf", "documento de identificação", "documento fiscal"]
        }
        
        query_expandida = query
        for termo, sinonimos in expansoes.items():
            if termo in query_normalizada:
                query_expandida += " " + " ".join(sinonimos)
        
        return {
            "original": query,
            "normalizada": query_normalizada,
            "expandida": query_expandida,
            "entidades": entidades_encontradas,
            "intencao": intencao
        }
    
    def buscar_com_contexto(self, query: str, match_count: int = 10) -> List[Dict]:
        """Busca aprimorada que considera contexto dos chunks"""
        # Pré-processar query
        query_info = self.preprocessar_query(query)
        
        # Ajustar pesos baseado na intenção
        if query_info["intencao"] == "procedural":
            full_text_weight = 1.0
            semantic_weight = 1.8
        elif query_info["intencao"] == "diagnostica":
            full_text_weight = 1.2
            semantic_weight = 1.5
        else:
            full_text_weight = 0.8
            semantic_weight = 1.5
        
        # Buscar com query expandida
        results = self.hybrid_search(
            query_info["expandida"],
            match_count=match_count * 2,  # Buscar mais para filtrar depois
            full_text_weight=full_text_weight,
            semantic_weight=semantic_weight
        )
        
        # Filtrar por score mínimo
        results_filtrados = []
        for r in results:
            if isinstance(r, dict) and r.get('score', 0) >= self.MIN_SCORE_THRESHOLD:
                results_filtrados.append(r)
        
        # Re-ranquear baseado em relevância das entidades
        if query_info["entidades"]:
            for result in results_filtrados:
                bonus = 0
                content = result.get('content', '').lower()
                
                # Bonus por entidades encontradas
                for categoria, entidade in query_info["entidades"]:
                    if entidade in content:
                        bonus += 0.01
                
                # Bonus por proximidade de termos
                palavras_query = set(query_info["normalizada"].split())
                palavras_content = set(content.split())
                overlap = len(palavras_query & palavras_content)
                bonus += overlap * 0.005
                
                # Aplicar bonus ao score
                if 'score' in result:
                    result['score'] = float(result['score']) + bonus
        
        # Reordenar por score
        results_filtrados.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Retornar top N
        return results_filtrados[:match_count]
    
    def gerar_resposta_aprimorada(
        self, 
        query: str, 
        results: List[Dict],
        include_confidence: bool = True
    ) -> Dict:
        """Gera resposta com indicadores de confiança"""
        if not results:
            return {
                "resposta": "Desculpe, não encontrei informações relevantes sobre esse tópico.",
                "confianca": 0.0,
                "sugestoes": []
            }
        
        # Analisar qualidade dos resultados
        scores = [r.get('score', 0) for r in results if isinstance(r, dict)]
        score_medio = np.mean(scores) if scores else 0
        score_maximo = max(scores) if scores else 0
        
        # Calcular confiança
        confianca = min(1.0, score_maximo * 10)  # Normalizar para 0-1
        
        # Prompt aprimorado baseado na confiança
        if confianca >= 0.7:
            system_prompt = """Você é um assistente especializado com acesso a documentos confiáveis.
            Responda com precisão e detalhes, pois as informações encontradas são altamente relevantes.
            Use bullet points e seja específico."""
        elif confianca >= 0.4:
            system_prompt = """Você é um assistente cuidadoso. As informações encontradas têm relevância moderada.
            Responda com base no contexto disponível, mas indique quando alguma informação não estiver 
            completamente clara ou completa."""
        else:
            system_prompt = """Você é um assistente cauteloso. As informações encontradas têm baixa relevância.
            Responda apenas com o que está claramente presente no contexto e indique as limitações
            das informações disponíveis."""
        
        # Gerar resposta
        resposta = self.generate_rag_response(query, results, system_prompt)
        
        # Gerar sugestões de perguntas relacionadas
        sugestoes = self.gerar_sugestoes(query, results)
        
        return {
            "resposta": resposta,
            "confianca": confianca,
            "score_medio": score_medio,
            "num_fontes": len(results),
            "sugestoes": sugestoes
        }
    
    def gerar_sugestoes(self, query: str, results: List[Dict]) -> List[str]:
        """Gera sugestões de perguntas relacionadas"""
        sugestoes = []
        
        # Extrair tópicos dos resultados
        topicos = set()
        for r in results[:3]:
            if isinstance(r, dict):
                content = r.get('content', '').lower()
                # Extrair palavras-chave importantes
                if "auralis" in content:
                    topicos.add("AURALIS")
                if "pantaneta" in content:
                    topicos.add("Cooperativa Pantaneta")
                if "cadastro" in content:
                    topicos.add("sistema de cadastro")
                if "validação" in content:
                    topicos.add("validação de dados")
        
        # Gerar sugestões baseadas nos tópicos
        templates = [
            "Quais são os benefícios de {}?",
            "Como melhorar o processo de {}?",
            "Quais são as melhores práticas para {}?",
            "Que problemas podem ocorrer com {}?"
        ]
        
        for topico in list(topicos)[:2]:  # Máximo 2 tópicos
            template = templates[len(sugestoes) % len(templates)]
            sugestoes.append(template.format(topico))
        
        return sugestoes[:3]  # Máximo 3 sugestões


class AssistenteRAGAprimorado:
    """Assistente com melhorias de assertividade"""
    
    def __init__(self):
        """Inicializa o assistente aprimorado"""
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        print("🚀 Inicializando Assistente RAG Aprimorado...")
        self.rag_system = RAGAprimorado(SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)
        self.historico = []
        self.contexto_conversa = []  # Manter contexto entre perguntas
        
    def processar_com_contexto(self, pergunta: str) -> Dict:
        """Processa pergunta considerando contexto da conversa"""
        # Adicionar contexto anterior se relevante
        query_contextualizada = pergunta
        if self.contexto_conversa and len(pergunta.split()) < 5:
            # Pergunta curta pode se referir ao contexto anterior
            contexto_recente = " ".join(self.contexto_conversa[-2:])
            query_contextualizada = f"{contexto_recente} {pergunta}"
        
        # Buscar com contexto aprimorado
        results = self.rag_system.buscar_com_contexto(query_contextualizada)
        
        # Gerar resposta aprimorada
        resultado = self.rag_system.gerar_resposta_aprimorada(pergunta, results)
        
        # Atualizar contexto
        if resultado["confianca"] >= 0.5:
            # Só adicionar ao contexto se a resposta for confiável
            self.contexto_conversa.append(pergunta)
            if len(self.contexto_conversa) > 5:
                self.contexto_conversa.pop(0)
        
        return resultado


# Funções de teste e demonstração
def demonstrar_melhorias():
    """Demonstra as melhorias de assertividade"""
    print("\n" + "="*60)
    print("🔬 DEMONSTRAÇÃO: Melhorias de Assertividade")
    print("="*60)
    
    assistente = AssistenteRAGAprimorado()
    
    # Queries de teste
    queries = [
        "Como funciona o AURALIS?",
        "Quais os problemas do sistema de cadastro?",
        "processo validação CPF",
        "E sobre os endereços?"  # Query contextual
    ]
    
    for query in queries:
        print(f"\n❓ Pergunta: '{query}'")
        print("-"*40)
        
        resultado = assistente.processar_com_contexto(query)
        
        print(f"📊 Confiança: {resultado['confianca']:.1%}")
        print(f"📈 Score médio: {resultado['score_medio']:.4f}")
        print(f"📚 Fontes consultadas: {resultado['num_fontes']}")
        
        print(f"\n🤖 Resposta:")
        print(resultado['resposta'][:300] + "..." if len(resultado['resposta']) > 300 else resultado['resposta'])
        
        if resultado['sugestoes']:
            print(f"\n💡 Perguntas relacionadas:")
            for sug in resultado['sugestoes']:
                print(f"   • {sug}")
        
        print("-"*40)


if __name__ == "__main__":
    demonstrar_melhorias()