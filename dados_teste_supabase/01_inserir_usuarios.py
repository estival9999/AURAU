#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inserir usuários de teste no Supabase
Dados realistas simulando funcionários de uma empresa
"""

import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import bcrypt

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Função para criar hash de senha
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Dados dos usuários - simulando empresa real
usuarios = [
    {
        "username": "carlos.mendes",
        "password_hash": hash_password("senha123"),  # Em produção, usar senhas seguras
        "email": "carlos.mendes@techcorp.com.br",
        "full_name": "Carlos Eduardo Mendes",
        "role": "Diretor de Tecnologia",
        "department": "Tecnologia",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(hours=2)).isoformat()
    },
    {
        "username": "ana.silva",
        "password_hash": hash_password("senha123"),
        "email": "ana.silva@techcorp.com.br",
        "full_name": "Ana Paula Silva",
        "role": "Gerente de Projetos",
        "department": "Tecnologia",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(days=1)).isoformat()
    },
    {
        "username": "roberto.santos",
        "password_hash": hash_password("senha123"),
        "email": "roberto.santos@techcorp.com.br",
        "full_name": "Roberto dos Santos",
        "role": "Analista de Sistemas Senior",
        "department": "Tecnologia",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(hours=5)).isoformat()
    },
    {
        "username": "mariana.costa",
        "password_hash": hash_password("senha123"),
        "email": "mariana.costa@techcorp.com.br",
        "full_name": "Mariana Ferreira Costa",
        "role": "Coordenadora de RH",
        "department": "Recursos Humanos",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(days=2)).isoformat()
    },
    {
        "username": "pedro.oliveira",
        "password_hash": hash_password("senha123"),
        "email": "pedro.oliveira@techcorp.com.br",
        "full_name": "Pedro Henrique Oliveira",
        "role": "Desenvolvedor Full Stack",
        "department": "Tecnologia",
        "is_active": True,
        "last_login": datetime.now().isoformat()
    },
    {
        "username": "juliana.martinez",
        "password_hash": hash_password("senha123"),
        "email": "juliana.martinez@techcorp.com.br",
        "full_name": "Juliana Martinez",
        "role": "Analista de Marketing",
        "department": "Marketing",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(days=3)).isoformat()
    },
    {
        "username": "fernando.lima",
        "password_hash": hash_password("senha123"),
        "email": "fernando.lima@techcorp.com.br",
        "full_name": "Fernando Augusto Lima",
        "role": "Gerente Financeiro",
        "department": "Financeiro",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(hours=8)).isoformat()
    },
    {
        "username": "patricia.rocha",
        "password_hash": hash_password("senha123"),
        "email": "patricia.rocha@techcorp.com.br",
        "full_name": "Patricia Rocha",
        "role": "UX Designer",
        "department": "Tecnologia",
        "is_active": True,
        "last_login": (datetime.now() - timedelta(days=1, hours=3)).isoformat()
    }
]

# Inserir usuários
print("🔄 Inserindo usuários no Supabase...")
for usuario in usuarios:
    try:
        response = supabase.table('users').insert(usuario).execute()
        print(f"✅ Usuário {usuario['full_name']} inserido com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inserir {usuario['full_name']}: {str(e)}")

# Verificar inserção
print("\n📊 Verificando usuários inseridos:")
try:
    users = supabase.table('users').select("*").execute()
    print(f"Total de usuários no banco: {len(users.data)}")
    for user in users.data:
        print(f"  - {user['full_name']} ({user['role']}) - Departamento: {user['department']}")
except Exception as e:
    print(f"❌ Erro ao verificar usuários: {str(e)}")

print("\n✅ Script de usuários concluído!")