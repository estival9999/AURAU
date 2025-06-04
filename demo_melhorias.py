#!/usr/bin/env python3
"""
Script de demonstração das melhorias implementadas nos prompts AURALIS.
Permite interação direta com os agentes melhorados.
"""

import os
import sys
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agentes.sistema_agentes import SistemaAgentes
from src.database.supabase_handler import SupabaseHandler


class DemoMelhorias:
    """Demonstração interativa das melhorias."""
    
    def __init__(self):
        """Inicializa o sistema em modo simulado."""
        print("🚀 DEMONSTRAÇÃO DAS MELHORIAS ULTRATHINKS - SISTEMA AURALIS")
        print("=" * 60)
        print("Iniciando sistema em modo simulado...\n")
        
        # Inicializa componentes
        self.db_handler = SupabaseHandler()
        self.sistema_agentes = SistemaAgentes(modo_debug=True)
        
        # Contexto do usuário para demonstração
        self.contexto_usuario = {
            "user_id": "demo_user",
            "nome": "Usuário Demo",
            "cargo": "Gerente de Projetos",
            "empresa": "TechCorp Demo",
            "timestamp": datetime.now().isoformat()
        }
        
        print("✅ Sistema inicializado com sucesso!\n")
    
    def demonstrar_casos_especiais(self):
        """Demonstra o tratamento de casos especiais."""
        print("\n📋 1. DEMONSTRAÇÃO: Tratamento de Casos Especiais")
        print("-" * 50)
        
        casos = [
            ("", "Entrada vazia"),
            ("?", "Comando muito curto"),
            ("ajuda", "Pedido de ajuda"),
            ("oi", "Saudação"),
            ("Buscar reuniões sobre vendas e também gerar ideias para melhorar atendimento", "Múltiplas intenções")
        ]
        
        for entrada, descricao in casos:
            print(f"\n🔸 {descricao}")
            print(f"   Entrada: '{entrada}'")
            
            resposta = self.sistema_agentes.processar_mensagem_usuario(
                entrada,
                self.contexto_usuario
            )
            
            print(f"   Resposta:")
            # Mostra apenas as primeiras linhas da resposta
            linhas = resposta.split('\n')[:5]
            for linha in linhas:
                print(f"   {linha}")
            if len(resposta.split('\n')) > 5:
                print("   ...")
    
    def demonstrar_consultas(self):
        """Demonstra melhorias nas consultas."""
        print("\n\n📋 2. DEMONSTRAÇÃO: Consultas Melhoradas")
        print("-" * 50)
        
        consultas = [
            "Encontre reuniões sobre projeto AURALIS",
            "Quem participou das reuniões desta semana?",
            "Buscar informações sobre um projeto que não existe"
        ]
        
        for consulta in consultas:
            print(f"\n🔸 Consulta: '{consulta}'")
            
            resposta = self.sistema_agentes.processar_mensagem_usuario(
                consulta,
                self.contexto_usuario
            )
            
            print(f"   Resposta:")
            # Mostra formatação rica
            linhas = resposta.split('\n')[:8]
            for linha in linhas:
                print(f"   {linha}")
            print("   ...")
    
    def demonstrar_brainstorm(self):
        """Demonstra melhorias no brainstorm."""
        print("\n\n📋 3. DEMONSTRAÇÃO: Brainstorm Melhorado")
        print("-" * 50)
        
        desafios = [
            "Preciso de ideias para reduzir custos operacionais",
            "Como melhorar a comunicação da equipe remota?"
        ]
        
        for desafio in desafios[:1]:  # Mostra apenas um exemplo completo
            print(f"\n🔸 Desafio: '{desafio}'")
            
            resposta = self.sistema_agentes.processar_mensagem_usuario(
                desafio,
                self.contexto_usuario
            )
            
            print(f"   Resposta:")
            # Mostra estrutura da resposta
            linhas = resposta.split('\n')[:15]
            for linha in linhas:
                print(f"   {linha}")
            print("   ...")
    
    def modo_interativo(self):
        """Modo interativo para testar qualquer entrada."""
        print("\n\n📋 4. MODO INTERATIVO")
        print("-" * 50)
        print("Digite suas mensagens para testar o sistema melhorado.")
        print("Digite 'sair' para encerrar.\n")
        
        while True:
            try:
                entrada = input("👤 Você: ")
                
                if entrada.lower() in ['sair', 'exit', 'quit']:
                    print("\n👋 Encerrando demonstração. Obrigado!")
                    break
                
                print("\n🤖 AURALIS processando...\n")
                
                resposta = self.sistema_agentes.processar_mensagem_usuario(
                    entrada,
                    self.contexto_usuario
                )
                
                print("🤖 AURALIS:")
                print(resposta)
                print("\n" + "-" * 50 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Demonstração interrompida. Até logo!")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}")
                print("Tente novamente.\n")
    
    def executar_demonstracao_completa(self):
        """Executa toda a demonstração."""
        print("\n🎯 INICIANDO DEMONSTRAÇÃO COMPLETA DAS MELHORIAS\n")
        
        # 1. Casos especiais
        self.demonstrar_casos_especiais()
        
        # 2. Consultas
        self.demonstrar_consultas()
        
        # 3. Brainstorm
        self.demonstrar_brainstorm()
        
        # 4. Modo interativo
        self.modo_interativo()


def main():
    """Função principal."""
    demo = DemoMelhorias()
    
    print("\n🎯 O que você gostaria de fazer?\n")
    print("1. Executar demonstração completa")
    print("2. Ir direto para o modo interativo")
    print("3. Sair")
    
    escolha = input("\nEscolha (1-3): ")
    
    if escolha == "1":
        demo.executar_demonstracao_completa()
    elif escolha == "2":
        demo.modo_interativo()
    else:
        print("\n👋 Até logo!")


if __name__ == "__main__":
    main()