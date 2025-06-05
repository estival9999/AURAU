#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitário para manipulação segura de caminhos no sistema AURALIS.
Previne problemas com espaços, caracteres especiais e barras invertidas.
"""

import os
import sys
import shlex
import subprocess
from pathlib import Path
from typing import Union, Optional, List


class ManipuladorCaminhos:
    """Classe para manipulação segura de caminhos no sistema."""
    
    @staticmethod
    def normalizar_caminho(caminho: str) -> str:
        """
        Normaliza um caminho removendo escapes desnecessários e padronizando separadores.
        
        Args:
            caminho: Caminho a ser normalizado
            
        Returns:
            Caminho normalizado e absoluto
        """
        # Remove escapes de barras invertidas
        caminho = caminho.replace('\\ ', ' ')
        
        # Converte para Path object para normalização
        path_obj = Path(caminho)
        
        # Retorna caminho absoluto normalizado
        return str(path_obj.absolute())
    
    @staticmethod
    def caminho_com_aspas(caminho: str) -> str:
        """
        Retorna o caminho com aspas duplas para uso em comandos shell.
        
        Args:
            caminho: Caminho a ser formatado
            
        Returns:
            Caminho entre aspas duplas
        """
        return f'"{caminho}"'
    
    @staticmethod
    def caminho_shell_safe(caminho: str) -> str:
        """
        Retorna o caminho seguro para uso em comandos shell usando shlex.
        
        Args:
            caminho: Caminho a ser formatado
            
        Returns:
            Caminho escapado corretamente para shell
        """
        return shlex.quote(caminho)
    
    @staticmethod
    def validar_caminho_diretorio(caminho: str) -> bool:
        """
        Valida se um caminho de diretório é válido e acessível.
        
        Args:
            caminho: Caminho do diretório a validar
            
        Returns:
            True se o diretório existe e é acessível, False caso contrário
        """
        try:
            path_obj = Path(caminho)
            return path_obj.exists() and path_obj.is_dir()
        except Exception:
            return False
    
    @staticmethod
    def criar_diretorio_seguro(caminho: str, parents: bool = True) -> bool:
        """
        Cria um diretório de forma segura, lidando com espaços e caracteres especiais.
        
        Args:
            caminho: Caminho do diretório a criar
            parents: Se True, cria diretórios pais se necessário
            
        Returns:
            True se criado com sucesso, False caso contrário
        """
        try:
            path_obj = Path(caminho)
            path_obj.mkdir(parents=parents, exist_ok=True)
            return True
        except Exception as e:
            print(f"Erro ao criar diretório: {e}")
            return False
    
    @staticmethod
    def executar_comando_seguro(comando: str, caminho: Optional[str] = None) -> tuple[bool, str]:
        """
        Executa um comando shell de forma segura, lidando com caminhos problemáticos.
        
        Args:
            comando: Comando base (ex: "mkdir -p")
            caminho: Caminho a ser usado no comando (opcional)
            
        Returns:
            Tupla (sucesso: bool, output: str)
        """
        try:
            if caminho:
                # Usa aspas duplas para o caminho
                comando_completo = f'{comando} "{caminho}"'
            else:
                comando_completo = comando
            
            # Executa o comando
            result = subprocess.run(
                comando_completo,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            return True, result.stdout
            
        except subprocess.CalledProcessError as e:
            return False, f"Erro: {e.stderr}"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
    
    @staticmethod
    def listar_diretorios_criados_erroneamente() -> List[str]:
        """
        Lista possíveis diretórios criados erroneamente devido a problemas de escape.
        
        Returns:
            Lista de caminhos de diretórios suspeitos
        """
        suspeitos = []
        
        # Padrões comuns de diretórios criados por erro
        padroes_erro = [
            "de/",
            "trabalho/",
            "Área/",
            "*/de/",
            "*/trabalho/",
        ]
        
        # Verifica no diretório atual e em caminhos comuns
        for padrao in padroes_erro:
            try:
                from glob import glob
                encontrados = glob(padrao, recursive=True)
                suspeitos.extend(encontrados)
            except:
                pass
        
        return list(set(suspeitos))  # Remove duplicatas
    
    @staticmethod
    def limpar_diretorios_errados(confirmar: bool = True) -> None:
        """
        Remove diretórios criados erroneamente após confirmação.
        
        Args:
            confirmar: Se True, pede confirmação antes de remover
        """
        suspeitos = ManipuladorCaminhos.listar_diretorios_criados_erroneamente()
        
        if not suspeitos:
            print("Nenhum diretório suspeito encontrado.")
            return
        
        print("Diretórios suspeitos encontrados:")
        for dir_path in suspeitos:
            print(f"  - {dir_path}")
        
        if confirmar:
            resposta = input("\nDeseja remover estes diretórios? (s/N): ")
            if resposta.lower() != 's':
                print("Operação cancelada.")
                return
        
        for dir_path in suspeitos:
            try:
                import shutil
                shutil.rmtree(dir_path)
                print(f"Removido: {dir_path}")
            except Exception as e:
                print(f"Erro ao remover {dir_path}: {e}")


def validar_antes_criar(caminho: str) -> bool:
    """
    Valida um caminho antes de criar diretório, mostrando informações detalhadas.
    
    Args:
        caminho: Caminho a validar
        
    Returns:
        True se o caminho é válido, False caso contrário
    """
    manipulador = ManipuladorCaminhos()
    
    print(f"\n=== Validação de Caminho ===")
    print(f"Caminho original: {caminho}")
    
    # Normaliza o caminho
    caminho_normalizado = manipulador.normalizar_caminho(caminho)
    print(f"Caminho normalizado: {caminho_normalizado}")
    
    # Verifica se já existe
    if manipulador.validar_caminho_diretorio(caminho_normalizado):
        print(f"✓ Diretório já existe: {caminho_normalizado}")
        return True
    
    # Mostra como será o comando
    print(f"\nComando que será executado:")
    print(f'  mkdir -p "{caminho_normalizado}"')
    
    # Verifica diretório pai
    parent = Path(caminho_normalizado).parent
    if parent.exists():
        print(f"✓ Diretório pai existe: {parent}")
    else:
        print(f"✗ Diretório pai NÃO existe: {parent}")
        print("  Será criado automaticamente com -p")
    
    return True


def exemplo_uso():
    """Demonstra o uso correto das funções."""
    print("=== Exemplo de Uso Seguro ===\n")
    
    # Caminho problemático
    caminho_problema = "/home/mateus/Área de trabalho/X_AURA/src/database"
    
    manipulador = ManipuladorCaminhos()
    
    # Mostra diferentes formas de lidar com o caminho
    print(f"1. Caminho original: {caminho_problema}")
    print(f"2. Normalizado: {manipulador.normalizar_caminho(caminho_problema)}")
    print(f"3. Com aspas: {manipulador.caminho_com_aspas(caminho_problema)}")
    print(f"4. Shell-safe: {manipulador.caminho_shell_safe(caminho_problema)}")
    
    # Validação antes de criar
    print("\n=== Validação ===")
    if validar_antes_criar(caminho_problema):
        print("\n✓ Caminho válido para criação")
    
    # Criar diretório de forma segura
    print("\n=== Criação Segura ===")
    if manipulador.criar_diretorio_seguro(caminho_problema):
        print("✓ Diretório criado com sucesso!")
    else:
        print("✗ Falha ao criar diretório")


if __name__ == "__main__":
    # Se executado diretamente, mostra exemplo
    exemplo_uso()
    
    # Opção para limpar diretórios errados
    print("\n" + "="*50)
    limpar = input("\nDeseja verificar e limpar diretórios criados erroneamente? (s/N): ")
    if limpar.lower() == 's':
        ManipuladorCaminhos.limpar_diretorios_errados()