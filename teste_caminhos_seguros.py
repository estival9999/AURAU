#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de demonstração e teste para manipulação segura de caminhos.
Mostra exemplos práticos de como evitar problemas com espaços e caracteres especiais.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils_caminhos import ManipuladorCaminhos, validar_antes_criar


def demonstrar_problema():
    """Demonstra o problema com barras invertidas em caminhos."""
    print("="*60)
    print("DEMONSTRAÇÃO DO PROBLEMA COM BARRAS INVERTIDAS")
    print("="*60)
    
    # Caminho problemático
    caminho_errado = "/home/mateus/Área\\ de\\ trabalho/X_AURA/teste"
    caminho_correto = "/home/mateus/Área de trabalho/X_AURA/teste"
    
    print(f"\n❌ FORMA ERRADA (com barras invertidas):")
    print(f"   {caminho_errado}")
    print(f"   Isso pode criar diretórios como: 'Área\\', 'de\\', 'trabalho\\'")
    
    print(f"\n✅ FORMA CORRETA (sem escapes, usar aspas no shell):")
    print(f"   {caminho_correto}")
    print(f'   No shell usar: mkdir -p "{caminho_correto}"')


def demonstrar_solucao():
    """Demonstra as soluções implementadas."""
    print("\n" + "="*60)
    print("SOLUÇÕES IMPLEMENTADAS")
    print("="*60)
    
    manipulador = ManipuladorCaminhos()
    
    # Exemplo de caminho com espaços
    caminho_teste = "/home/mateus/Área de trabalho/X_AURA/teste_espacos/novo diretório"
    
    print(f"\n1. NORMALIZAÇÃO DE CAMINHOS:")
    print(f"   Original: {caminho_teste}")
    print(f"   Normalizado: {manipulador.normalizar_caminho(caminho_teste)}")
    
    print(f"\n2. FORMATAÇÃO PARA SHELL:")
    print(f"   Com aspas duplas: {manipulador.caminho_com_aspas(caminho_teste)}")
    print(f"   Shell-safe (shlex): {manipulador.caminho_shell_safe(caminho_teste)}")
    
    print(f"\n3. CRIAÇÃO SEGURA DE DIRETÓRIOS:")
    print(f"   Usando Python Path (recomendado):")
    print(f"   >>> manipulador.criar_diretorio_seguro('{caminho_teste}')")
    
    # Cria o diretório de teste
    if manipulador.criar_diretorio_seguro(caminho_teste):
        print(f"   ✅ Diretório criado com sucesso!")
        
        # Verifica se foi criado corretamente
        if manipulador.validar_caminho_diretorio(caminho_teste):
            print(f"   ✅ Verificado: diretório existe no local correto")
        
        # Remove o diretório de teste
        try:
            import shutil
            shutil.rmtree("/home/mateus/Área de trabalho/X_AURA/teste_espacos")
            print(f"   🗑️  Diretório de teste removido")
        except:
            pass


def exemplos_praticos():
    """Mostra exemplos práticos de uso."""
    print("\n" + "="*60)
    print("EXEMPLOS PRÁTICOS DE USO")
    print("="*60)
    
    manipulador = ManipuladorCaminhos()
    
    print("\n📁 EXEMPLO 1: Criar estrutura de diretórios do projeto")
    diretorios_projeto = [
        "/home/mateus/Área de trabalho/X_AURA/src/database",
        "/home/mateus/Área de trabalho/X_AURA/src/database/migrations",
        "/home/mateus/Área de trabalho/X_AURA/src/database/models",
        "/home/mateus/Área de trabalho/X_AURA/data/audio files",
        "/home/mateus/Área de trabalho/X_AURA/data/meeting notes"
    ]
    
    for dir_path in diretorios_projeto:
        print(f"\n   Criando: {dir_path}")
        print(f'   Comando seguro: mkdir -p "{dir_path}"')
    
    print("\n\n📝 EXEMPLO 2: Comandos shell seguros")
    print("   # Listar arquivos em diretório com espaços:")
    print('   ls -la "/home/mateus/Área de trabalho/X_AURA"')
    
    print("\n   # Copiar arquivo para diretório com espaços:")
    print('   cp arquivo.txt "/home/mateus/Área de trabalho/X_AURA/data/meeting notes/"')
    
    print("\n   # Mover arquivo entre diretórios com espaços:")
    print('   mv "/home/mateus/Área de trabalho/X_AURA/old file.txt" "/home/mateus/Área de trabalho/X_AURA/new file.txt"')
    
    print("\n\n🐍 EXEMPLO 3: Uso em Python")
    print("""
from pathlib import Path
from src.utils_caminhos import ManipuladorCaminhos

# Método 1: Usando pathlib (recomendado)
caminho = Path("/home/mateus/Área de trabalho/X_AURA/src/database")
caminho.mkdir(parents=True, exist_ok=True)

# Método 2: Usando o utilitário
manipulador = ManipuladorCaminhos()
manipulador.criar_diretorio_seguro("/home/mateus/Área de trabalho/X_AURA/src/database")

# Método 3: Executar comando shell de forma segura
sucesso, output = manipulador.executar_comando_seguro(
    "mkdir -p",
    "/home/mateus/Área de trabalho/X_AURA/src/database"
)
""")


def regras_importantes():
    """Lista as regras mais importantes."""
    print("\n" + "="*60)
    print("⚠️  REGRAS IMPORTANTES - MEMORIZE!")
    print("="*60)
    
    regras = [
        "1. SEMPRE use aspas duplas em caminhos com espaços no shell",
        "2. NUNCA use barras invertidas (\\) para escapar espaços",
        "3. SEMPRE valide o caminho antes de criar diretórios",
        "4. PREFIRA usar Python Path em vez de comandos shell quando possível",
        "5. SEMPRE verifique se o diretório foi criado no local correto",
        "6. Use o utilitário utils_caminhos.py para operações complexas",
        "7. Em caso de dúvida, imprima o caminho primeiro para verificar"
    ]
    
    for regra in regras:
        print(f"\n   🔸 {regra}")
    
    print("\n\n💡 DICA FINAL:")
    print("   Se você ver diretórios como 'de/', 'trabalho/', 'Área/' criados")
    print("   isoladamente, é sinal de que houve erro com escapes de espaços!")


if __name__ == "__main__":
    # Executa todas as demonstrações
    demonstrar_problema()
    demonstrar_solucao()
    exemplos_praticos()
    regras_importantes()
    
    print("\n\n" + "="*60)
    print("✅ DEMONSTRAÇÃO COMPLETA!")
    print("="*60)