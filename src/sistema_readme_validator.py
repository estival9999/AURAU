#!/usr/bin/env python3
"""
Sistema de Validação e Criação de READMEs com Garantia de Ordem Cronológica
===========================================================================

Este módulo GARANTE que READMEs sejam criados SEMPRE em ordem cronológica.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
import hashlib
import sys

class ValidadorREADME:
    """Validador que IMPOSSIBILITA criação de READMEs fora de ordem"""
    
    def __init__(self):
        self.readmes_dir = "/home/mateus/Área de trabalho/X_AURA/READMES_COMP"
        self.lock_file = os.path.join(self.readmes_dir, ".readme_lock.json")
        self.criar_estrutura()
    
    def criar_estrutura(self):
        """Cria estrutura necessária"""
        os.makedirs(self.readmes_dir, exist_ok=True)
    
    def obter_estado_atual(self):
        """Obtém estado atual do sistema de READMEs"""
        estado = {
            'ultimo_timestamp': None,
            'ultimo_id': 0,
            'readmes_existentes': [],
            'hash_verificacao': None
        }
        
        # Listar todos os READMEs existentes
        if os.path.exists(self.readmes_dir):
            readmes = []
            for f in os.listdir(self.readmes_dir):
                if f.startswith("README_") and f.endswith(".md"):
                    filepath = os.path.join(self.readmes_dir, f)
                    timestamp = os.path.getctime(filepath)
                    readmes.append({
                        'nome': f,
                        'timestamp': timestamp,
                        'data_criacao': datetime.fromtimestamp(timestamp)
                    })
            
            # Ordenar por timestamp real
            readmes.sort(key=lambda x: x['timestamp'])
            
            if readmes:
                estado['readmes_existentes'] = readmes
                estado['ultimo_timestamp'] = readmes[-1]['timestamp']
                estado['ultimo_id'] = len(readmes)
        
        # Gerar hash de verificação (converter datetime para string)
        readmes_serializaveis = [
            {
                'nome': r['nome'],
                'timestamp': r['timestamp'],
                'data_criacao': r['data_criacao'].isoformat()
            }
            for r in readmes
        ]
        conteudo = json.dumps(readmes_serializaveis, sort_keys=True)
        estado['hash_verificacao'] = hashlib.sha256(conteudo.encode()).hexdigest()
        
        return estado
    
    def validar_novo_readme(self, nome_proposto=None):
        """Valida se um novo README pode ser criado"""
        estado = self.obter_estado_atual()
        agora = datetime.now()
        
        # REGRA 1: Timestamp atual DEVE ser posterior ao último README
        if estado['ultimo_timestamp']:
            ultimo_dt = datetime.fromtimestamp(estado['ultimo_timestamp'])
            if agora <= ultimo_dt:
                raise ValueError(
                    f"❌ ERRO CRÍTICO: Tentativa de criar README com timestamp "
                    f"anterior ou igual ao último!\n"
                    f"Último: {ultimo_dt.strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Atual: {agora.strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Sistema de proteção ativado!"
                )
        
        # REGRA 2: ID deve ser sequencial
        proximo_id = estado['ultimo_id'] + 1
        
        # REGRA 3: Nome deve usar timestamp ATUAL
        nome_correto = f"README_{agora.strftime('%d_%m_%H%M')}_{proximo_id:03d}.md"
        
        if nome_proposto and nome_proposto != nome_correto:
            raise ValueError(
                f"❌ ERRO: Nome proposto '{nome_proposto}' não corresponde ao "
                f"timestamp atual!\n"
                f"Nome correto: '{nome_correto}'\n"
                f"Use SEMPRE o timestamp do momento da criação!"
            )
        
        return {
            'nome': nome_correto,
            'timestamp': agora.timestamp(),
            'id': proximo_id,
            'validado': True
        }
    
    def criar_readme_seguro(self, conteudo, titulo_customizado=None):
        """Cria README com garantia de ordem cronológica"""
        try:
            # Validar criação
            validacao = self.validar_novo_readme()
            
            # Criar arquivo
            filepath = os.path.join(self.readmes_dir, validacao['nome'])
            
            # Adicionar cabeçalho de validação ao conteúdo
            cabecalho = f"""# {validacao['nome']}

<!-- VALIDAÇÃO AUTOMÁTICA -->
<!-- Criado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} -->
<!-- ID Sequencial: {validacao['id']:03d} -->
<!-- Hash de Validação: {hashlib.sha256(conteudo.encode()).hexdigest()[:16]} -->

