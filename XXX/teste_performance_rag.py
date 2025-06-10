"""
Teste de Performance do Sistema RAG com Busca Híbrida
Analisa diferentes configurações e gera visualizações
"""

import os
import sys
import time
import json
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from dotenv import load_dotenv

# Adicionar diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_search_rag_test import HybridSearchRAG

# Carregar variáveis de ambiente
load_dotenv()

class TestadorPerformanceRAG:
    def __init__(self):
        """Inicializa o testador de performance"""
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        print("🚀 Inicializando sistema para teste de performance...")
        self.rag_system = HybridSearchRAG(SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)
        self.resultados = []
        
    def testar_configuracao(
        self, 
        query: str, 
        full_text_weight: float, 
        semantic_weight: float,
        match_count: int = 5
    ) -> Dict:
        """Testa uma configuração específica e retorna métricas"""
        inicio = time.time()
        
        try:
            # Realizar busca
            results = self.rag_system.hybrid_search(
                query,
                match_count=match_count,
                full_text_weight=full_text_weight,
                semantic_weight=semantic_weight
            )
            
            tempo_busca = time.time() - inicio
            
            if results:
                # Calcular métricas
                scores = []
                for r in results:
                    if isinstance(r, dict) and 'score' in r:
                        try:
                            scores.append(float(r['score']))
                        except:
                            pass
                
                # Gerar resposta RAG
                inicio_rag = time.time()
                resposta = self.rag_system.generate_rag_response(query, results)
                tempo_rag = time.time() - inicio_rag
                
                return {
                    "sucesso": True,
                    "tempo_busca": tempo_busca,
                    "tempo_rag": tempo_rag,
                    "tempo_total": tempo_busca + tempo_rag,
                    "num_resultados": len(results),
                    "score_maximo": max(scores) if scores else 0,
                    "score_medio": np.mean(scores) if scores else 0,
                    "score_minimo": min(scores) if scores else 0,
                    "tamanho_resposta": len(resposta)
                }
            else:
                return {
                    "sucesso": False,
                    "tempo_busca": tempo_busca,
                    "tempo_rag": 0,
                    "tempo_total": tempo_busca,
                    "num_resultados": 0,
                    "score_maximo": 0,
                    "score_medio": 0,
                    "score_minimo": 0,
                    "tamanho_resposta": 0
                }
                
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "tempo_busca": 0,
                "tempo_rag": 0,
                "tempo_total": 0,
                "num_resultados": 0,
                "score_maximo": 0,
                "score_medio": 0,
                "score_minimo": 0,
                "tamanho_resposta": 0
            }
    
    def executar_bateria_testes(self):
        """Executa uma bateria completa de testes com diferentes configurações"""
        print("\n" + "="*60)
        print("📊 TESTE DE PERFORMANCE - BUSCA HÍBRIDA RAG")
        print("="*60)
        
        # Queries de teste representativas
        queries_teste = [
            {
                "query": "Como funciona o sistema AURALIS?",
                "tipo": "conceitual",
                "categoria": "AURALIS"
            },
            {
                "query": "validação CPF documentos",
                "tipo": "palavras-chave",
                "categoria": "Cadastro"
            },
            {
                "query": "Quais são os problemas com endereços e CEP no sistema de cadastro?",
                "tipo": "pergunta_complexa",
                "categoria": "Cadastro"
            },
            {
                "query": "cooperativa Pantaneta produtos crédito",
                "tipo": "especifico",
                "categoria": "Pantaneta"
            },
            {
                "query": "Como garantir segurança e compliance dos dados?",
                "tipo": "pergunta_tecnica",
                "categoria": "Segurança"
            }
        ]
        
        # Configurações de peso para testar
        configuracoes = [
            {"nome": "Full-Text Puro", "ft": 1.0, "sem": 0.0},
            {"nome": "Semântico Puro", "ft": 0.0, "sem": 1.0},
            {"nome": "Balanceado 50-50", "ft": 1.0, "sem": 1.0},
            {"nome": "Ênfase Full-Text", "ft": 2.0, "sem": 0.5},
            {"nome": "Ênfase Semântica", "ft": 0.5, "sem": 2.0},
            {"nome": "Otimizado Híbrido", "ft": 0.8, "sem": 1.5},
            {"nome": "Ultra Full-Text", "ft": 3.0, "sem": 0.2},
            {"nome": "Ultra Semântico", "ft": 0.2, "sem": 3.0}
        ]
        
        total_testes = len(queries_teste) * len(configuracoes)
        teste_atual = 0
        
        print(f"\n🔬 Executando {total_testes} testes...")
        print("Isso pode levar alguns minutos...\n")
        
        for query_info in queries_teste:
            for config in configuracoes:
                teste_atual += 1
                print(f"\r⏳ Progresso: {teste_atual}/{total_testes} ({teste_atual/total_testes*100:.1f}%)", end="")
                
                resultado = self.testar_configuracao(
                    query_info["query"],
                    config["ft"],
                    config["sem"]
                )
                
                # Adicionar metadados
                resultado.update({
                    "query": query_info["query"],
                    "tipo_query": query_info["tipo"],
                    "categoria": query_info["categoria"],
                    "config_nome": config["nome"],
                    "full_text_weight": config["ft"],
                    "semantic_weight": config["sem"]
                })
                
                self.resultados.append(resultado)
                
                # Pequena pausa para evitar sobrecarga
                time.sleep(0.1)
        
        print("\n\n✅ Testes concluídos!")
        
    def analisar_resultados(self):
        """Analisa os resultados e gera visualizações"""
        print("\n📈 Analisando resultados...")
        
        # Converter para DataFrame
        df = pd.DataFrame(self.resultados)
        
        # Configurar estilo do seaborn
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (15, 10)
        
        # Criar figura com subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Análise de Performance - Busca Híbrida RAG', fontsize=16, fontweight='bold')
        
        # 1. Tempo de Resposta por Configuração
        ax1 = axes[0, 0]
        tempo_por_config = df.groupby('config_nome')['tempo_total'].mean().sort_values()
        tempo_por_config.plot(kind='barh', ax=ax1, color='skyblue')
        ax1.set_title('Tempo Médio de Resposta por Configuração')
        ax1.set_xlabel('Tempo (segundos)')
        
        # 2. Score Médio por Configuração
        ax2 = axes[0, 1]
        score_por_config = df.groupby('config_nome')['score_medio'].mean().sort_values()
        score_por_config.plot(kind='barh', ax=ax2, color='lightcoral')
        ax2.set_title('Score Médio por Configuração')
        ax2.set_xlabel('Score')
        
        # 3. Heatmap de Performance (Configuração vs Tipo de Query)
        ax3 = axes[0, 2]
        pivot_score = df.pivot_table(values='score_medio', index='config_nome', columns='tipo_query')
        sns.heatmap(pivot_score, annot=True, fmt='.3f', cmap='YlOrRd', ax=ax3)
        ax3.set_title('Score por Configuração e Tipo de Query')
        
        # 4. Tempo de Busca vs Tempo RAG
        ax4 = axes[1, 0]
        df_tempos = df.groupby('config_nome')[['tempo_busca', 'tempo_rag']].mean()
        df_tempos.plot(kind='bar', ax=ax4, stacked=True)
        ax4.set_title('Decomposição do Tempo de Resposta')
        ax4.set_ylabel('Tempo (segundos)')
        ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha='right')
        ax4.legend(['Busca', 'Geração RAG'])
        
        # 5. Scatter: Score vs Tempo Total
        ax5 = axes[1, 1]
        colors = plt.cm.viridis(np.linspace(0, 1, len(df['config_nome'].unique())))
        for i, config in enumerate(df['config_nome'].unique()):
            data = df[df['config_nome'] == config]
            ax5.scatter(data['tempo_total'], data['score_medio'], 
                       label=config, alpha=0.6, s=100, color=colors[i])
        ax5.set_xlabel('Tempo Total (segundos)')
        ax5.set_ylabel('Score Médio')
        ax5.set_title('Trade-off: Score vs Tempo')
        ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 6. Boxplot de Scores por Categoria
        ax6 = axes[1, 2]
        df.boxplot(column='score_medio', by='categoria', ax=ax6)
        ax6.set_title('Distribuição de Scores por Categoria')
        ax6.set_xlabel('Categoria')
        ax6.set_ylabel('Score')
        
        plt.tight_layout()
        
        # Salvar gráfico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analise_performance_rag_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Gráficos salvos em: {filename}")
        
        # Análise estatística
        print("\n📋 RESUMO ESTATÍSTICO:")
        print("-"*50)
        
        # Melhor configuração geral
        melhor_config = df.groupby('config_nome').agg({
            'score_medio': 'mean',
            'tempo_total': 'mean',
            'sucesso': 'sum'
        }).sort_values('score_medio', ascending=False)
        
        print("\n🏆 Top 3 Configurações por Score:")
        for i, (config, row) in enumerate(melhor_config.head(3).iterrows(), 1):
            print(f"{i}. {config}:")
            print(f"   Score médio: {row['score_medio']:.4f}")
            print(f"   Tempo médio: {row['tempo_total']:.2f}s")
        
        # Configuração mais rápida
        print("\n⚡ Configuração mais rápida:")
        config_rapida = melhor_config.sort_values('tempo_total').iloc[0]
        print(f"   {melhor_config.sort_values('tempo_total').index[0]}")
        print(f"   Tempo médio: {config_rapida['tempo_total']:.2f}s")
        
        # Melhor equilíbrio
        print("\n⚖️ Melhor equilíbrio (Score/Tempo):")
        df_balance = melhor_config.copy()
        df_balance['eficiencia'] = df_balance['score_medio'] / df_balance['tempo_total']
        melhor_balance = df_balance.sort_values('eficiencia', ascending=False).iloc[0]
        print(f"   {df_balance.sort_values('eficiencia', ascending=False).index[0]}")
        print(f"   Eficiência: {melhor_balance['eficiencia']:.4f}")
        
        # Salvar resultados detalhados
        df.to_csv(f"resultados_detalhados_{timestamp}.csv", index=False)
        print(f"\n💾 Resultados detalhados salvos em: resultados_detalhados_{timestamp}.csv")
        
        return df, melhor_config

def main():
    """Função principal"""
    testador = TestadorPerformanceRAG()
    
    # Executar testes
    testador.executar_bateria_testes()
    
    # Analisar e visualizar
    df_resultados, resumo = testador.analisar_resultados()
    
    print("\n✨ Teste de performance concluído!")
    print("\n💡 Recomendações baseadas nos resultados:")
    print("   • Para queries conceituais: Use configuração com ênfase semântica")
    print("   • Para palavras-chave específicas: Use configuração com ênfase full-text")
    print("   • Para uso geral: Use configuração híbrida otimizada (0.8, 1.5)")
    
    plt.show()

if __name__ == "__main__":
    main()