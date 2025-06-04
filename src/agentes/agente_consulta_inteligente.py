"""
Agente de Consulta Inteligente - Especialista em busca e recuperação de informações.
Realiza buscas semânticas, correlaciona dados e apresenta informações relevantes.
"""

from typing import Dict, List, Any, Optional, Tuple
import os
import re
from datetime import datetime
from collections import Counter

# Importar classe base apropriada
if os.getenv("OPENAI_API_KEY"):
    from .agente_base import AgenteBase
else:
    from .agente_base_simulado import AgenteBaseSimulado as AgenteBase


class AgenteConsultaInteligente(AgenteBase):
    """
    Agente especializado em busca e recuperação de informações no sistema AURALIS.
    
    Responsabilidades:
    - Buscar em reuniões passadas
    - Consultar base de conhecimento
    - Realizar buscas semânticas
    - Correlacionar informações de múltiplas fontes
    - Calcular relevância e ranquear resultados
    """
    
    def __init__(self):
        super().__init__(
            nome="Consultor Inteligente AURALIS",
            descricao="Especialista em busca semântica e recuperação de informações relevantes"
        )
        
        # Configurações específicas
        self.temperatura = 0.2  # Mais determinístico para buscas precisas
        self.max_resultados = 10
        
        # Sinônimos para expansão de busca
        self.sinonimos = {
            "reunião": ["meeting", "encontro", "sessão", "conferência"],
            "projeto": ["project", "iniciativa", "programa", "empreendimento"],
            "decisão": ["decision", "resolução", "determinação", "deliberação"],
            "equipe": ["team", "time", "grupo", "squad"],
            "prazo": ["deadline", "data limite", "vencimento", "término"],
            "tarefa": ["task", "atividade", "trabalho", "demanda"],
            "problema": ["issue", "questão", "desafio", "dificuldade"],
            "solução": ["solution", "resolução", "resposta", "saída"]
        }
        
        # Mock de base de dados (em produção seria Supabase/ChromaDB)
        self.mock_reunioes = [
            {
                "id": "001",
                "titulo": "Kickoff do Projeto AURALIS",
                "data": "2024-01-15",
                "hora": "14:00",
                "duracao": "90 min",
                "participantes": ["João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa"],
                "pauta": ["Definição de escopo", "Cronograma", "Atribuição de responsabilidades"],
                "decisoes": [
                    "Prazo de entrega definido para 30/06/2024",
                    "Maria Santos será a gerente do projeto",
                    "Reuniões semanais às segundas 10h"
                ],
                "transcricao": "João: Vamos começar definindo o escopo do projeto AURALIS...",
                "tags": ["kickoff", "projeto", "planejamento"]
            },
            {
                "id": "002",
                "titulo": "Revisão Sprint 1 - AURALIS",
                "data": "2024-01-22",
                "hora": "15:00",
                "duracao": "60 min",
                "participantes": ["Maria Santos", "Pedro Oliveira", "Lucas Mendes"],
                "pauta": ["Review das entregas", "Impedimentos", "Próximos passos"],
                "decisoes": [
                    "Sprint aprovada com 85% das tarefas concluídas",
                    "Necessário contratar mais um desenvolvedor",
                    "Ajustar estimativas para próxima sprint"
                ],
                "transcricao": "Maria: A sprint foi produtiva, mas encontramos alguns desafios...",
                "tags": ["sprint", "review", "agile"]
            },
            {
                "id": "003",
                "titulo": "Brainstorming - Funcionalidades IA",
                "data": "2024-01-25",
                "hora": "10:00",
                "duracao": "120 min",
                "participantes": ["Pedro Oliveira", "Ana Costa", "Carlos Tech", "João Silva"],
                "pauta": ["Ideação de features", "Priorização", "Viabilidade técnica"],
                "decisoes": [
                    "Implementar busca semântica como prioridade 1",
                    "Sistema de agentes para processamento inteligente",
                    "Interface de voz para próxima fase"
                ],
                "transcricao": "Ana: Precisamos pensar em como a IA pode agregar valor...",
                "tags": ["brainstorm", "ia", "funcionalidades", "inovação"]
            }
        ]
        
        self.mock_documentos = [
            {
                "id": "doc001",
                "titulo": "Plano de Projeto AURALIS",
                "tipo": "documento",
                "data_criacao": "2024-01-10",
                "autor": "João Silva",
                "conteudo": "Documento detalhando objetivos, escopo e metodologia do projeto...",
                "tags": ["planejamento", "projeto", "documentação"]
            },
            {
                "id": "doc002",
                "titulo": "Arquitetura do Sistema",
                "tipo": "documento técnico",
                "data_criacao": "2024-01-20",
                "autor": "Pedro Oliveira",
                "conteudo": "Descrição da arquitetura multi-agente, componentes e integrações...",
                "tags": ["arquitetura", "técnico", "sistema"]
            }
        ]
    
    def get_prompt_sistema(self) -> str:
        """
        Define o prompt do sistema para o agente de consulta.
        
        Returns:
            str: Prompt do sistema
        """
        return """Você é o Consultor Inteligente do sistema AURALIS, especializado em buscar e apresentar informações relevantes.

Suas responsabilidades:
1. Buscar informações precisas em reuniões passadas e documentos
2. Correlacionar dados de múltiplas fontes
3. Apresentar as informações de forma clara e estruturada
4. Sempre citar as fontes (reunião, data, participante)
5. Destacar informações mais relevantes primeiro

Ao responder:
- Seja preciso e objetivo
- Cite sempre as fontes das informações
- Se não encontrar informações, seja claro sobre isso
- Sugira buscas alternativas quando apropriado
- Use formatação para facilitar a leitura (bullets, negrito, etc.)

Formato preferido de resposta:
1. Resumo executivo (se aplicável)
2. Informações encontradas com fontes
3. Informações relacionadas (se relevante)
4. Sugestões de busca adicional (se necessário)

Sempre responda em português brasileiro."""
    
    def processar_mensagem(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        """
        Processa uma consulta de busca de informações.
        
        Args:
            mensagem: Consulta do usuário
            contexto: Contexto adicional
            
        Returns:
            str: Resposta com informações encontradas
        """
        # Atualizar contexto
        if contexto:
            self.atualizar_contexto(contexto)
        
        # Extrair termos de busca
        termos = self.extrair_termos_busca(mensagem)
        termos_expandidos = self.expandir_termos(termos)
        
        print(f"[CONSULTA] Termos de busca: {termos}")
        print(f"[CONSULTA] Termos expandidos: {termos_expandidos}")
        
        # Buscar em diferentes fontes
        resultados_reunioes = self.buscar_em_reunioes(termos_expandidos)
        resultados_documentos = self.buscar_em_documentos(termos_expandidos)
        
        # Consolidar e formatar resposta
        resposta = self.formatar_resposta_busca(
            mensagem, 
            resultados_reunioes, 
            resultados_documentos,
            termos
        )
        
        # Adicionar ao histórico
        self.adicionar_ao_historico(mensagem, resposta)
        
        return resposta
    
    def extrair_termos_busca(self, mensagem: str) -> List[str]:
        """
        Extrai termos relevantes para busca da mensagem.
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            List[str]: Lista de termos para busca
        """
        # Remover stop words comuns
        stop_words = {
            "o", "a", "os", "as", "de", "da", "do", "das", "dos", "em", "na", "no",
            "nas", "nos", "por", "para", "com", "sem", "sob", "sobre", "é", "são",
            "foi", "foram", "ser", "sendo", "sido", "ter", "tendo", "tido", "que",
            "qual", "quais", "quando", "onde", "quem", "como", "e", "ou", "mas",
            "se", "não", "sim", "muito", "pouco", "mais", "menos", "já", "ainda",
            "um", "uma", "uns", "umas"
        }
        
        # Tokenizar e filtrar
        palavras = mensagem.lower().split()
        termos = []
        
        for palavra in palavras:
            # Remover pontuação
            palavra_limpa = re.sub(r'[^\w\s]', '', palavra)
            
            # Adicionar se não for stop word e tiver mais de 2 caracteres
            if palavra_limpa and palavra_limpa not in stop_words and len(palavra_limpa) > 2:
                termos.append(palavra_limpa)
        
        # Identificar frases importantes (palavras consecutivas capitalizadas)
        frases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', mensagem)
        termos.extend([frase.lower() for frase in frases])
        
        return list(set(termos))  # Remover duplicatas
    
    def expandir_termos(self, termos: List[str]) -> List[str]:
        """
        Expande termos de busca com sinônimos e variações.
        
        Args:
            termos: Lista de termos originais
            
        Returns:
            List[str]: Lista expandida de termos
        """
        termos_expandidos = termos.copy()
        
        for termo in termos:
            # Adicionar sinônimos se existirem
            if termo in self.sinonimos:
                termos_expandidos.extend(self.sinonimos[termo])
            
            # Adicionar variações (plural/singular simplificado)
            if termo.endswith('s'):
                termos_expandidos.append(termo[:-1])  # Remove 's'
            else:
                termos_expandidos.append(termo + 's')  # Adiciona 's'
        
        return list(set(termos_expandidos))  # Remover duplicatas
    
    def calcular_relevancia(self, texto: str, termos: List[str], 
                          titulo: str = "", autor: str = "") -> int:
        """
        Calcula score de relevância de um texto para os termos de busca.
        
        Args:
            texto: Texto para analisar
            termos: Termos de busca
            titulo: Título do documento/reunião
            autor: Autor/participante
            
        Returns:
            int: Score de relevância
        """
        texto_completo = f"{titulo} {autor} {texto}".lower()
        relevancia = 0
        
        for termo in termos:
            termo_lower = termo.lower()
            
            # Contar ocorrências
            ocorrencias = texto_completo.count(termo_lower)
            relevancia += ocorrencias
            
            # Bonus se aparece no título (peso 5)
            if termo_lower in titulo.lower():
                relevancia += 5
            
            # Bonus se é o autor (peso 3)
            if termo_lower in autor.lower():
                relevancia += 3
            
            # Bonus por match exato de frase
            if len(termo.split()) > 1 and termo_lower in texto_completo:
                relevancia += 10
        
        return relevancia
    
    def buscar_em_reunioes(self, termos: List[str]) -> List[Dict[str, Any]]:
        """
        Busca termos em reuniões.
        
        Args:
            termos: Termos de busca
            
        Returns:
            List[Dict]: Reuniões encontradas com relevância
        """
        resultados = []
        
        for reuniao in self.mock_reunioes:
            # Criar texto completo para busca
            texto_busca = f"{reuniao['titulo']} {' '.join(reuniao['participantes'])} "
            texto_busca += f"{' '.join(reuniao['pauta'])} {' '.join(reuniao['decisoes'])} "
            texto_busca += f"{reuniao['transcricao']} {' '.join(reuniao['tags'])}"
            
            # Calcular relevância
            relevancia = self.calcular_relevancia(
                texto_busca,
                termos,
                reuniao['titulo'],
                ' '.join(reuniao['participantes'])
            )
            
            if relevancia > 0:
                resultados.append({
                    "tipo": "reunião",
                    "relevancia": relevancia,
                    "dados": reuniao,
                    "trechos_relevantes": self.extrair_trechos_relevantes(
                        reuniao['transcricao'], 
                        termos
                    )
                })
        
        # Ordenar por relevância
        resultados.sort(key=lambda x: x['relevancia'], reverse=True)
        
        return resultados[:self.max_resultados]
    
    def buscar_em_documentos(self, termos: List[str]) -> List[Dict[str, Any]]:
        """
        Busca termos em documentos.
        
        Args:
            termos: Termos de busca
            
        Returns:
            List[Dict]: Documentos encontrados com relevância
        """
        resultados = []
        
        for doc in self.mock_documentos:
            # Criar texto completo para busca
            texto_busca = f"{doc['titulo']} {doc['autor']} {doc['conteudo']} {' '.join(doc['tags'])}"
            
            # Calcular relevância
            relevancia = self.calcular_relevancia(
                texto_busca,
                termos,
                doc['titulo'],
                doc['autor']
            )
            
            if relevancia > 0:
                resultados.append({
                    "tipo": "documento",
                    "relevancia": relevancia,
                    "dados": doc,
                    "trechos_relevantes": self.extrair_trechos_relevantes(
                        doc['conteudo'], 
                        termos
                    )
                })
        
        # Ordenar por relevância
        resultados.sort(key=lambda x: x['relevancia'], reverse=True)
        
        return resultados[:self.max_resultados]
    
    def extrair_trechos_relevantes(self, texto: str, termos: List[str], 
                                  contexto_chars: int = 100) -> List[str]:
        """
        Extrai trechos do texto que contêm os termos de busca.
        
        Args:
            texto: Texto completo
            termos: Termos para destacar
            contexto_chars: Número de caracteres de contexto
            
        Returns:
            List[str]: Trechos relevantes
        """
        trechos = []
        texto_lower = texto.lower()
        
        for termo in termos:
            termo_lower = termo.lower()
            
            # Encontrar todas as ocorrências
            inicio = 0
            while True:
                pos = texto_lower.find(termo_lower, inicio)
                if pos == -1:
                    break
                
                # Extrair trecho com contexto
                inicio_trecho = max(0, pos - contexto_chars)
                fim_trecho = min(len(texto), pos + len(termo) + contexto_chars)
                
                trecho = texto[inicio_trecho:fim_trecho]
                
                # Adicionar reticências se truncado
                if inicio_trecho > 0:
                    trecho = "..." + trecho
                if fim_trecho < len(texto):
                    trecho = trecho + "..."
                
                # Destacar termo no trecho
                trecho_destacado = trecho.replace(
                    termo, 
                    f"**{termo}**"
                )
                
                if trecho_destacado not in trechos:
                    trechos.append(trecho_destacado)
                
                inicio = pos + 1
                
                # Limitar número de trechos por termo
                if len(trechos) >= 3:
                    break
        
        return trechos[:5]  # Máximo 5 trechos total
    
    def formatar_resposta_busca(self, consulta: str, resultados_reunioes: List[Dict], 
                               resultados_documentos: List[Dict], termos: List[str]) -> str:
        """
        Formata a resposta da busca de forma clara e estruturada.
        
        Args:
            consulta: Consulta original do usuário
            resultados_reunioes: Resultados de reuniões
            resultados_documentos: Resultados de documentos
            termos: Termos de busca utilizados
            
        Returns:
            str: Resposta formatada
        """
        # Se não encontrou nada
        if not resultados_reunioes and not resultados_documentos:
            return self._formatar_resposta_vazia(consulta, termos)
        
        # Construir resposta
        partes = []
        
        # Resumo executivo
        total_resultados = len(resultados_reunioes) + len(resultados_documentos)
        partes.append(f"🔍 **Encontrei {total_resultados} resultado(s) relevante(s) para sua busca.**\n")
        
        # Resultados de reuniões
        if resultados_reunioes:
            partes.append("### 📅 Reuniões Encontradas:\n")
            
            for i, resultado in enumerate(resultados_reunioes[:3], 1):  # Top 3
                reuniao = resultado['dados']
                partes.append(f"**{i}. {reuniao['titulo']}**")
                partes.append(f"   - Data: {reuniao['data']} às {reuniao['hora']}")
                partes.append(f"   - Participantes: {', '.join(reuniao['participantes'][:3])}")
                
                # Decisões relevantes
                decisoes_relevantes = [d for d in reuniao['decisoes'] 
                                     if any(t.lower() in d.lower() for t in termos)]
                if decisoes_relevantes:
                    partes.append(f"   - Decisões relacionadas:")
                    for decisao in decisoes_relevantes[:2]:
                        partes.append(f"     • {decisao}")
                
                # Trechos relevantes
                if resultado['trechos_relevantes']:
                    partes.append(f"   - Trecho relevante: {resultado['trechos_relevantes'][0]}")
                
                partes.append("")  # Linha em branco
        
        # Resultados de documentos
        if resultados_documentos:
            partes.append("### 📄 Documentos Encontrados:\n")
            
            for i, resultado in enumerate(resultados_documentos[:2], 1):  # Top 2
                doc = resultado['dados']
                partes.append(f"**{i}. {doc['titulo']}**")
                partes.append(f"   - Tipo: {doc['tipo']}")
                partes.append(f"   - Autor: {doc['autor']}")
                partes.append(f"   - Data: {doc['data_criacao']}")
                
                # Trecho relevante
                if resultado['trechos_relevantes']:
                    partes.append(f"   - Trecho: {resultado['trechos_relevantes'][0]}")
                
                partes.append("")
        
        # Sugestões adicionais
        if total_resultados < 3:
            partes.append("\n💡 **Sugestões para refinar sua busca:**")
            partes.append("- Tente usar termos mais específicos")
            partes.append("- Inclua nomes de participantes ou datas aproximadas")
            partes.append("- Use palavras-chave dos tópicos discutidos")
        
        return "\n".join(partes)
    
    def _formatar_resposta_vazia(self, consulta: str, termos: List[str]) -> str:
        """
        Formata resposta quando não há resultados.
        
        Args:
            consulta: Consulta original
            termos: Termos utilizados
            
        Returns:
            str: Resposta formatada
        """
        resposta = [
            "🔍 **Não encontrei resultados para sua busca.**\n",
            f"Termos pesquisados: {', '.join(termos)}\n",
            "**Sugestões:**",
            "• Verifique a ortografia dos termos",
            "• Use palavras mais genéricas",
            "• Tente sinônimos ou termos relacionados",
            "• Especifique um período de tempo diferente\n",
            "Posso ajudar de outra forma? Tente reformular sua pergunta ou peça sugestões de busca."
        ]
        
        return "\n".join(resposta)
    
    def buscar_por_periodo(self, data_inicio: str, data_fim: str) -> List[Dict[str, Any]]:
        """
        Busca reuniões em um período específico.
        
        Args:
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)
            
        Returns:
            List[Dict]: Reuniões no período
        """
        resultados = []
        
        for reuniao in self.mock_reunioes:
            if data_inicio <= reuniao['data'] <= data_fim:
                resultados.append({
                    "tipo": "reunião",
                    "dados": reuniao
                })
        
        return resultados
    
    def buscar_por_participante(self, nome_participante: str) -> List[Dict[str, Any]]:
        """
        Busca reuniões de um participante específico.
        
        Args:
            nome_participante: Nome do participante
            
        Returns:
            List[Dict]: Reuniões do participante
        """
        resultados = []
        nome_lower = nome_participante.lower()
        
        for reuniao in self.mock_reunioes:
            participantes_lower = [p.lower() for p in reuniao['participantes']]
            if any(nome_lower in p for p in participantes_lower):
                resultados.append({
                    "tipo": "reunião",
                    "dados": reuniao
                })
        
        return resultados
    
    def gerar_resumo_topico(self, topico: str, num_items: int = 5) -> str:
        """
        Gera um resumo sobre um tópico específico.
        
        Args:
            topico: Tópico para resumir
            num_items: Número de itens para incluir
            
        Returns:
            str: Resumo formatado
        """
        # Buscar informações sobre o tópico
        termos = self.extrair_termos_busca(topico)
        resultados_reunioes = self.buscar_em_reunioes(termos)
        
        if not resultados_reunioes:
            return f"Não encontrei informações suficientes sobre '{topico}' para gerar um resumo."
        
        # Extrair informações relevantes
        todas_decisoes = []
        todos_participantes = []
        todas_datas = []
        
        for resultado in resultados_reunioes[:num_items]:
            reuniao = resultado['dados']
            todas_decisoes.extend(reuniao['decisoes'])
            todos_participantes.extend(reuniao['participantes'])
            todas_datas.append(reuniao['data'])
        
        # Contar participantes mais frequentes
        participantes_freq = Counter(todos_participantes).most_common(3)
        
        # Formatar resumo
        resumo = [
            f"📊 **Resumo sobre: {topico}**\n",
            f"**Período analisado:** {min(todas_datas)} a {max(todas_datas)}",
            f"**Total de reuniões:** {len(resultados_reunioes)}\n",
            "**Principais participantes:**"
        ]
        
        for participante, freq in participantes_freq:
            resumo.append(f"• {participante} ({freq} reuniões)")
        
        resumo.append("\n**Principais decisões/pontos:**")
        for decisao in todas_decisoes[:5]:
            if any(t.lower() in decisao.lower() for t in termos):
                resumo.append(f"• {decisao}")
        
        return "\n".join(resumo)
    
    def __repr__(self):
        return f"AgenteConsultaInteligente(max_resultados={self.max_resultados})"