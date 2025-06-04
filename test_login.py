#!/usr/bin/env python3
"""
Script de teste simples para verificar login com credenciais admin/admin123
"""

from main import AURALISBackend

print("🔐 Teste de Login AURALIS")
print("-" * 40)

# Criar backend em modo mock para teste
backend = AURALISBackend(mock_mode=True)

print("\nTestando login com credenciais:")
print("Usuário: admin")
print("Senha: admin123")

user = backend.authenticate("admin", "admin123")

if user:
    print("\n✅ Login bem-sucedido!")
    print(f"Usuário: {user['full_name']}")
    print(f"Email: {user['email']}")
    print(f"Área: {user['area']}")
    print(f"Role: {user['role']}")
else:
    print("\n❌ Falha no login!")

print("\nTestando processamento de mensagem...")
if user:
    response = backend.process_user_message("ajuda")
    print(f"\nResposta do sistema:\n{response[:200]}...")