"""
Sistema de Comunicação Inter-Agentes - Barramento de mensagens para o AURALIS.
Permite comunicação assíncrona, broadcast de eventos e rastreamento de mensagens.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid
import asyncio
from collections import defaultdict, deque
import json


class TipoMensagem(Enum):
    """Tipos de mensagem no sistema de comunicação.
    
    Define os diferentes tipos de mensagens que podem trafegar entre agentes.
    """
    SOLICITACAO = "SOLICITACAO"    # Solicitação de processamento
    RESPOSTA = "RESPOSTA"          # Resposta a uma solicitação
    NOTIFICACAO = "NOTIFICACAO"    # Notificação de evento
    ERRO = "ERRO"                  # Mensagem de erro
    BROADCAST = "BROADCAST"        # Mensagem para todos
    HEARTBEAT = "HEARTBEAT"        # Verificação de vida
    STATUS = "STATUS"              # Atualização de status


class StatusMensagem(Enum):
    """Status de processamento da mensagem.
    
    Rastreia o ciclo de vida de cada mensagem no sistema.
    """
    PENDENTE = "PENDENTE"          # Aguardando processamento
    PROCESSANDO = "PROCESSANDO"    # Em processamento
    CONCLUIDO = "CONCLUIDO"        # Processamento concluído
    ERRO = "ERRO"                  # Erro no processamento
    CANCELADO = "CANCELADO"        # Processamento cancelado
    TIMEOUT = "TIMEOUT"            # Tempo limite excedido


@dataclass
class MensagemAgente:
    """Estrutura de dados para mensagens entre agentes.
    
    Contém todas as informações necessárias para comunicação entre agentes.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # ID único da mensagem
    tipo: TipoMensagem = TipoMensagem.SOLICITACAO              # Tipo da mensagem
    remetente: str = ""                                         # Agente que envia
    destinatario: str = ""                                      # Agente que recebe
    conteudo: Dict[str, Any] = field(default_factory=dict)     # Conteúdo da mensagem
    contexto: Dict[str, Any] = field(default_factory=dict)     # Contexto adicional
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # Hora de criação
    status: StatusMensagem = StatusMensagem.PENDENTE           # Status atual
    prioridade: int = 5                                         # 1-10 (1 = mais alta)
    resposta_para: Optional[str] = None                        # ID da mensagem original se for resposta
    tentativas: int = 0                                         # Número de tentativas
    max_tentativas: int = 3                                     # Máximo de tentativas
    timeout_segundos: int = 30                                  # Tempo limite em segundos
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte mensagem para dicionário serializavel."""
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "remetente": self.remetente,
            "destinatario": self.destinatario,
            "conteudo": self.conteudo,
            "contexto": self.contexto,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "prioridade": self.prioridade,
            "resposta_para": self.resposta_para,
            "tentativas": self.tentativas
        }


class ComunicacaoAgentes:
    """
    Sistema central de comunicação entre agentes.
    
    Funcionalidades:
    - Roteamento de mensagens
    - Filas por prioridade
    - Callbacks assíncronos
    - Broadcast para múltiplos agentes
    - Histórico e estatísticas
    """
    
    def __init__(self, max_historico: int = 1000):
        """
        Inicializa o sistema de comunicação.
        
        Args:
            max_historico: Número máximo de mensagens no histórico
        """
        # ===== REGISTRO DE AGENTES =====
        self.agentes_registrados: Dict[str, Any] = {}
        
        # ===== FILAS DE MENSAGENS =====
        # Estrutura: {nome_agente: {prioridade: fila}}
        # 10 níveis de prioridade (1 = mais alta, 10 = mais baixa)
        self.filas_mensagens: Dict[str, Dict[int, deque]] = defaultdict(
            lambda: {i: deque() for i in range(1, 11)}
        )
        
        # ===== CALLBACKS =====
        # Funções a serem chamadas quando um agente recebe mensagem
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # ===== HISTÓRICO =====
        # Mantém histórico limitado de mensagens
        self.historico: deque = deque(maxlen=max_historico)
        
        # ===== ESTATÍSTICAS =====
        # Métricas do sistema de comunicação
        self.estatisticas = {
            "mensagens_enviadas": 0,
            "mensagens_processadas": 0,
            "mensagens_erro": 0,
            "tempo_total_processamento": 0.0,
            "mensagens_por_tipo": defaultdict(int),
            "mensagens_por_agente": defaultdict(int)
        }
        
        # ===== CONTROLE DE CONCORRÊNCIA =====
        # Lock para operações thread-safe
        self.lock = asyncio.Lock()
        
        # Flag para controlar se o sistema está ativo
        self.ativo = True
        
        # Rastreamento de mensagens em processamento
        self.mensagens_processando: Dict[str, MensagemAgente] = {}
    
    def registrar_agente(self, nome: str, agente: Any, callback: Optional[Callable] = None):
        """
        Registra um agente no sistema de comunicação.
        
        Args:
            nome: Nome único do agente
            agente: Instância do agente
            callback: Função callback para processar mensagens
        """
        self.agentes_registrados[nome] = agente
        
        # Registra callback se fornecido
        if callback:
            self.callbacks[nome].append(callback)
        
        print(f"[COMUNICAÇÃO] Agente '{nome}' registrado com sucesso")
    
    def desregistrar_agente(self, nome: str):
        """
        Remove um agente do sistema.
        
        Args:
            nome: Nome do agente
        """
        # Remove todas as referências ao agente
        if nome in self.agentes_registrados:
            del self.agentes_registrados[nome]
            
        if nome in self.callbacks:
            del self.callbacks[nome]
            
        if nome in self.filas_mensagens:
            del self.filas_mensagens[nome]
        
        print(f"[COMUNICAÇÃO] Agente '{nome}' desregistrado")
    
    async def enviar_mensagem(self, mensagem: MensagemAgente) -> Dict[str, Any]:
        """
        Envia uma mensagem para um agente específico.
        
        Args:
            mensagem: Mensagem a enviar
            
        Returns:
            Dict: Resultado do envio
        """
        async with self.lock:
            # ===== VALIDAÇÃO DA MENSAGEM =====
            if not mensagem.destinatario:
                return {"sucesso": False, "erro": "Destinatário não especificado"}
            
            if mensagem.destinatario not in self.agentes_registrados:
                return {"sucesso": False, "erro": f"Agente '{mensagem.destinatario}' não registrado"}
            
            # ===== ENFILEIRAMENTO =====
            # Adiciona mensagem na fila de prioridade correspondente
            self.filas_mensagens[mensagem.destinatario][mensagem.prioridade].append(mensagem)
            
            # ===== ATUALIZAÇÃO DE ESTATÍSTICAS =====
            self.estatisticas["mensagens_enviadas"] += 1
            self.estatisticas["mensagens_por_tipo"][mensagem.tipo.value] += 1
            self.estatisticas["mensagens_por_agente"][mensagem.remetente] += 1
            
            # Adiciona ao histórico para rastreamento
            self.historico.append(mensagem)
            
            # ===== PROCESSAMENTO =====
            resultado = await self._processar_mensagem(mensagem)
            
            return resultado
    
    async def _processar_mensagem(self, mensagem: MensagemAgente) -> Dict[str, Any]:
        """
        Processa uma mensagem específica.
        
        Args:
            mensagem: Mensagem para processar
            
        Returns:
            Dict: Resultado do processamento
        """
        inicio = datetime.now()
        mensagem.status = StatusMensagem.PROCESSANDO
        self.mensagens_processando[mensagem.id] = mensagem
        
        try:
            # ===== OBTENÇÃO DO AGENTE =====
            agente = self.agentes_registrados[mensagem.destinatario]
            
            # ===== EXECUÇÃO DE CALLBACKS =====
            # Executa todos os callbacks registrados para o agente
            for callback in self.callbacks.get(mensagem.destinatario, []):
                await self._executar_callback(callback, mensagem, agente)
            
            # ===== PROCESSAMENTO DIRETO =====
            # Se o agente tem método processar_mensagem, chama diretamente
            if hasattr(agente, 'processar_mensagem'):
                resposta = agente.processar_mensagem(
                    mensagem.conteudo.get("mensagem", ""),
                    mensagem.contexto
                )
                
                # ===== CRIAÇÃO DE RESPOSTA =====
                # Se foi uma solicitação, cria mensagem de resposta
                if mensagem.tipo == TipoMensagem.SOLICITACAO:
                    msg_resposta = MensagemAgente(
                        tipo=TipoMensagem.RESPOSTA,
                        remetente=mensagem.destinatario,
                        destinatario=mensagem.remetente,
                        conteudo={"resposta": resposta},
                        contexto=mensagem.contexto,
                        resposta_para=mensagem.id
                    )
                    
                    # Envia resposta de volta ao remetente original
                    await self.enviar_mensagem(msg_resposta)
            
            # Marca mensagem como concluída
            mensagem.status = StatusMensagem.CONCLUIDO
            
            # ===== ATUALIZAÇÃO DE MÉTRICAS =====
            tempo_processamento = (datetime.now() - inicio).total_seconds()
            self.estatisticas["mensagens_processadas"] += 1
            self.estatisticas["tempo_total_processamento"] += tempo_processamento
            
            return {
                "sucesso": True,
                "mensagem_id": mensagem.id,
                "tempo_processamento": tempo_processamento
            }
            
        except Exception as e:
            # ===== TRATAMENTO DE ERRO =====
            mensagem.status = StatusMensagem.ERRO
            self.estatisticas["mensagens_erro"] += 1
            
            return {
                "sucesso": False,
                "mensagem_id": mensagem.id,
                "erro": str(e)
            }
            
        finally:
            # ===== LIMPEZA =====
            # Remove mensagem da lista de processamento
            if mensagem.id in self.mensagens_processando:
                del self.mensagens_processando[mensagem.id]
    
    async def _executar_callback(self, callback: Callable, mensagem: MensagemAgente, agente: Any):
        """
        Executa um callback de forma segura.
        
        Args:
            callback: Função callback
            mensagem: Mensagem recebida
            agente: Agente destinatário
        """
        try:
            # Verifica se callback é assíncrono ou síncrono
            if asyncio.iscoroutinefunction(callback):
                await callback(mensagem, agente)
            else:
                callback(mensagem, agente)
        except Exception as e:
            print(f"[COMUNICAÇÃO] Erro em callback: {str(e)}")
    
    async def broadcast(self, remetente: str, conteudo: Dict[str, Any], 
                       excluir: List[str] = None, tipo: TipoMensagem = TipoMensagem.BROADCAST) -> Dict[str, Any]:
        """
        Envia mensagem para todos os agentes registrados.
        
        Args:
            remetente: Agente que envia o broadcast
            conteudo: Conteúdo da mensagem
            excluir: Lista de agentes para excluir
            tipo: Tipo da mensagem
            
        Returns:
            Dict: Resultado do broadcast
        """
        # ===== PREPARAÇÃO DO BROADCAST =====
        excluir = excluir or []
        excluir.append(remetente)  # Não enviar para si mesmo
        
        # Filtra destinatários
        destinatarios = [nome for nome in self.agentes_registrados 
                        if nome not in excluir]
        
        resultados = {
            "total_destinatarios": len(destinatarios),
            "sucessos": 0,
            "falhas": 0,
            "detalhes": {}
        }
        
        # ===== ENVIO PARA MÚLTIPLOS DESTINATÁRIOS =====
        for destinatario in destinatarios:
            mensagem = MensagemAgente(
                tipo=tipo,
                remetente=remetente,
                destinatario=destinatario,
                conteudo=conteudo,
                prioridade=5  # Prioridade média para broadcasts
            )
            
            resultado = await self.enviar_mensagem(mensagem)
            
            if resultado["sucesso"]:
                resultados["sucessos"] += 1
            else:
                resultados["falhas"] += 1
            
            resultados["detalhes"][destinatario] = resultado
        
        return resultados
    
    def obter_proxima_mensagem(self, agente: str) -> Optional[MensagemAgente]:
        """
        Obtém a próxima mensagem da fila de um agente (por prioridade).
        
        Args:
            agente: Nome do agente
            
        Returns:
            MensagemAgente ou None
        """
        if agente not in self.filas_mensagens:
            return None
        
        # ===== BUSCA POR PRIORIDADE =====
        # Verifica filas da maior para menor prioridade
        for prioridade in range(1, 11):
            fila = self.filas_mensagens[agente][prioridade]
            if fila:
                return fila.popleft()
        
        return None
    
    def obter_historico(self, filtros: Dict[str, Any] = None) -> List[MensagemAgente]:
        """
        Obtém histórico de mensagens com filtros opcionais.
        
        Args:
            filtros: Dicionário com filtros (remetente, destinatario, tipo, status)
            
        Returns:
            List[MensagemAgente]: Mensagens filtradas
        """
        if not filtros:
            return list(self.historico)
        
        # ===== FILTRAGEM DO HISTÓRICO =====
        mensagens_filtradas = []
        
        for msg in self.historico:
            incluir = True
            
            if "remetente" in filtros and msg.remetente != filtros["remetente"]:
                incluir = False
            
            if "destinatario" in filtros and msg.destinatario != filtros["destinatario"]:
                incluir = False
            
            if "tipo" in filtros and msg.tipo.value != filtros["tipo"]:
                incluir = False
            
            if "status" in filtros and msg.status.value != filtros["status"]:
                incluir = False
            
            if incluir:
                mensagens_filtradas.append(msg)
        
        return mensagens_filtradas
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do sistema de comunicação.
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        # ===== CÁLCULO DE MÉTRICAS =====
        tempo_medio = 0.0
        if self.estatisticas["mensagens_processadas"] > 0:
            tempo_medio = (self.estatisticas["tempo_total_processamento"] / 
                          self.estatisticas["mensagens_processadas"])
        
        # Conta total de mensagens aguardando nas filas
        mensagens_em_fila = 0
        for agente_filas in self.filas_mensagens.values():
            for fila in agente_filas.values():
                mensagens_em_fila += len(fila)
        
        return {
            "mensagens_enviadas": self.estatisticas["mensagens_enviadas"],
            "mensagens_processadas": self.estatisticas["mensagens_processadas"],
            "mensagens_erro": self.estatisticas["mensagens_erro"],
            "tempo_medio_resposta": round(tempo_medio, 3),
            "agentes_ativos": len(self.agentes_registrados),
            "mensagens_em_fila": mensagens_em_fila,
            "mensagens_processando": len(self.mensagens_processando),
            "tipos_mensagem": dict(self.estatisticas["mensagens_por_tipo"]),
            "mensagens_por_agente": dict(self.estatisticas["mensagens_por_agente"]),
            "tamanho_historico": len(self.historico)
        }
    
    def limpar_filas(self, agente: Optional[str] = None):
        """
        Limpa filas de mensagens.
        
        Args:
            agente: Nome do agente (None para limpar todas)
        """
        # ===== LIMPEZA DE FILAS =====
        if agente:
            # Limpa filas de um agente específico
            if agente in self.filas_mensagens:
                for fila in self.filas_mensagens[agente].values():
                    fila.clear()
        else:
            # Limpa todas as filas
            for agente_filas in self.filas_mensagens.values():
                for fila in agente_filas.values():
                    fila.clear()
    
    def exportar_historico(self, caminho: Optional[str] = None) -> str:
        """
        Exporta histórico de comunicações.
        
        Args:
            caminho: Caminho do arquivo (opcional)
            
        Returns:
            str: JSON com o histórico
        """
        dados_exportacao = {
            "timestamp_exportacao": datetime.now().isoformat(),
            "estatisticas": self.obter_estatisticas(),
            "agentes_registrados": list(self.agentes_registrados.keys()),
            "historico": [msg.to_dict() for msg in self.historico]
        }
        
        json_data = json.dumps(dados_exportacao, ensure_ascii=False, indent=2)
        
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(json_data)
        
        return json_data
    
    async def processar_fila_agente(self, nome_agente: str, max_mensagens: int = 10):
        """
        Processa mensagens pendentes de um agente específico.
        
        Args:
            nome_agente: Nome do agente
            max_mensagens: Número máximo de mensagens para processar
        """
        # ===== PROCESSAMENTO EM LOTE =====
        processadas = 0
        
        while processadas < max_mensagens:
            mensagem = self.obter_proxima_mensagem(nome_agente)
            
            if not mensagem:
                break  # Não há mais mensagens
            
            await self._processar_mensagem(mensagem)
            processadas += 1
        
        return processadas
    
    def criar_canal_direto(self, agente1: str, agente2: str) -> Callable:
        """
        Cria um canal de comunicação direta entre dois agentes.
        
        Args:
            agente1: Primeiro agente
            agente2: Segundo agente
            
        Returns:
            Callable: Função para enviar mensagens diretamente
        """
        # ===== FUNÇÃO DE CANAL DIRETO =====
        async def enviar_direto(remetente: str, conteudo: Dict[str, Any], 
                               prioridade: int = 5) -> Dict[str, Any]:
            # Determina destinatário baseado no remetente
            destinatario = agente2 if remetente == agente1 else agente1
            
            mensagem = MensagemAgente(
                tipo=TipoMensagem.SOLICITACAO,
                remetente=remetente,
                destinatario=destinatario,
                conteudo=conteudo,
                prioridade=prioridade
            )
            
            return await self.enviar_mensagem(mensagem)
        
        return enviar_direto
    
    def __repr__(self):
        return (f"ComunicacaoAgentes(agentes={len(self.agentes_registrados)}, "
                f"mensagens_enviadas={self.estatisticas['mensagens_enviadas']})")


# ===== FUNÇÕES AUXILIARES =====
# Funções de conveniência para uso síncrono
def criar_sistema_comunicacao() -> ComunicacaoAgentes:
    """Cria uma instância do sistema de comunicação."""
    return ComunicacaoAgentes()


def enviar_mensagem_sincrona(sistema: ComunicacaoAgentes, mensagem: MensagemAgente) -> Dict[str, Any]:
    """
    Wrapper síncrono para enviar mensagens.
    
    Args:
        sistema: Sistema de comunicação
        mensagem: Mensagem a enviar
        
    Returns:
        Dict: Resultado do envio
    """
    # Cria loop de eventos para execução síncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(sistema.enviar_mensagem(mensagem))
    finally:
        loop.close()