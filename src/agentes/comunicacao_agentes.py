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
    """Tipos de mensagem no sistema"""
    SOLICITACAO = "SOLICITACAO"
    RESPOSTA = "RESPOSTA"
    NOTIFICACAO = "NOTIFICACAO"
    ERRO = "ERRO"
    BROADCAST = "BROADCAST"
    HEARTBEAT = "HEARTBEAT"
    STATUS = "STATUS"


class StatusMensagem(Enum):
    """Status de processamento da mensagem"""
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    ERRO = "ERRO"
    CANCELADO = "CANCELADO"
    TIMEOUT = "TIMEOUT"


@dataclass
class MensagemAgente:
    """Estrutura de dados para mensagens entre agentes"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tipo: TipoMensagem = TipoMensagem.SOLICITACAO
    remetente: str = ""
    destinatario: str = ""
    conteudo: Dict[str, Any] = field(default_factory=dict)
    contexto: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: StatusMensagem = StatusMensagem.PENDENTE
    prioridade: int = 5  # 1-10 (1 = mais alta)
    resposta_para: Optional[str] = None  # ID da mensagem original se for resposta
    tentativas: int = 0
    max_tentativas: int = 3
    timeout_segundos: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte mensagem para dicionário"""
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
        # Registro de agentes
        self.agentes_registrados: Dict[str, Any] = {}
        
        # Filas de mensagens por destinatário e prioridade
        self.filas_mensagens: Dict[str, Dict[int, deque]] = defaultdict(
            lambda: {i: deque() for i in range(1, 11)}
        )
        
        # Callbacks por agente
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Histórico de mensagens
        self.historico: deque = deque(maxlen=max_historico)
        
        # Estatísticas
        self.estatisticas = {
            "mensagens_enviadas": 0,
            "mensagens_processadas": 0,
            "mensagens_erro": 0,
            "tempo_total_processamento": 0.0,
            "mensagens_por_tipo": defaultdict(int),
            "mensagens_por_agente": defaultdict(int)
        }
        
        # Lock para operações thread-safe
        self.lock = asyncio.Lock()
        
        # Flag para sistema ativo
        self.ativo = True
        
        # Mensagens em processamento
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
        
        if callback:
            self.callbacks[nome].append(callback)
        
        print(f"[COMUNICAÇÃO] Agente '{nome}' registrado com sucesso")
    
    def desregistrar_agente(self, nome: str):
        """
        Remove um agente do sistema.
        
        Args:
            nome: Nome do agente
        """
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
            # Validar mensagem
            if not mensagem.destinatario:
                return {"sucesso": False, "erro": "Destinatário não especificado"}
            
            if mensagem.destinatario not in self.agentes_registrados:
                return {"sucesso": False, "erro": f"Agente '{mensagem.destinatario}' não registrado"}
            
            # Adicionar à fila apropriada
            self.filas_mensagens[mensagem.destinatario][mensagem.prioridade].append(mensagem)
            
            # Atualizar estatísticas
            self.estatisticas["mensagens_enviadas"] += 1
            self.estatisticas["mensagens_por_tipo"][mensagem.tipo.value] += 1
            self.estatisticas["mensagens_por_agente"][mensagem.remetente] += 1
            
            # Adicionar ao histórico
            self.historico.append(mensagem)
            
            # Processar mensagem
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
            # Obter agente destinatário
            agente = self.agentes_registrados[mensagem.destinatario]
            
            # Executar callbacks
            for callback in self.callbacks.get(mensagem.destinatario, []):
                await self._executar_callback(callback, mensagem, agente)
            
            # Se o agente tem método processar_mensagem, chamar diretamente
            if hasattr(agente, 'processar_mensagem'):
                resposta = agente.processar_mensagem(
                    mensagem.conteudo.get("mensagem", ""),
                    mensagem.contexto
                )
                
                # Criar mensagem de resposta
                if mensagem.tipo == TipoMensagem.SOLICITACAO:
                    msg_resposta = MensagemAgente(
                        tipo=TipoMensagem.RESPOSTA,
                        remetente=mensagem.destinatario,
                        destinatario=mensagem.remetente,
                        conteudo={"resposta": resposta},
                        contexto=mensagem.contexto,
                        resposta_para=mensagem.id
                    )
                    
                    # Enviar resposta de volta
                    await self.enviar_mensagem(msg_resposta)
            
            # Marcar como concluído
            mensagem.status = StatusMensagem.CONCLUIDO
            
            # Atualizar estatísticas
            tempo_processamento = (datetime.now() - inicio).total_seconds()
            self.estatisticas["mensagens_processadas"] += 1
            self.estatisticas["tempo_total_processamento"] += tempo_processamento
            
            return {
                "sucesso": True,
                "mensagem_id": mensagem.id,
                "tempo_processamento": tempo_processamento
            }
            
        except Exception as e:
            # Marcar como erro
            mensagem.status = StatusMensagem.ERRO
            self.estatisticas["mensagens_erro"] += 1
            
            return {
                "sucesso": False,
                "mensagem_id": mensagem.id,
                "erro": str(e)
            }
            
        finally:
            # Remover de processando
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
        excluir = excluir or []
        excluir.append(remetente)  # Não enviar para si mesmo
        
        destinatarios = [nome for nome in self.agentes_registrados 
                        if nome not in excluir]
        
        resultados = {
            "total_destinatarios": len(destinatarios),
            "sucessos": 0,
            "falhas": 0,
            "detalhes": {}
        }
        
        # Enviar para cada destinatário
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
        
        # Verificar filas por prioridade (1 = mais alta)
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
        tempo_medio = 0.0
        if self.estatisticas["mensagens_processadas"] > 0:
            tempo_medio = (self.estatisticas["tempo_total_processamento"] / 
                          self.estatisticas["mensagens_processadas"])
        
        # Contar mensagens em filas
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
        if agente:
            if agente in self.filas_mensagens:
                for fila in self.filas_mensagens[agente].values():
                    fila.clear()
        else:
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
        processadas = 0
        
        while processadas < max_mensagens:
            mensagem = self.obter_proxima_mensagem(nome_agente)
            
            if not mensagem:
                break
            
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
        async def enviar_direto(remetente: str, conteudo: Dict[str, Any], 
                               prioridade: int = 5) -> Dict[str, Any]:
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


# Funções auxiliares para uso síncrono
def criar_sistema_comunicacao() -> ComunicacaoAgentes:
    """Cria uma instância do sistema de comunicação"""
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(sistema.enviar_mensagem(mensagem))
    finally:
        loop.close()