#!/usr/bin/env python3
"""
Busca Simples no Supabase - Apenas Full-Text
Não depende da API OpenAI, usa apenas busca por palavras-chave
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class BuscaSimples:
    def __init__(self):
        """Inicializa cliente Supabase"""
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
    def buscar(self, query: str, limit: int = 5):
        """Busca simples por palavras no conteúdo"""
        print(f"\n🔍 Buscando por: '{query}'")
        
        try:
            # Buscar documentos que contenham a query
            response = self.supabase.table('documents').select(
                'id', 'content', 'metadata'
            ).ilike('content', f'%{query}%').limit(limit).execute()
            
            if response.data:
                print(f"✅ Encontrados {len(response.data)} resultados\n")
                return response.data
            else:
                print("❌ Nenhum resultado encontrado\n")
                return []
                
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def mostrar_resultados(self, query: str, resultados):
        """Mostra os resultados de forma legível"""
        if not resultados:
            print("Nenhum documento encontrado.")
            return
            
        print("="*70)
        print(f"RESULTADOS PARA: '{query}'")
        print("="*70)
        
        for i, doc in enumerate(resultados, 1):
            print(f"\n📄 Documento {i}:")
            
            # Metadados
            metadata = doc.get('metadata', {})
            if isinstance(metadata, dict):
                fonte = metadata.get('fonte', 'Desconhecida')
                print(f"   Fonte: {fonte}")
            
            # Conteúdo com destaque
            content = doc.get('content', '')
            
            # Encontrar e destacar a query no conteúdo
            pos = content.lower().find(query.lower())
            if pos != -1:
                # Mostrar contexto ao redor da query
                inicio = max(0, pos - 100)
                fim = min(len(content), pos + 200)
                
                trecho = content[inicio:fim]
                
                # Adicionar reticências se necessário
                if inicio > 0:
                    trecho = "..." + trecho
                if fim < len(content):
                    trecho = trecho + "..."
                
                # Destacar a query
                trecho_destacado = trecho.replace(
                    query, f"**{query.upper()}**"
                )
                
                print(f"\n   Trecho relevante:")
                print(f"   {trecho_destacado}")
            
            print("\n" + "-"*70)


def main():
    """Interface simples de busca"""
    busca = BuscaSimples()
    
    print("\n" + "="*70)
    print("🔍 BUSCA SIMPLES NO SUPABASE")
    print("="*70)
    print("\nEste sistema busca por palavras-chave nos documentos.")
    print("Não requer API OpenAI!\n")
    print("Digite 'sair' para encerrar\n")
    print("-"*70)
    
    while True:
        try:
            query = input("\n🔍 Buscar por: ").strip()
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Até logo!")
                break
                
            if not query:
                continue
            
            # Buscar
            resultados = busca.buscar(query)
            
            # Mostrar
            busca.mostrar_resultados(query, resultados)
            
            # Responder especificamente sobre "ponto focal" se for a query
            if "ponto focal" in query.lower() and resultados:
                print("\n💡 RESPOSTA SOBRE 'PONTO FOCAL':")
                print("-"*50)
                
                for doc in resultados:
                    content = doc.get('content', '')
                    if "ponto focal" in content.lower():
                        # Extrair sentença completa
                        sentences = content.split('.')
                        for sentence in sentences:
                            if "ponto focal" in sentence.lower():
                                print(f"\n→ {sentence.strip()}.")
                                
                                # Contexto adicional
                                if "mateus" in sentence.lower():
                                    print("\n📌 Informação encontrada: Mateus foi definido como ponto focal")
                                break
                        break
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrompido")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    main()