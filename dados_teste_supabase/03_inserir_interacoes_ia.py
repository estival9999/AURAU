#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inserir interações com IA de teste no Supabase
Simulando conversas reais com o assistente AURALIS
"""

import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import random

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Buscar IDs dos usuários e reuniões
print("🔍 Buscando dados existentes...")
users_response = supabase.table('users').select("id, username, full_name").execute()
users = {user['username']: user for user in users_response.data}

meetings_response = supabase.table('meetings').select("id, title").execute()
meetings = meetings_response.data

# Interações realistas com a IA
interacoes = [
    {
        "usuario": "carlos.mendes",
        "meeting_id": None,  # Consulta geral
        "conversa": [
            {
                "pergunta": "Quais foram as principais decisões tomadas nas reuniões de tecnologia este mês?",
                "resposta": "Analisando as reuniões de tecnologia deste mês, identifiquei as seguintes decisões principais:\n\n1. **Arquitetura de Notificações**: Decidido usar WebSockets em vez de SSE para o sistema de notificações em tempo real, aproveitando a experiência da equipe com Socket.IO.\n\n2. **Correção do Gateway de Pagamento**: Priorizada a resolução do problema de integração com o gateway, identificado como problema de certificado SSL do fornecedor.\n\n3. **Contratações**: Aprovadas 15 novas vagas para o departamento de tecnologia, com ajuste de 20% no teto salarial para desenvolvedores sênior.\n\n4. **Processo Seletivo**: Implementação de etapa de pair programming (1 hora) no processo seletivo para avaliar trabalho em equipe.\n\n5. **Documentação**: Decisão de atualizar toda a documentação da API que está defasada, com prazo até final da sprint.\n\nEssas decisões refletem o foco em crescimento da equipe e melhoria da infraestrutura técnica.",
                "tempo_resposta": 1852,
                "tokens": 245
            }
        ]
    },
    {
        "usuario": "ana.silva",
        "meeting_id": meetings[0]["id"] if meetings else None,
        "conversa": [
            {
                "pergunta": "Preciso de um resumo da última reunião de planejamento de sprint para enviar para a equipe",
                "resposta": "Aqui está o resumo executivo da reunião de Planejamento Sprint 23:\n\n**Data e Participantes**\n- Realizada com 5 participantes da equipe de tecnologia\n- Duração: 1 hora\n\n**Resultados Sprint Anterior**\n- 80% das entregas concluídas\n- ✅ Funcionalidade de login completa\n- ⚠️ Integração com gateway de pagamento bloqueada (problema: certificado SSL do fornecedor)\n\n**Planejamento Sprint 23**\n\n*Tarefas Distribuídas:*\n- Roberto: Finalizar gateway de pagamento + iniciar sistema de notificações\n- Pedro: Implementar filtros de busca avançados\n- Ana: Code review + atualização de documentação\n- Patricia: Designs das notificações (prazo: quarta-feira)\n\n**Decisões Técnicas**\n- WebSockets escolhido para notificações real-time\n- Commits frequentes e atualização constante do Jira\n\n**⚠️ Importante**: Demo para cliente na sexta-feira - gateway de pagamento deve estar funcional\n\nQualquer bloqueio deve ser comunicado imediatamente ao Carlos.",
                "tempo_resposta": 2103,
                "tokens": 287
            }
        ]
    },
    {
        "usuario": "roberto.santos",
        "meeting_id": None,
        "conversa": [
            {
                "pergunta": "Quais são minhas tarefas pendentes das últimas reuniões?",
                "resposta": "Roberto, baseado nas últimas reuniões, suas tarefas pendentes são:\n\n**🔴 Alta Prioridade**\n1. **Finalizar integração do Gateway de Pagamento**\n   - Status: Em andamento (problema do certificado SSL resolvido)\n   - Pendente: Implementar webhooks para confirmações\n   - Prazo: Hoje\n   - Contexto: Necessário para demo de sexta-feira\n\n2. **Sistema de Notificações com WebSockets**\n   - Status: A iniciar após gateway\n   - Decisão: Usar Socket.IO\n   - Dependência: Designs da Patricia (até quarta)\n\n**🟡 Média Prioridade**\n3. **Ajustar código conforme review da Ana**\n   - Status: Comentários no PR de autenticação\n   - Prazo: Hoje\n\n4. **Adicionar exemplos na documentação da API**\n   - Status: Aguardando Ana finalizar estrutura\n   - Prazo: Quando documentação base estiver pronta\n\n**📝 Notas**\n- Servidor staging com problemas de performance (chamado aberto com infra)\n- Manter commits frequentes e Jira atualizado\n\nRecomendo focar no gateway hoje para garantir a demo de sexta. Precisa de ajuda com algo específico?",
                "tempo_resposta": 1677,
                "tokens": 312
            }
        ]
    },
    {
        "usuario": "fernando.lima",
        "meeting_id": meetings[2]["id"] if len(meetings) > 2 else None,
        "conversa": [
            {
                "pergunta": "Gere um relatório executivo dos resultados apresentados no Q4 para enviar à diretoria",
                "resposta": "**RELATÓRIO EXECUTIVO - RESULTADOS Q4 2024**\n\n**RESUMO DE PERFORMANCE**\n\n📈 **Crescimento de Receita**: +15% YoY\n- Receita adicional: R$ 3,5 milhões\n- Principal driver: Novo contrato com multinacional\n- Crescimento orgânico: 8%\n\n**PERFORMANCE POR DEPARTAMENTO**\n- Tecnologia: +22% (maior crescimento)\n- Marketing: +15%\n- Operações: Estável\n\n**INDICADORES DE RH**\n- Taxa de retenção: 92% (vs. 85% mercado)\n- Crescimento do quadro: +12% em despesas com folha\n- Proporção despesa/receita: Melhorada\n- Headcount Tecnologia: +30%\n\n**EFICIÊNCIA DE MARKETING**\n- ROI campanhas digitais: 300%\n- ⚠️ Risco: Alta dependência de Google Ads\n\n**PROJEÇÕES Q1 2025**\n- Cenário conservador: +10%\n- Cenário otimista: +18% (mediante fechamento de 2 contratos em negociação)\n\n**PLANO DE AÇÃO**\n✅ 20 novas contratações aprovadas (15 Tech, 5 Marketing)\n✅ Início das contratações: Janeiro 2025\n✅ Diversificação de canais de marketing\n\n**RISCO CRÍTICO**\n🔴 Renovação do maior cliente (30% da receita) - Decisão esperada até final de janeiro\n\n**RECOMENDAÇÃO**: Manter foco na renovação do contrato principal enquanto acelera contratações para suportar crescimento projetado.",
                "tempo_resposta": 2234,
                "tokens": 398
            }
        ]
    },
    {
        "usuario": "mariana.costa",
        "meeting_id": None,
        "conversa": [
            {
                "pergunta": "Preciso de um template de email para divulgar as novas vagas de tecnologia com os benefícios atualizados",
                "resposta": "Aqui está o template de email para divulgação das vagas:\n\n---\n\n**Assunto: [TechCorp] Oportunidades para Profissionais de Tecnologia - Vagas Abertas!**\n\nOlá [Nome],\n\nA TechCorp está em expansão e buscamos talentos para integrar nosso time de tecnologia! São 15 vagas abertas em diferentes níveis:\n\n**📋 VAGAS DISPONÍVEIS**\n• Desenvolvedor Sênior (5 vagas)\n• Desenvolvedor Pleno (3 vagas)  \n• Desenvolvedor Júnior (4 vagas)\n• DevOps Engineer (2 vagas)\n• Arquiteto de Software (1 vaga)\n\n**💰 REMUNERAÇÃO E BENEFÍCIOS**\n• Salários competitivos (reajustados +20% para seniors)\n• Vale Alimentação + Vale Refeição (separados)\n• Plano de Saúde Premium (sem coparticipação)\n• Auxílio Home Office: R$ 300/mês\n• 🆕 Auxílio Educação: R$ 1.500/ano\n• Gympass\n• Trabalho híbrido flexível\n\n**🎯 NOSSO PROCESSO SELETIVO**\n• Entrevista inicial com RH\n• Avaliação técnica + Pair Programming (1h)\n• Entrevista com gestor\n• Proposta em até 48h\n\n**🚀 POR QUE A TECHCORP?**\n• Crescimento de 22% no último ano\n• Taxa de retenção: 92%\n• Projetos desafiadores com clientes multinacionais\n• Cultura de aprendizado contínuo\n• Time colaborativo e ambiente inclusivo\n\n**Prazo para candidaturas**: Até 28/02/2025\n\n**Como se candidatar**: Envie seu CV para vagas@techcorp.com.br com o código da vaga no assunto.\n\nCompartilhe com sua rede! 🤝\n\nAtenciosamente,\nEquipe de Talentos TechCorp\n\n---\n\nDica: Personalize o campo [Nome] e considere segmentar por senioridade para mensagens mais direcionadas.",
                "tempo_resposta": 1923,
                "tokens": 456
            }
        ]
    },
    {
        "usuario": "pedro.oliveira",
        "meeting_id": None,
        "conversa": [
            {
                "pergunta": "Me ajuda a estruturar as queries complexas para os filtros avançados que mencionei no daily?",
                "resposta": "Claro Pedro! Vou te ajudar a estruturar as queries para filtros avançados. Baseado no contexto do daily, aqui está uma abordagem otimizada:\n\n```sql\n-- 1. QUERY BASE COM MÚLTIPLOS CRITÉRIOS\n-- Usando CTEs para melhor performance e legibilidade\n\nWITH filtered_meetings AS (\n  SELECT \n    m.id,\n    m.title,\n    m.start_time,\n    m.duration_seconds,\n    m.transcription_summary,\n    m.participants,\n    m.key_points,\n    m.decisions\n  FROM meetings m\n  WHERE 1=1\n    -- Filtro por data (índice: idx_meetings_created_at)\n    AND m.start_time >= $1 \n    AND m.start_time <= $2\n    \n    -- Filtro por status\n    AND ($3::varchar IS NULL OR m.status = $3)\n    \n    -- Filtro por organizador\n    AND ($4::uuid IS NULL OR m.user_id = $4)\n),\n\n-- 2. FILTROS AVANÇADOS COM ARRAYS\narray_filtered AS (\n  SELECT *\n  FROM filtered_meetings\n  WHERE \n    -- Busca em participantes (usa índice GIN)\n    ($5::text[] IS NULL OR participants && $5)\n    \n    -- Busca em key_points\n    AND ($6::text IS NULL OR \n         EXISTS (\n           SELECT 1 FROM unnest(key_points) kp \n           WHERE kp ILIKE '%' || $6 || '%'\n         )\n    )\n)\n\n-- 3. QUERY FINAL COM BUSCA TEXTUAL\nSELECT \n  *,\n  -- Relevância para ordenação\n  ts_rank(\n    to_tsvector('portuguese', \n      COALESCE(title, '') || ' ' || \n      COALESCE(transcription_summary, '')\n    ),\n    plainto_tsquery('portuguese', $7)\n  ) as relevance\nFROM array_filtered\nWHERE \n  -- Busca textual opcional\n  ($7::text IS NULL OR\n   to_tsvector('portuguese', \n     COALESCE(title, '') || ' ' || \n     COALESCE(transcription_summary, '')\n   ) @@ plainto_tsquery('portuguese', $7)\n  )\nORDER BY \n  CASE \n    WHEN $8 = 'relevance' THEN relevance\n    WHEN $8 = 'date_desc' THEN EXTRACT(EPOCH FROM start_time) * -1\n    WHEN $8 = 'date_asc' THEN EXTRACT(EPOCH FROM start_time)\n    ELSE EXTRACT(EPOCH FROM start_time) * -1\n  END\nLIMIT $9 OFFSET $10;\n```\n\n**OTIMIZAÇÕES IMPLEMENTADAS:**\n\n1. **CTEs (Common Table Expressions)**: Dividem a query em etapas lógicas\n2. **Índices aproveitados**: \n   - `idx_meetings_created_at` para filtro de data\n   - `idx_meetings_participants` (GIN) para arrays\n   - Índices de text search para busca textual\n\n3. **Parâmetros opcionais**: Usa `IS NULL` para ignorar filtros não fornecidos\n\n4. **Performance tips**:\n   - Evita múltiplos JOINs desnecessários\n   - Usa operador `&&` para arrays (muito rápido com GIN)\n   - `EXISTS` com `unnest` para busca parcial em arrays\n\n**EXEMPLO DE USO NO PYTHON:**\n\n```python\ndef buscar_reunioes_avancado(filtros):\n    query = \"\"\" ... query acima ... \"\"\"\n    \n    params = [\n        filtros.get('data_inicio'),\n        filtros.get('data_fim'),\n        filtros.get('status'),\n        filtros.get('organizador_id'),\n        filtros.get('participantes'),  # array\n        filtros.get('palavra_chave'),\n        filtros.get('busca_texto'),\n        filtros.get('ordenacao', 'date_desc'),\n        filtros.get('limite', 20),\n        filtros.get('offset', 0)\n    ]\n    \n    return supabase.rpc('buscar_reunioes_complexo', params).execute()\n```\n\nPrecisa de ajustes específicos para algum tipo de filtro?",
                "tempo_resposta": 3142,
                "tokens": 892
            }
        ]
    },
    {
        "usuario": "juliana.martinez",
        "meeting_id": None,
        "conversa": [
            {
                "pergunta": "Baseado nas reuniões recentes, quais são as principais tendências e oportunidades para o departamento de marketing?",
                "resposta": "Analisando as reuniões recentes, identifiquei importantes tendências e oportunidades para o Marketing:\n\n**📊 TENDÊNCIAS IDENTIFICADAS**\n\n1. **Crescimento Digital Acelerado**\n   - ROI de 300% em campanhas digitais (Q4 2024)\n   - Marketing cresceu 15% no período\n   - Alta eficiência em conversão\n\n2. **Dependência de Canal Único**\n   - ⚠️ Concentração excessiva em Google Ads\n   - Risco identificado pela diretoria\n   - Necessidade urgente de diversificação\n\n**💡 OPORTUNIDADES IMEDIATAS**\n\n1. **Expansão da Equipe**\n   - 5 novas vagas aprovadas para Marketing\n   - Orçamento já liberado\n   - Chance de formar equipe especializada por canal\n\n2. **Diversificação de Canais**\n   - **LinkedIn Ads**: B2B para alcançar decisores\n   - **Marketing de Conteúdo**: Aproveitar cases de sucesso (crescimento 22% Tech)\n   - **Email Marketing**: Base de clientes atual subaproveitada\n   - **Webinars/Eventos**: Mostrar expertise técnica\n\n3. **Sinergia com Tecnologia**\n   - Departamento Tech cresceu 22%\n   - Oportunidade de criar conteúdo técnico\n   - Cases de transformação digital dos clientes\n   - Parceria para marketing de produto\n\n**🎯 RECOMENDAÇÕES ESTRATÉGICAS**\n\n1. **Curto Prazo (Q1 2025)**\n   - Contratar especialista em LinkedIn Ads\n   - Iniciar testes em novos canais (20% do budget)\n   - Criar programa de marketing de conteúdo\n\n2. **Médio Prazo**\n   - Reduzir dependência Google Ads para máx. 50%\n   - Implementar marketing automation\n   - Desenvolver programa de advocacy com clientes\n\n3. **KPIs Sugeridos**\n   - Diversificação: % receita por canal\n   - CAC por canal\n   - LTV/CAC ratio\n   - Marketing Qualified Leads (MQLs)\n\n**💰 ARGUMENTO PARA BUDGET**\nCom ROI atual de 300% e apenas 5 contratações vs. 15 de Tech, há espaço para solicitar aumento de investimento, especialmente para ferramentas de automation e novos canais.\n\nGostaria de detalhar alguma estratégia específica?",
                "tempo_resposta": 2567,
                "tokens": 524
            }
        ]
    },
    {
        "usuario": "patricia.rocha",
        "meeting_id": None,
        "conversa": [
            {
                "pergunta": "Quais foram os feedbacks sobre meus designs e o que preciso priorizar esta semana?",
                "resposta": "Patricia, analisando as reuniões recentes, aqui estão os feedbacks e prioridades:\n\n**🎨 FEEDBACKS SOBRE SEUS DESIGNS**\n\n**Dashboard Principal e Tela de Relatórios**\n✅ Positivos:\n- Ana: \"Ficou excelente\"\n- Aprovação geral da equipe\n- Designs já compartilhados no Figma\n\n⚠️ Ajustes solicitados:\n- **Paleta de cores**: Tom de azul está muito escuro\n- Pedro concordou: precisa clarear para melhorar contraste\n- Sugestão: Aumentar luminosidade mantendo identidade visual\n\n**📋 SUAS PRIORIDADES ESTA SEMANA**\n\n**1. URGENTE - Designs de Notificações** 🔴\n- **Prazo**: Quarta-feira (definido por Carlos)\n- **Contexto**: Sistema usará WebSockets\n- **Requisitos**:\n  - Notificações em tempo real\n  - Estados: nova, lida, arquivada\n  - Mobile-friendly\n  - Integração com o design atual\n- **Status**: Você mencionou já ter ideias\n\n**2. Ajustes no Dashboard** 🟡\n- Clarear paleta de azul\n- Melhorar contraste para acessibilidade\n- Validar com Ana e Pedro após ajustes\n\n**3. Próximas Demandas** 🟢\n- Preparar mockups para pair programming (nova etapa do processo seletivo)\n- Possíveis telas para módulo de pagamento (após Roberto finalizar)\n\n**💡 SUGESTÕES**\n\n1. **Para as notificações**:\n   - Considere micro-interações\n   - Badge com contador\n   - Som opcional\n   - Agrupamento por tipo\n\n2. **Quick wins**:\n   - Criar variações da paleta azul hoje\n   - Compartilhar rascunhos das notificações antes de quarta\n\n**📅 Timeline sugerida**:\n- Segunda: Ajustar cores + iniciar notificações\n- Terça: Finalizar notificações + revisão\n- Quarta manhã: Entrega final\n\nPrecisa de referências ou discussão sobre as notificações?",
                "tempo_resposta": 1834,
                "tokens": 468
            }
        ]
    }
]

# Inserir interações
print("\n🔄 Inserindo interações com IA no Supabase...")
for dados in interacoes:
    try:
        usuario = users.get(dados["usuario"])
        if not usuario:
            print(f"❌ Usuário {dados['usuario']} não encontrado")
            continue
        
        for conversa in dados["conversa"]:
            # Criar contexto usado (simulação)
            context = {
                "meetings": [],
                "knowledge": [],
                "chunks": []
            }
            
            if dados.get("meeting_id"):
                context["meetings"].append(dados["meeting_id"])
            else:
                # Simular busca em múltiplas reuniões
                if meetings:
                    context["meetings"] = [m["id"] for m in random.sample(meetings, min(3, len(meetings)))]
            
            interacao = {
                "user_id": usuario["id"],
                "meeting_id": dados.get("meeting_id"),
                "user_message": conversa["pergunta"],
                "ai_response": conversa["resposta"],
                "response_time_ms": conversa["tempo_resposta"],
                "tokens_used": conversa["tokens"],
                "model_used": "gpt-4-turbo",
                "context_used": context,
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 15), hours=random.randint(0, 23))).isoformat()
            }
            
            response = supabase.table('ai_interactions').insert(interacao).execute()
            print(f"✅ Interação de {usuario['full_name']} inserida com sucesso")
            
    except Exception as e:
        print(f"❌ Erro ao inserir interação: {str(e)}")

# Verificar inserção
print("\n📊 Verificando interações inseridas:")
try:
    interactions = supabase.table('ai_interactions').select("*").order("created_at", desc=True).execute()
    print(f"Total de interações no banco: {len(interactions.data)}")
    
    # Estatísticas
    usuarios_unicos = set()
    total_tokens = 0
    tempo_medio = 0
    
    for interaction in interactions.data:
        usuarios_unicos.add(interaction['user_id'])
        total_tokens += interaction['tokens_used'] or 0
        tempo_medio += interaction['response_time_ms'] or 0
    
    if interactions.data:
        tempo_medio = tempo_medio / len(interactions.data)
        print(f"\n📈 Estatísticas:")
        print(f"  - Usuários únicos: {len(usuarios_unicos)}")
        print(f"  - Total de tokens usados: {total_tokens}")
        print(f"  - Tempo médio de resposta: {tempo_medio:.0f}ms")
        
except Exception as e:
    print(f"❌ Erro ao verificar interações: {str(e)}")

print("\n✅ Script de interações com IA concluído!")