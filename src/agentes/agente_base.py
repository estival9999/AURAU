"""
Classe base abstrata para todos os agentes do sistema AURALIS.
Define a interface comum e funcionalidades básicas compartilhadas.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import json
from dataclasses import dataclass, asdict


@dataclass
class Mensagem:
    """Estrutura de dados para mensagens no histórico"""
    role: str
    content: str
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class AgenteBase(ABC):
    """
    Classe abstrata base para todos os agentes do sistema AURALIS.
    
    Fornece funcionalidades básicas como:
    - Comunicação com LLM (OpenAI)
    - Gestão de histórico de conversas
    - Formatação de contexto
    - Extração de informações
    """
    
    def __init__(self, nome: str, descricao: str):
        """
        Inicializa o agente base.
        
        Args:
            nome: Nome identificador do agente
            descricao: Descrição das capacidades do agente
        """
        self.nome = nome
        self.descricao = descricao
        self.historico_conversas: List[Mensagem] = []
        self.contexto_atual: Dict[str, Any] = {}
        
        # Configurações do modelo
        self.modelo = "gpt-3.5-turbo"
        self.temperatura = 0.7
        self.max_tokens = 1000
        
        # Cliente OpenAI (será inicializado quando disponível)
        self.openai_client = None
        self._inicializar_openai()
        
    def _inicializar_openai(self):
        """Inicializa o cliente OpenAI se a chave estiver disponível"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
            except ImportError:
                print(f"[{self.nome}] OpenAI não instalado. Usando modo simulado.")
            except Exception as e:
                print(f"[{self.nome}] Erro ao inicializar OpenAI: {str(e)}")
    
    @abstractmethod
    def get_prompt_sistema(self) -> str:
        """
        Retorna o prompt do sistema que define o comportamento do agente.
        
        Returns:
            str: Prompt do sistema para o agente
        """
        pass
    
    @abstractmethod
    def processar_mensagem(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        """
        Processa uma mensagem recebida e retorna uma resposta.
        
        Args:
            mensagem: Mensagem a ser processada
            contexto: Contexto adicional para processar a mensagem
            
        Returns:
            str: Resposta do agente
        """
        pass
    
    def chamar_llm(self, mensagem: str, historico: List[Dict] = None) -> str:
        """
        Faz uma chamada para o modelo de linguagem.
        
        Args:
            mensagem: Mensagem para o modelo
            historico: Histórico de conversas (opcional)
            
        Returns:
            str: Resposta do modelo
        """
        if not self.openai_client:
            return self._resposta_simulada(mensagem)
        
        try:
            # Preparar mensagens
            messages = [{"role": "system", "content": self.get_prompt_sistema()}]
            
            # Adicionar histórico se fornecido
            if historico:
                for msg in historico:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Adicionar mensagem atual
            messages.append({"role": "user", "content": mensagem})
            
            # Fazer chamada para OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.modelo,
                messages=messages,
                temperature=self.temperatura,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[{self.nome}] Erro ao chamar LLM: {str(e)}")
            return self._resposta_simulada(mensagem)
    
    def _resposta_simulada(self, mensagem: str) -> str:
        """
        Gera uma resposta simulada quando não há acesso ao LLM.
        
        Args:
            mensagem: Mensagem recebida
            
        Returns:
            str: Resposta simulada
        """
        return f"[MODO SIMULADO - {self.nome}] Recebi sua mensagem: '{mensagem}'. Em produção, processaria com IA."
    
    def adicionar_ao_historico(self, mensagem: str, resposta: str):
        """
        Adiciona uma interação ao histórico de conversas.
        
        Args:
            mensagem: Mensagem do usuário
            resposta: Resposta do agente
        """
        self.historico_conversas.append(Mensagem("user", mensagem))
        self.historico_conversas.append(Mensagem("assistant", resposta))
        
        # Limitar tamanho do histórico para economizar memória
        if len(self.historico_conversas) > 100:
            self.historico_conversas = self.historico_conversas[-50:]
    
    def formatar_contexto(self, contexto: Dict[str, Any] = None) -> str:
        """
        Formata o contexto adicional para inclusão nas mensagens.
        
        Args:
            contexto: Dicionário com contexto adicional
            
        Returns:
            str: Contexto formatado como string
        """
        if not contexto:
            contexto = self.contexto_atual
        
        if not contexto:
            return ""
        
        linhas = ["Contexto adicional:"]
        for chave, valor in contexto.items():
            if isinstance(valor, (list, dict)):
                valor_str = json.dumps(valor, ensure_ascii=False, indent=2)
            else:
                valor_str = str(valor)
            linhas.append(f"- {chave}: {valor_str}")
        
        return "\n".join(linhas)
    
    def extrair_informacoes(self, texto: str, tipo_info: str) -> List[str]:
        """
        Extrai informações específicas de um texto.
        
        Args:
            texto: Texto para extrair informações
            tipo_info: Tipo de informação a extrair (datas, nomes, decisões, etc.)
            
        Returns:
            List[str]: Lista de informações extraídas
        """
        informacoes = []
        texto_lower = texto.lower()
        
        if tipo_info == "datas":
            # Padrões simples para datas
            import re
            padroes = [
                r'\d{1,2}/\d{1,2}/\d{4}',
                r'\d{1,2} de \w+ de \d{4}',
                r'\d{4}-\d{2}-\d{2}'
            ]
            for padrao in padroes:
                matches = re.findall(padrao, texto)
                informacoes.extend(matches)
                
        elif tipo_info == "decisoes":
            # Procurar por palavras-chave de decisão
            palavras_decisao = ["decidido", "aprovado", "definido", "acordado", "determinado"]
            linhas = texto.split('.')
            for linha in linhas:
                if any(palavra in linha.lower() for palavra in palavras_decisao):
                    informacoes.append(linha.strip())
                    
        elif tipo_info == "participantes":
            # Extrair nomes próprios (heurística simples)
            import re
            # Padrão para nomes próprios (palavras capitalizadas)
            padrao_nome = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
            matches = re.findall(padrao_nome, texto)
            informacoes.extend(matches)
        
        return list(set(informacoes))  # Remover duplicatas
    
    def atualizar_contexto(self, novo_contexto: Dict[str, Any]):
        """
        Atualiza o contexto atual do agente.
        
        Args:
            novo_contexto: Novo contexto para adicionar/atualizar
        """
        self.contexto_atual.update(novo_contexto)
    
    def limpar_historico(self):
        """Limpa o histórico de conversas"""
        self.historico_conversas = []
    
    def obter_resumo_historico(self, num_mensagens: int = 10) -> str:
        """
        Obtém um resumo do histórico recente.
        
        Args:
            num_mensagens: Número de mensagens recentes para incluir
            
        Returns:
            str: Resumo formatado do histórico
        """
        if not self.historico_conversas:
            return "Sem histórico de conversas."
        
        mensagens_recentes = self.historico_conversas[-num_mensagens:]
        resumo = []
        
        for msg in mensagens_recentes:
            role = "Usuário" if msg.role == "user" else self.nome
            resumo.append(f"{role}: {msg.content[:100]}...")
        
        return "\n".join(resumo)
    
    def exportar_historico(self) -> Dict[str, Any]:
        """
        Exporta o histórico e estado do agente.
        
        Returns:
            Dict: Estado completo do agente
        """
        return {
            "nome": self.nome,
            "descricao": self.descricao,
            "timestamp_exportacao": datetime.now().isoformat(),
            "configuracoes": {
                "modelo": self.modelo,
                "temperatura": self.temperatura,
                "max_tokens": self.max_tokens
            },
            "historico": [asdict(msg) for msg in self.historico_conversas],
            "contexto_atual": self.contexto_atual,
            "estatisticas": {
                "total_mensagens": len(self.historico_conversas),
                "mensagens_usuario": len([m for m in self.historico_conversas if m.role == "user"]),
                "mensagens_assistente": len([m for m in self.historico_conversas if m.role == "assistant"])
            }
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(nome='{self.nome}', historico_size={len(self.historico_conversas)})"