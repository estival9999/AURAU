"""
Teste Rápido de Performance do Sistema RAG
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hybrid_search_rag_test import HybridSearchRAG

load_dotenv()

def teste_rapido():
    """Executa teste rápido de performance"""
    # Inicializar
    print("🚀 Iniciando teste rápido de performance...")
    rag = HybridSearchRAG(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY"),
        os.getenv("OPENAI_API_KEY")
    )
    
    # Queries de teste
    queries = [
        "Como funciona o sistema AURALIS?",
        "validação CPF documentos",
        "cooperativa Pantaneta crédito"
    ]
    
    # Configurações principais
    configs = [
        {"nome": "Full-Text", "ft": 2.0, "sem": 0.2},
        {"nome": "Semântico", "ft": 0.2, "sem": 2.0},
        {"nome": "Híbrido", "ft": 0.8, "sem": 1.5}
    ]
    
    resultados = []
    
    print("\n📊 Executando testes...")
    for query in queries:
        print(f"\nQuery: '{query[:40]}...'")
        
        for config in configs:
            inicio = time.time()
            
            # Buscar
            results = rag.hybrid_search(
                query,
                match_count=3,
                full_text_weight=config["ft"],
                semantic_weight=config["sem"]
            )
            
            tempo_busca = time.time() - inicio
            
            # Calcular score médio
            scores = []
            for r in results:
                if isinstance(r, dict) and 'score' in r:
                    scores.append(float(r['score']))
            
            score_medio = sum(scores) / len(scores) if scores else 0
            
            print(f"  {config['nome']}: {len(results)} resultados, score médio: {score_medio:.4f}, tempo: {tempo_busca:.2f}s")
            
            resultados.append({
                "query": query[:40],
                "config": config["nome"],
                "num_resultados": len(results),
                "score_medio": score_medio,
                "tempo": tempo_busca
            })
    
    # Análise
    print("\n📈 RESUMO DOS RESULTADOS:")
    print("-"*50)
    
    # Melhor score por configuração
    scores_por_config = {}
    tempos_por_config = {}
    
    for r in resultados:
        config = r["config"]
        if config not in scores_por_config:
            scores_por_config[config] = []
            tempos_por_config[config] = []
        scores_por_config[config].append(r["score_medio"])
        tempos_por_config[config].append(r["tempo"])
    
    print("\n🏆 Média por Configuração:")
    for config in configs:
        nome = config["nome"]
        score_medio = sum(scores_por_config[nome]) / len(scores_por_config[nome])
        tempo_medio = sum(tempos_por_config[nome]) / len(tempos_por_config[nome])
        print(f"  {nome}:")
        print(f"    Score médio: {score_medio:.4f}")
        print(f"    Tempo médio: {tempo_medio:.2f}s")
    
    # Salvar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"teste_rapido_{timestamp}.json", 'w') as f:
        json.dump(resultados, f, indent=2)
    
    print(f"\n💾 Resultados salvos em: teste_rapido_{timestamp}.json")
    
    # Recomendação
    print("\n💡 RECOMENDAÇÃO:")
    print("Para melhor equilíbrio entre performance e qualidade,")
    print("use a configuração Híbrida (full_text=0.8, semantic=1.5)")

if __name__ == "__main__":
    teste_rapido()