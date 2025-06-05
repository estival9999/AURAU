"""
Script para importar base de conhecimento de arquivos .txt para o Supabase.
Processa documentos de texto e gera embeddings para busca semântica.

Uso:
    python importar_base_conhecimento.py arquivo.txt --titulo "Manual XYZ" --tipo manual --departamento TI
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional
import re
import json

# Adicionar diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.supabase_handler import SupabaseHandler
from database.embeddings_handler import EmbeddingsHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImportadorConhecimento:
    """Classe para importar documentos da base de conhecimento."""
    
    def __init__(self):
        """Inicializa o importador."""
        logger.info("Inicializando importador de base de conhecimento...")
        
        # Inicializar handlers
        self.db = SupabaseHandler()
        self.embeddings = EmbeddingsHandler(self.db.client)
        
        # Verificar conexão
        if not self.db.testar_conexao():
            raise RuntimeError("Falha na conexão com Supabase")
        
        logger.info("Conexão com Supabase estabelecida")
    
    def processar_arquivo_txt(self, caminho: str, titulo: str, 
                            tipo: str = 'manual', 
                            departamento: Optional[str] = None,
                            tags: Optional[list] = None) -> str:
        """
        Processa um arquivo .txt e importa para a base de conhecimento.
        
        Args:
            caminho: Caminho do arquivo .txt
            titulo: Título do documento
            tipo: Tipo do documento (manual, procedimento, política, etc)
            departamento: Departamento relacionado
            tags: Lista de tags/palavras-chave
            
        Returns:
            ID do documento criado
        """
        try:
            # Verificar se arquivo existe
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
            
            # Ler conteúdo do arquivo
            logger.info(f"Lendo arquivo: {caminho}")
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Validar conteúdo
            if not conteudo.strip():
                raise ValueError("Arquivo está vazio")
            
            logger.info(f"Arquivo lido com sucesso: {len(conteudo)} caracteres")
            
            # Processar metadados
            arquivo_nome = os.path.basename(caminho)
            tamanho_bytes = os.path.getsize(caminho)
            
            # Extrair informações do conteúdo
            resumo = self._gerar_resumo(conteudo)
            palavras_chave = self._extrair_palavras_chave(conteudo) if not tags else tags
            
            # Criar documento no banco
            logger.info("Inserindo documento no banco de dados...")
            
            # Preparar chunks do conteúdo
            chunks = self._criar_chunks_inteligentes(conteudo)
            
            # Preparar dados do documento
            doc_data = {
                'title': titulo,
                'doc_type': tipo,
                'content_full': conteudo,
                'content_summary': resumo,
                'content_chunks': json.dumps(chunks),  # JSONB como string
                'department': departamento,
                'tags': palavras_chave,
                'category': tipo,  # Usar tipo como categoria
                'is_current': True,
                'version': '1.0'  # String ao invés de número
            }
            
            # Inserir no banco
            response = self.db.client.table('knowledge_base').insert(doc_data).execute()
            
            if not response.data:
                raise RuntimeError("Falha ao inserir documento no banco")
            
            doc_id = response.data[0]['id']
            logger.info(f"Documento inserido com ID: {doc_id}")
            
            # Gerar embeddings
            logger.info("Gerando embeddings para busca semântica...")
            num_embeddings = self.embeddings.processar_base_conhecimento(
                doc_id=doc_id,
                titulo=titulo,
                conteudo=conteudo,
                tipo=tipo,
                departamento=departamento
            )
            
            logger.info(f"✅ Documento importado com sucesso!")
            logger.info(f"   - ID: {doc_id}")
            logger.info(f"   - Embeddings criados: {num_embeddings}")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            raise
    
    def _gerar_resumo(self, conteudo: str, max_chars: int = 500) -> str:
        """
        Gera um resumo simples do conteúdo.
        
        Args:
            conteudo: Texto completo
            max_chars: Máximo de caracteres no resumo
            
        Returns:
            Resumo do conteúdo
        """
        # Pegar primeiras linhas não vazias
        linhas = [l.strip() for l in conteudo.split('\n') if l.strip()]
        
        resumo = ""
        for linha in linhas[:10]:  # Primeiras 10 linhas
            if len(resumo) + len(linha) > max_chars:
                break
            resumo += linha + " "
        
        # Truncar se necessário
        if len(resumo) > max_chars:
            resumo = resumo[:max_chars-3] + "..."
        
        return resumo.strip()
    
    def _extrair_palavras_chave(self, conteudo: str, num_palavras: int = 10) -> list:
        """
        Extrai palavras-chave do conteúdo.
        
        Args:
            conteudo: Texto completo
            num_palavras: Número de palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        # Palavras a ignorar (stop words em português)
        stop_words = {
            'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no',
            'nas', 'nos', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 'é', 'são',
            'foi', 'foram', 'ser', 'sendo', 'sido', 'ter', 'tendo', 'tido', 'que',
            'e', 'ou', 'mas', 'se', 'não', 'sim', 'um', 'uma', 'uns', 'umas'
        }
        
        # Extrair palavras
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', conteudo.lower())
        
        # Contar frequência
        freq = {}
        for palavra in palavras:
            if palavra not in stop_words:
                freq[palavra] = freq.get(palavra, 0) + 1
        
        # Ordenar por frequência e pegar top N
        palavras_frequentes = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        
        return [palavra for palavra, _ in palavras_frequentes[:num_palavras]]
    
    def _criar_chunks_inteligentes(self, conteudo: str, tamanho_chunk: int = 800) -> list:
        """
        Cria chunks inteligentes do conteúdo, respeitando parágrafos e seções.
        
        Args:
            conteudo: Texto completo
            tamanho_chunk: Tamanho aproximado de cada chunk
            
        Returns:
            Lista de chunks com metadados
        """
        chunks = []
        
        # Dividir por parágrafos duplos (seções)
        secoes = re.split(r'\n\n+', conteudo)
        
        chunk_atual = ""
        chunk_id = 0
        
        for secao in secoes:
            secao = secao.strip()
            if not secao:
                continue
            
            # Se adicionar a seção ultrapassar o tamanho, criar novo chunk
            if chunk_atual and len(chunk_atual) + len(secao) > tamanho_chunk:
                # Salvar chunk atual
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_atual.strip(),
                    'embedding': None  # Será preenchido pelo embeddings_handler
                })
                chunk_id += 1
                chunk_atual = secao
            else:
                # Adicionar ao chunk atual
                if chunk_atual:
                    chunk_atual += "\n\n" + secao
                else:
                    chunk_atual = secao
        
        # Adicionar último chunk se houver
        if chunk_atual:
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_atual.strip(),
                'embedding': None
            })
        
        # Se nenhum chunk foi criado, criar um único com todo o conteúdo
        if not chunks:
            chunks.append({
                'chunk_id': 0,
                'text': conteudo.strip(),
                'embedding': None
            })
        
        logger.info(f"Criados {len(chunks)} chunks do documento")
        return chunks
    
    def listar_documentos(self, departamento: Optional[str] = None):
        """
        Lista documentos existentes na base de conhecimento.
        
        Args:
            departamento: Filtrar por departamento (opcional)
        """
        try:
            query = self.db.client.table('knowledge_base').select(
                'id, title, doc_type, department, created_at, version'
            ).eq('is_current', True)
            
            if departamento:
                query = query.eq('department', departamento)
            
            response = query.order('created_at', desc=True).execute()
            
            if not response.data:
                print("Nenhum documento encontrado.")
                return
            
            print(f"\n📚 Documentos na Base de Conhecimento ({len(response.data)} total):\n")
            print(f"{'ID':<36} | {'Título':<40} | {'Tipo':<15} | {'Depto':<10} | {'Data':<10}")
            print("-" * 120)
            
            for doc in response.data:
                doc_id = doc['id']
                titulo = doc['title'][:40]
                tipo = doc['doc_type']
                depto = doc.get('department', '-')
                data = doc['created_at'][:10]
                
                print(f"{doc_id} | {titulo:<40} | {tipo:<15} | {depto:<10} | {data}")
            
        except Exception as e:
            logger.error(f"Erro ao listar documentos: {e}")
    
    def buscar_documentos(self, query: str, limite: int = 5):
        """
        Busca documentos usando busca semântica.
        
        Args:
            query: Texto de busca
            limite: Número máximo de resultados
        """
        try:
            logger.info(f"Buscando por: '{query}'")
            
            # Usar busca semântica via embeddings
            resultados = self.embeddings.buscar_por_similaridade(
                query=query,
                limite=limite
            )
            
            if not resultados:
                print("Nenhum resultado encontrado.")
                return
            
            print(f"\n🔍 Resultados da Busca ({len(resultados)} encontrados):\n")
            
            for i, resultado in enumerate(resultados, 1):
                print(f"{i}. {resultado.get('meeting_data', {}).get('title', 'Sem título')}")
                print(f"   Similaridade: {resultado.get('similarity', 0):.2%}")
                print(f"   Trecho: {resultado.get('chunk_text', '')[:150]}...")
                print()
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description='Importar base de conhecimento de arquivos .txt para Supabase'
    )
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    
    # Comando importar
    import_parser = subparsers.add_parser('importar', help='Importar arquivo .txt')
    import_parser.add_argument('arquivo', help='Caminho do arquivo .txt')
    import_parser.add_argument('--titulo', required=True, help='Título do documento')
    import_parser.add_argument('--tipo', default='manual', 
                             choices=['manual', 'procedimento', 'política', 'guia', 'outro'],
                             help='Tipo do documento')
    import_parser.add_argument('--departamento', help='Departamento relacionado')
    import_parser.add_argument('--tags', nargs='+', help='Tags/palavras-chave')
    
    # Comando listar
    list_parser = subparsers.add_parser('listar', help='Listar documentos')
    list_parser.add_argument('--departamento', help='Filtrar por departamento')
    
    # Comando buscar
    search_parser = subparsers.add_parser('buscar', help='Buscar documentos')
    search_parser.add_argument('query', help='Texto de busca')
    search_parser.add_argument('--limite', type=int, default=5, help='Número de resultados')
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    # Criar importador
    importador = ImportadorConhecimento()
    
    # Executar comando
    if args.comando == 'importar':
        try:
            doc_id = importador.processar_arquivo_txt(
                caminho=args.arquivo,
                titulo=args.titulo,
                tipo=args.tipo,
                departamento=args.departamento,
                tags=args.tags
            )
            print(f"\n✅ Documento importado com sucesso! ID: {doc_id}")
        except Exception as e:
            print(f"\n❌ Erro ao importar: {e}")
            sys.exit(1)
    
    elif args.comando == 'listar':
        importador.listar_documentos(departamento=args.departamento)
    
    elif args.comando == 'buscar':
        importador.buscar_documentos(query=args.query, limite=args.limite)


if __name__ == "__main__":
    main()