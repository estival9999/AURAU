"""
Carrega variáveis de ambiente do arquivo .env
Deve ser importado ANTES de qualquer outro módulo que use essas variáveis
"""

import os
from pathlib import Path

def load_env():
    """Carrega variáveis de ambiente do arquivo .env"""
    env_file = Path(__file__).parent / '.env'
    
    if env_file.exists():
        print("📋 Carregando configurações de .env...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value.strip()
                        if key == 'OPENAI_API_KEY':
                            print(f"   ✅ {key} configurada ({value[:20]}...)")
                        elif key in ['SUPABASE_URL', 'DEBUG_MODE']:
                            print(f"   ✅ {key} configurada")
    else:
        print("⚠️  Arquivo .env não encontrado")

# Carregar automaticamente ao importar
load_env()