"""
            
            conteudo_final = cabecalho + conteudo
            
            # Escrever arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(conteudo_final)
            
            print(f"✅ README criado com sucesso: {validacao['nome']}")
            print(f"   Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"   ID Sequencial: {validacao['id']:03d}")
            
            # Salvar estado
            self.salvar_estado_lock(validacao)
            
            return validacao['nome']
            
        except Exception as e:
            print(f"❌ Falha ao criar README: {str(e)}")
            raise
    
    def salvar_estado_lock(self, validacao):
        """Salva estado atual em arquivo de lock"""
        lock_data = {
            'ultimo_readme': validacao['nome'],
            'ultimo_timestamp': validacao['timestamp'],
            'ultimo_id': validacao['id'],
            'data_criacao': datetime.now().isoformat()
        }
        
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
    
    def verificar_integridade(self):
        """Verifica integridade do sistema de READMEs"""
        print("🔍 Verificando integridade do sistema...")
        
        estado = self.obter_estado_atual()
        problemas = []
        
        # Verificar ordem cronológica
        for i in range(1, len(estado['readmes_existentes'])):
            atual = estado['readmes_existentes'][i]
            anterior = estado['readmes_existentes'][i-1]
            
            if atual['timestamp'] <= anterior['timestamp']:
                problemas.append(
                    f"❌ {atual['nome']} tem timestamp anterior ou igual a "
                    f"{anterior['nome']}"
                )
        
        # Verificar consistência entre nome e timestamp real
        print(f"\n📊 Total de READMEs: {len(estado['readmes_existentes'])}")
        
        for readme in estado['readmes_existentes']:
            # Extrair data do nome
            match = re.match(r"README_(\d{2})_(\d{2})_(\d{2})(\d{2})_(\d{3})\.md", readme['nome'])
            if match:
                dia, mes, hora, minuto, id_seq = match.groups()
                try:
                    # Assumir ano 2025 para comparação
                    dt_nome = datetime(2025, int(mes), int(dia), int(hora), int(minuto))
                    dt_real = readme['data_criacao']
                    
                    # Se diferença maior que 1 hora, é problema
                    diff_horas = abs((dt_real - dt_nome).total_seconds()) / 3600
                    if diff_horas > 1:
                        problemas.append(
                            f"❌ {readme['nome']}: data no nome ({dt_nome.strftime('%d/%m %H:%M')}) "
                            f"difere da real ({dt_real.strftime('%d/%m %H:%M')}) em {diff_horas:.1f} horas"
                        )
                except ValueError as e:
                    problemas.append(f"❌ {readme['nome']}: data inválida no nome")
        
        # Verificar IDs duplicados por data
        ids_por_data = {}
        for readme in estado['readmes_existentes']:
            match = re.match(r"README_(\d{2})_(\d{2})_\d{4}_(\d{3})\.md", readme['nome'])
            if match:
                dia, mes, id_seq = match.groups()
                data_key = f"{mes}_{dia}"
                if data_key not in ids_por_data:
                    ids_por_data[data_key] = []
                ids_por_data[data_key].append((readme['nome'], int(id_seq)))
        
        for data_key, items in ids_por_data.items():
            ids = [item[1] for item in items]
            if len(ids) != len(set(ids)):
                problemas.append(f"❌ IDs duplicados na data {data_key}")
        
        if problemas:
            print("\n⚠️  PROBLEMAS ENCONTRADOS:")
            for p in problemas:
                print(f"   {p}")
            print(f"\n❌ Total de problemas: {len(problemas)}")
            return False
        else:
            print("✅ Sistema íntegro! Todos os READMEs em ordem cronológica.")
            return True

# Funções auxiliares para uso direto
def criar_readme_automatico(conteudo, titulo=None):
    """Função helper para criar README com validação automática"""
    validador = ValidadorREADME()
    return validador.criar_readme_seguro(conteudo, titulo)

def verificar_sistema():
    """Verifica integridade do sistema"""
    validador = ValidadorREADME()
    return validador.verificar_integridade()

def obter_proximo_nome_readme():
    """Obtém o próximo nome válido de README"""
    validador = ValidadorREADME()
    validacao = validador.validar_novo_readme()
    return validacao['nome']

if __name__ == "__main__":
    # Teste do sistema
    if len(sys.argv) > 1 and sys.argv[1] == "--verificar":
        verificar_sistema()
    else:
        print("Sistema de Validação de READMEs")
        print("================================")
        print("Use --verificar para verificar integridade")
        print("\nPróximo README válido:", obter_proximo_nome_readme())