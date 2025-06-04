"""
Sistema Integrado de Agentes AURALIS - Classe principal que gerencia todos os agentes.
Fornece interface unificada para o sistema multi-agente.
"""

from typing import Dict, List, Any, Optional
import os
import json
from datetime import datetime
import asyncio

# Importar componentes do sistema
from .agente_orquestrador import AgenteOrquestrador
from .agente_consulta_inteligente import AgenteConsultaInteligente
from .agente_brainstorm import AgenteBrainstorm
from .comunicacao_agentes import ComunicacaoAgentes, MensagemAgente, TipoMensagem
from .otimizador import otimizador_global


class SistemaAgentes:
    """
    Sistema principal que integra todos os agentes do AURALIS.
    
    Responsabilidades:
    - Inicializar e configurar todos os agentes
    - Gerenciar comunicação entre agentes
    - Fornecer interface unificada para o frontend
    - Manter contexto global do sistema
    - Coletar e reportar estatísticas
    """
    
    def __init__(self, modo_debug: bool = False):
        """
        Inicializa o sistema de agentes.
        
        Args:
            modo_debug: Se True, ativa logs detalhados
        """
        self.modo_debug = modo_debug
        
        # Sistema de comunicação
        self.comunicacao = ComunicacaoAgentes()
        
        # Contexto global compartilhado
        self.contexto_global = {
            "sistema": "AURALIS",
            "versao": "1.0.0",
            "inicializado_em": datetime.now().isoformat(),
            "modo": "simulado" if not os.getenv("OPENAI_API_KEY") else "producao"
        }
        
        # Inicializar agentes
        self._inicializar_agentes()
        
        # Configurar otimizador
        self.otimizador = otimizador_global
        
        # Estatísticas do sistema
        self.estatisticas_sistema = {
            "total_interacoes": 0,
            "tempo_total_processamento": 0.0,
            "erros": 0
        }
        
        print(f"[SISTEMA] Sistema AURALIS inicializado em modo: {self.contexto_global['modo']}")
    
    def _inicializar_agentes(self):
        """Inicializa todos os agentes do sistema"""
        # Criar instâncias dos agentes
        self.orquestrador = AgenteOrquestrador()
        self.consultor = AgenteConsultaInteligente()
        self.criativo = AgenteBrainstorm()
        
        # Configurar referências diretas no orquestrador
        self.orquestrador.definir_agentes(
            agente_consulta=self.consultor,
            agente_brainstorm=self.criativo
        )
        
        # Registrar agentes no sistema de comunicação
        self._registrar_agentes()
        
        if self.modo_debug:
            print("[SISTEMA] Todos os agentes foram inicializados")
    
    def _registrar_agentes(self):
        """Registra agentes no sistema de comunicação"""
        # Registrar cada agente com seus callbacks
        self.comunicacao.registrar_agente(
            self.orquestrador.nome,
            self.orquestrador,
            self._criar_callback_agente(self.orquestrador)
        )
        
        self.comunicacao.registrar_agente(
            self.consultor.nome,
            self.consultor,
            self._criar_callback_agente(self.consultor)
        )
        
        self.comunicacao.registrar_agente(
            self.criativo.nome,
            self.criativo,
            self._criar_callback_agente(self.criativo)
        )
    
    def _criar_callback_agente(self, agente):
        """
        Cria callback para processar mensagens de um agente.
        
        Args:
            agente: Instância do agente
            
        Returns:
            Callable: Função callback
        """
        def callback(mensagem: MensagemAgente, agente_ref):
            if self.modo_debug:
                print(f"[CALLBACK] {agente.nome} recebeu mensagem de {mensagem.remetente}")
            
            # Processar mensagem através do agente
            if hasattr(agente, 'processar_mensagem'):
                return agente.processar_mensagem(
                    mensagem.conteudo.get("mensagem", ""),
                    mensagem.contexto
                )
        
        return callback
    
    def processar_mensagem_usuario(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        """
        Processa uma mensagem do usuário através do sistema.
        
        Args:
            mensagem: Mensagem do usuário
            contexto: Contexto adicional (opcional)
            
        Returns:
            str: Resposta do sistema
        """
        inicio = datetime.now()
        
        try:
            # Atualizar contexto global
            contexto_completo = self.contexto_global.copy()
            if contexto:
                contexto_completo.update(contexto)
            
            # Adicionar timestamp
            contexto_completo["timestamp_interacao"] = datetime.now().isoformat()
            
            # Verificar cache primeiro
            cache_key = self.otimizador.cache._gerar_chave(mensagem, contexto_completo)
            resposta_cache = self.otimizador.cache.get(cache_key)
            
            if resposta_cache:
                if self.modo_debug:
                    print("[SISTEMA] Resposta encontrada no cache")
                return resposta_cache
            
            # Processar através do orquestrador
            resposta = self.orquestrador.processar_mensagem(mensagem, contexto_completo)
            
            # Armazenar no cache
            self.otimizador.cache.set(cache_key, resposta)
            
            # Atualizar estatísticas
            tempo_processamento = (datetime.now() - inicio).total_seconds()
            self.estatisticas_sistema["total_interacoes"] += 1
            self.estatisticas_sistema["tempo_total_processamento"] += tempo_processamento
            
            if self.modo_debug:
                print(f"[SISTEMA] Processamento concluído em {tempo_processamento:.2f}s")
            
            return resposta
            
        except Exception as e:
            self.estatisticas_sistema["erros"] += 1
            erro_msg = f"Erro ao processar mensagem: {str(e)}"
            
            if self.modo_debug:
                print(f"[SISTEMA] {erro_msg}")
            
            return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
    
    def executar_analise_completa(self, topico: str) -> Dict[str, Any]:
        """
        Executa uma análise completa sobre um tópico usando todos os agentes.
        
        Args:
            topico: Tópico para análise
            
        Returns:
            Dict: Resultados consolidados
        """
        print(f"[SISTEMA] Iniciando análise completa sobre: {topico}")
        
        resultado = {
            "topico": topico,
            "timestamp": datetime.now().isoformat(),
            "analises": {}
        }
        
        try:
            # 1. Buscar informações existentes
            print("[SISTEMA] Fase 1: Buscando informações...")
            consulta = f"Buscar todas as informações sobre {topico}"
            resultado["analises"]["informacoes"] = self.consultor.processar_mensagem(
                consulta, 
                self.contexto_global
            )
            
            # 2. Gerar ideias criativas
            print("[SISTEMA] Fase 2: Gerando ideias criativas...")
            brainstorm = f"Gerar ideias inovadoras para {topico}"
            resultado["analises"]["ideias"] = self.criativo.processar_mensagem(
                brainstorm,
                self.contexto_global
            )
            
            # 3. Análise executiva pelo orquestrador
            print("[SISTEMA] Fase 3: Consolidando análise executiva...")
            resultado["resumo_executivo"] = self.orquestrador.gerar_resumo_executivo(
                topico,
                resultado["analises"]
            )
            
            print("[SISTEMA] Análise completa concluída")
            
        except Exception as e:
            resultado["erro"] = str(e)
            print(f"[SISTEMA] Erro durante análise: {str(e)}")
        
        return resultado
    
    def buscar_informacoes(self, consulta: str, filtros: Dict[str, Any] = None) -> str:
        """
        Busca informações específicas usando o agente de consulta.
        
        Args:
            consulta: Consulta de busca
            filtros: Filtros adicionais (opcional)
            
        Returns:
            str: Resultados da busca
        """
        contexto = self.contexto_global.copy()
        if filtros:
            contexto["filtros"] = filtros
        
        return self.consultor.processar_mensagem(consulta, contexto)
    
    def gerar_ideias(self, desafio: str, tecnica: Optional[str] = None) -> str:
        """
        Gera ideias criativas para um desafio.
        
        Args:
            desafio: Descrição do desafio
            tecnica: Técnica específica de brainstorming (opcional)
            
        Returns:
            str: Ideias geradas
        """
        contexto = self.contexto_global.copy()
        if tecnica:
            contexto["tecnica_preferida"] = tecnica
        
        return self.criativo.processar_mensagem(desafio, contexto)
    
    def atualizar_contexto_global(self, novo_contexto: Dict[str, Any]):
        """
        Atualiza o contexto global do sistema.
        
        Args:
            novo_contexto: Novo contexto para adicionar/atualizar
        """
        self.contexto_global.update(novo_contexto)
        
        # Propagar para todos os agentes
        self.orquestrador.atualizar_contexto(novo_contexto)
        self.consultor.atualizar_contexto(novo_contexto)
        self.criativo.atualizar_contexto(novo_contexto)
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Obtém estatísticas completas do sistema.
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        # Coletar estatísticas de cada componente
        stats = {
            "sistema": {
                "modo": self.contexto_global["modo"],
                "inicializado_em": self.contexto_global["inicializado_em"],
                "total_interacoes": self.estatisticas_sistema["total_interacoes"],
                "tempo_medio_resposta": (
                    self.estatisticas_sistema["tempo_total_processamento"] / 
                    max(1, self.estatisticas_sistema["total_interacoes"])
                ),
                "erros": self.estatisticas_sistema["erros"]
            },
            "comunicacao": self.comunicacao.obter_estatisticas(),
            "otimizacao": self.otimizador.estatisticas_completas(),
            "agentes": {
                "orquestrador": {
                    "nome": self.orquestrador.nome,
                    "historico": len(self.orquestrador.historico_conversas),
                    "agentes_conectados": sum(1 for a in [
                        self.orquestrador.agente_consulta,
                        self.orquestrador.agente_brainstorm
                    ] if a)
                },
                "consultor": {
                    "nome": self.consultor.nome,
                    "historico": len(self.consultor.historico_conversas)
                },
                "criativo": {
                    "nome": self.criativo.nome,
                    "historico": len(self.criativo.historico_conversas)
                }
            }
        }
        
        return stats
    
    def obter_historico_conversas(self) -> Dict[str, List[Dict]]:
        """
        Obtém histórico de conversas de todos os agentes.
        
        Returns:
            Dict: Histórico organizado por agente
        """
        return {
            "orquestrador": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in self.orquestrador.historico_conversas
            ],
            "consultor": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in self.consultor.historico_conversas
            ],
            "criativo": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in self.criativo.historico_conversas
            ]
        }
    
    def exportar_sessao(self, caminho: Optional[str] = None) -> str:
        """
        Exporta toda a sessão para análise ou backup.
        
        Args:
            caminho: Caminho do arquivo (opcional)
            
        Returns:
            str: JSON com dados da sessão
        """
        sessao = {
            "timestamp_exportacao": datetime.now().isoformat(),
            "contexto_global": self.contexto_global,
            "estatisticas": self.obter_estatisticas(),
            "historico_conversas": self.obter_historico_conversas(),
            "historico_comunicacoes": [
                msg.to_dict() for msg in self.comunicacao.obter_historico()
            ]
        }
        
        json_data = json.dumps(sessao, ensure_ascii=False, indent=2)
        
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(json_data)
            print(f"[SISTEMA] Sessão exportada para: {caminho}")
        
        return json_data
    
    def resetar_sistema(self):
        """Reseta o sistema para estado inicial"""
        # Limpar históricos dos agentes
        self.orquestrador.limpar_historico()
        self.consultor.limpar_historico()
        self.criativo.limpar_historico()
        
        # Limpar cache
        self.otimizador.limpar_cache()
        
        # Limpar filas de comunicação
        self.comunicacao.limpar_filas()
        
        # Resetar estatísticas
        self.estatisticas_sistema = {
            "total_interacoes": 0,
            "tempo_total_processamento": 0.0,
            "erros": 0
        }
        
        print("[SISTEMA] Sistema resetado com sucesso")
    
    def modo_teste(self):
        """Executa testes básicos do sistema"""
        print("\n=== MODO TESTE AURALIS ===\n")
        
        testes = [
            ("Buscar reuniões sobre transformação digital", "CONSULTA"),
            ("Gerar ideias para melhorar a comunicação entre equipes", "BRAINSTORM"),
            ("Como posso ajudar você hoje?", "GERAL"),
            ("Buscar informações sobre IA e gerar ideias inovadoras", "MÚLTIPLA")
        ]
        
        for pergunta, tipo_esperado in testes:
            print(f"📝 Teste: {pergunta}")
            print(f"   Tipo esperado: {tipo_esperado}")
            
            resposta = self.processar_mensagem_usuario(pergunta)
            print(f"   ✅ Resposta recebida ({len(resposta)} caracteres)")
            print(f"   Preview: {resposta[:100]}...\n")
        
        # Mostrar estatísticas
        stats = self.obter_estatisticas()
        print("\n📊 Estatísticas do Teste:")
        print(f"   Total de interações: {stats['sistema']['total_interacoes']}")
        print(f"   Taxa de cache: {stats['otimizacao']['cache']['taxa_hit']}")
        print(f"   Mensagens processadas: {stats['comunicacao']['mensagens_processadas']}")
        
        print("\n✅ Testes concluídos!")
    
    def __repr__(self):
        return f"SistemaAgentes(modo={self.contexto_global['modo']}, agentes=3, interacoes={self.estatisticas_sistema['total_interacoes']})"


# Funções auxiliares para facilitar o uso
def criar_sistema_auralis(modo_debug: bool = False) -> SistemaAgentes:
    """
    Cria e retorna uma instância do Sistema AURALIS.
    
    Args:
        modo_debug: Ativar modo debug
        
    Returns:
        SistemaAgentes: Sistema inicializado
    """
    return SistemaAgentes(modo_debug=modo_debug)


def processar_pergunta_simples(pergunta: str) -> str:
    """
    Processa uma pergunta simples criando um sistema temporário.
    
    Args:
        pergunta: Pergunta do usuário
        
    Returns:
        str: Resposta do sistema
    """
    sistema = SistemaAgentes()
    return sistema.processar_mensagem_usuario(pergunta)