#!/usr/bin/env python3
"""
Teste final da integração com IA real
"""

import sys
import os

# Carregar ambiente ANTES de tudo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import load_env

print("\n=== TESTE FINAL - AURALIS COM IA REAL ===\n")

# Verificar se OpenAI está configurada
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OpenAI API Key carregada: {api_key[:20]}...")
else:
    print("❌ OpenAI API Key NÃO encontrada!")
    sys.exit(1)

# Importar após carregar env
from main import AURALISBackend
from src.agentes.sistema_agentes import SistemaAgentes

print("\n1. Testando sistema de agentes:")
sistema = SistemaAgentes(modo_debug=True)

print(f"\n   Modo: {sistema.contexto_global['modo']}")
print(f"   Agentes ativos: {len([a for a in [sistema.orquestrador, sistema.consultor, sistema.criativo] if a])}")

# Verificar se está usando implementação real
base_class = type(sistema.orquestrador).__bases__[0].__name__
print(f"   Implementação: {'REAL' if base_class == 'AgenteBase' else 'SIMULADA'}")

print("\n2. Testando processamento de mensagem:")
# Testar uma pergunta simples
pergunta = "Como posso usar o AURALIS para melhorar minhas reuniões?"
print(f"   Pergunta: {pergunta}")

try:
    resposta = sistema.processar_mensagem_usuario(pergunta)
    print(f"   ✅ Resposta recebida!")
    print(f"   Preview: {resposta[:150]}...")
    
    # Verificar se é resposta simulada
    if "[MODO SIMULADO" in resposta:
        print("   ⚠️  AINDA USANDO MODO SIMULADO!")
    else:
        print("   ✅ Usando IA REAL!")
        
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n3. Testando backend integrado:")
backend = AURALISBackend(mock_mode=False)  # Forçar modo real
print(f"   Mock mode: {backend.mock_mode}")

# Testar processamento via backend
try:
    resposta2 = backend.process_user_message("Olá, sou novo no sistema")
    print(f"   ✅ Backend processou mensagem")
    print(f"   Preview: {resposta2[:100]}...")
except Exception as e:
    print(f"   ❌ Erro no backend: {e}")

print("\n=== FIM DO TESTE ===")

if base_class != "AgenteBase":
    print("\n⚠️  ATENÇÃO: Sistema ainda está usando implementação simulada!")
    print("   Verifique se os módulos dos agentes estão detectando a API key corretamente.")
else:
    print("\n✅ Sistema configurado para usar IA REAL!")
    print("   Você pode executar FRONT.py agora.")