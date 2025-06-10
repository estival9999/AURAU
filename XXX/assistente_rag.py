#!/usr/bin/env python3
"""
Assistente RAG Interativo com Busca Híbrida
Execute: python assistente_rag.py
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import json

# Adicionar diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_search_rag_test import HybridSearchRAG

# Carregar variáveis de ambiente
load_dotenv()

class AssistenteRAG:
    def __init__(self):
        """Inicializa o assistente RAG"""
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        print("🤖 Inicializando Assistente RAG...")
        self.rag_system = HybridSearchRAG(SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)
        self.historico = []
        
    def processar_pergunta(self, pergunta):
        """Processa uma pergunta e retorna a resposta"""
        # Configuração otimizada baseada nos testes de performance
        # Padrão: Híbrida (0.8, 1.5) - melhor equilíbrio geral
        full_text_weight = 0.8
        semantic_weight = 1.5
        
        # Ajustes finos baseados no tipo de pergunta
        if "?" in pergunta or any(q in pergunta.lower() for q in ["como", "o que", "qual", "quando", "onde", "por que"]):
            # Pergunta natural - aumentar um pouco o peso semântico
            semantic_weight = 1.8
        elif len(pergunta.split()) <= 3 and not "?" in pergunta:
            # Busca por palavras-chave específicas
            full_text_weight = 1.2
            semantic_weight = 1.0
        elif any(termo in pergunta.lower() for termo in ["cpf", "cep", "auralis", "pantaneta"]):
            # Termos técnicos ou nomes próprios - mais full-text
            full_text_weight = 1.5
            semantic_weight = 0.8
        
        # Buscar documentos relevantes
        print("\n🔍 Buscando informações...")
        results = self.rag_system.hybrid_search(
            pergunta,
            match_count=5,
            full_text_weight=full_text_weight,
            semantic_weight=semantic_weight
        )
        
        if not results:
            return {
                "resposta": "Desculpe, não encontrei informações sobre isso na base de conhecimento. Tente reformular sua pergunta.",
                "fontes": [],
                "documentos": 0
            }
        
        print(f"✅ Encontrei {len(results)} documentos relevantes")
        
        # Gerar resposta
        print("💭 Processando resposta...")
        
        system_prompt = """Você é um assistente especializado em dar respostas com base em documentos internos da empresa.
        Responda de forma clara, objetiva e estruturada, usando apenas as informações do contexto fornecido.
        Use bullet points quando apropriado para melhor legibilidade."""
        
        resposta = self.rag_system.generate_rag_response(
            pergunta, 
            results,
            system_prompt=system_prompt
        )
        
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
            "fontes": list(set(fontes)),  # Remover duplicatas
            "documentos": len(results)
        }
    
    def chat_interativo(self):
        """Interface de chat interativa"""
        print("\n" + "="*70)
        print("💬 ASSISTENTE RAG - BUSCA HÍBRIDA INTELIGENTE")
        print("="*70)
        
        print("\n📚 Base de Conhecimento Disponível:")
        print("   • Manual AURALIS - Sistema de gestão de reuniões com IA")
        print("   • Manual Cooperativa Pantaneta - Cooperativa de crédito")
        
        print("\n🎯 Dicas para melhores resultados:")
        print("   • Faça perguntas específicas")
        print("   • Use palavras-chave relevantes")
        print("   • Perguntas naturais funcionam muito bem!")
        
        print("\n💡 Exemplos:")
        print('   • "Como gravar uma reunião no AURALIS?"')
        print('   • "Quais são as taxas de crédito rural?"')
        print('   • "Procedimentos de segurança de dados"')
        
        print("\n📝 Comandos especiais:")
        print("   • 'sair' - encerrar chat")
        print("   • 'limpar' - limpar tela")
        print("   • 'historico' - ver perguntas anteriores")
        
        print("\n" + "-"*70)
        
        while True:
            try:
                # Receber entrada
                print("\n❓ Sua pergunta:")
                pergunta = input(">>> ").strip()
                
                # Comandos especiais
                if pergunta.lower() in ['sair', 'exit', 'quit', 'q']:
                    print("\n👋 Obrigado por usar o Assistente RAG! Até logo!")
                    break
                
                if pergunta.lower() == 'limpar':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                
                if pergunta.lower() == 'historico':
                    if self.historico:
                        print("\n📜 Histórico de perguntas:")
                        for i, h in enumerate(self.historico[-5:], 1):
                            print(f"   {i}. {h}")
                    else:
                        print("\n📜 Histórico vazio")
                    continue
                
                if not pergunta:
                    continue
                
                # Adicionar ao histórico
                self.historico.append(pergunta)
                
                # Processar pergunta
                resultado = self.processar_pergunta(pergunta)
                
                # Exibir resposta
                print("\n" + "="*70)
                print("🤖 RESPOSTA:")
                print("="*70)
                print(resultado["resposta"])
                print("="*70)
                
                # Exibir metadados
                print(f"\n📊 Metadados:")
                print(f"   • Documentos analisados: {resultado['documentos']}")
                if resultado["fontes"]:
                    print(f"   • Fontes principais:")
                    for fonte in resultado["fontes"]:
                        print(f"     - {fonte}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrompido pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro: {str(e)}")
                print("Por favor, tente novamente.")

def main():
    """Função principal"""
    try:
        assistente = AssistenteRAG()
        assistente.chat_interativo()
    except Exception as e:
        print(f"❌ Erro ao inicializar: {str(e)}")
        print("Verifique se as credenciais estão corretas no arquivo .env")

if __name__ == "__main__":
    main()