#!/usr/bin/env python3
"""
Script de teste para verificar a integração entre frontend e backend
"""

import os
import sys

# Adicionar o diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== Teste de Integração AURALIS ===\n")

# 1. Verificar variáveis de ambiente
print("1. Verificando variáveis de ambiente:")
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"   ✅ OPENAI_API_KEY configurada: {openai_key[:10]}...")
else:
    print("   ❌ OPENAI_API_KEY não configurada - sistema usará modo simulado")

debug_mode = os.getenv("DEBUG_MODE")
print(f"   DEBUG_MODE: {debug_mode or 'Não definido'}")

# 2. Testar importação do backend
print("\n2. Testando importação do backend:")
try:
    from main import AURALISBackend
    print("   ✅ Backend importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar backend: {e}")
    sys.exit(1)

# 3. Criar instância do backend
print("\n3. Criando instância do backend:")
try:
    backend = AURALISBackend(mock_mode=None)
    print(f"   ✅ Backend criado em modo: {'mock' if backend.mock_mode else 'produção'}")
except Exception as e:
    print(f"   ❌ Erro ao criar backend: {e}")
    sys.exit(1)

# 4. Testar autenticação
print("\n4. Testando autenticação:")
user = backend.authenticate("teste", "123")
if user:
    print(f"   ✅ Usuário autenticado: {user.get('username')}")
else:
    print("   ❌ Falha na autenticação")

# 5. Testar processamento de mensagem
print("\n5. Testando processamento de mensagem:")
try:
    resposta = backend.process_user_message("Olá, como você pode me ajudar?")
    print(f"   ✅ Resposta recebida ({len(resposta)} caracteres)")
    print(f"   Preview: {resposta[:100]}...")
except Exception as e:
    print(f"   ❌ Erro ao processar mensagem: {e}")

# 6. Verificar qual implementação está sendo usada
print("\n6. Verificando implementação dos agentes:")
try:
    from src.agentes.sistema_agentes import SistemaAgentes
    sistema = SistemaAgentes(modo_debug=True)
    
    # Verificar tipo do orquestrador
    orq_type = type(sistema.orquestrador).__name__
    base_class = type(sistema.orquestrador).__bases__[0].__name__
    
    print(f"   Orquestrador: {orq_type}")
    print(f"   Classe base: {base_class}")
    
    if base_class == "AgenteBaseSimulado":
        print("   ⚠️  Usando implementação SIMULADA (mock)")
    else:
        print("   ✅ Usando implementação REAL")
        
except Exception as e:
    print(f"   ❌ Erro ao verificar implementação: {e}")

print("\n=== Fim do teste ===")

# 7. Informações para configurar OpenAI
if not openai_key:
    print("\n📝 Para usar IA real, configure a variável de ambiente:")
    print("   export OPENAI_API_KEY='sua-chave-aqui'")
    print("   ou crie um arquivo .env com:")
    print("   OPENAI_API_KEY=sua-chave-aqui")