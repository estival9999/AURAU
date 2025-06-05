#!/usr/bin/env python3
"""
Script para verificar o conteúdo completo do documento e entender
porque está gerando chunks repetidos
"""

import os
import sys

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.supabase_handler import SupabaseHandler

def main():
    print("🔍 Verificando documento original...")
    
    supabase = SupabaseHandler()
    
    # ID do documento problemático
    doc_id = "e98bd2fe-beaa-428f-b6c6-5963f229e08a"
    
    # Buscar documento completo
    try:
        response = supabase.client.table('knowledge_base').select(
            'id, title, content_full, created_at, updated_at'
        ).eq('id', doc_id).execute()
        
        if response.data:
            doc = response.data[0]
            
            print(f"\n📄 DOCUMENTO: {doc['title']}")
            print(f"ID: {doc['id']}")
            print(f"Criado em: {doc['created_at']}")
            print(f"Atualizado em: {doc['updated_at']}")
            
            content = doc['content_full']
            print(f"\nTamanho total: {len(content):,} caracteres")
            
            # Mostrar últimos 1000 caracteres
            print("\n📝 ÚLTIMOS 1000 CARACTERES DO DOCUMENTO:")
            print("-" * 80)
            if len(content) > 1000:
                print(content[-1000:])
            else:
                print(content)
            print("-" * 80)
            
            # Analisar estrutura do final do documento
            print("\n🔍 ANÁLISE DO FINAL DO DOCUMENTO:")
            
            # Verificar se há repetições no próprio documento
            last_500 = content[-500:] if len(content) > 500 else content
            
            # Contar ocorrências de strings específicas
            ocorrencias = {
                "suporte@auralis.com": content.count("suporte@auralis.com"),
                "Python Best Practices": content.count("Python Best Practices"),
                "Versão": content.count("Versão"),
                "mentation": content.count("mentation")
            }
            
            print("\nOcorrências de strings no documento completo:")
            for string, count in ocorrencias.items():
                print(f"  '{string}': {count} vez(es)")
            
            # Verificar se o documento termina abruptamente
            print(f"\nÚltimos 200 caracteres (com repr):")
            print(repr(content[-200:]))
            
            # Sugestão de correção
            print("\n💡 DIAGNÓSTICO DO PROBLEMA:")
            print("O documento parece ter sido truncado ou mal formatado no final.")
            print("Os últimos 200 caracteres estão sendo repetidos em múltiplos chunks.")
            print("\nPossíveis causas:")
            print("1. O algoritmo de chunking tem um bug quando o documento é menor que o esperado")
            print("2. O overlap está causando repetição excessiva no final do documento")
            print("3. O documento foi importado com problemas de formatação")
            
        else:
            print(f"❌ Documento {doc_id} não encontrado!")
            
    except Exception as e:
        print(f"❌ Erro ao buscar documento: {e}")


if __name__ == "__main__":
    main()