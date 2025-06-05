#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inserir reuniões de teste no Supabase
Transcrições brutas simulando gravações reais
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

# Buscar IDs dos usuários
print("🔍 Buscando usuários existentes...")
users_response = supabase.table('users').select("id, username, full_name").execute()
users = {user['username']: user for user in users_response.data}

# Transcrições brutas realistas (texto contínuo como seria de uma gravação)
transcricoes = [
    {
        "organizador": "carlos.mendes",
        "titulo": "Reunião de Planejamento Sprint 23",
        "duracao": 3600,  # 1 hora
        "participantes": ["Carlos Eduardo Mendes", "Ana Paula Silva", "Roberto dos Santos", "Pedro Henrique Oliveira", "Patricia Rocha"],
        "transcricao": "carlos então pessoal vamos começar nossa reunião de planejamento da sprint vinte e três primeiro quero agradecer a presença de todos sei que está corrido mas é importante alinharmos as próximas duas semanas ana você pode compartilhar os resultados da sprint anterior ana claro carlos então conseguimos entregar oitenta por cento do planejado a funcionalidade de login ficou completa o roberto fez um excelente trabalho com a api mas tivemos um impedimento com a integração do gateway de pagamento roberto é verdade encontramos uma limitação na documentação deles que não estava clara passei quase dois dias debugando até descobrir que o problema era no certificado ssl deles não no nosso código patricia você tem alguma atualização sobre os mockups da nova interface patricia sim já finalizei os designs do dashboard principal e da tela de relatórios compartilhei no figma ontem vocês viram ana vi sim ficou excelente só tenho uma dúvida sobre a paleta de cores aquela azul não está muito escura pedro concordo com a ana acho que podemos clarear um pouco para melhorar o contraste carlos ok então para essa sprint o que temos no backlog ana temos a continuação da integração de pagamento que ficou pendente a implementação dos novos filtros de busca e início do módulo de notificações roberto sobre as notificações precisamos decidir se vamos usar websockets ou sse para real time pedro acho que websockets seria melhor já temos experiência com socket io carlos concordo vamos com websockets então patricia preciso que você crie os designs das notificações até quarta feira pode ser patricia sem problemas já tenho algumas ideias vou fazer uns rascunhos hoje mesmo carlos ótimo então vamos fazer a distribuição roberto você continua com o gateway de pagamento e depois pega as notificações pedro você fica com os filtros ana você pode dar suporte ao roberto e revisar o código do pedro ana perfeito vou também atualizar a documentação que está defasada carlos excelente não esqueçam de atualizar o jira e fazer os commits frequentes lembrem que sexta feira temos a demo para o cliente então precisamos ter pelo menos o pagamento funcionando roberto vai dar certo já identifiquei o problema é só ajustar a configuração carlos alguma dúvida pessoal todos não está tudo claro carlos então é isso bom trabalho a todos e qualquer bloqueio me avisem imediatamente vamos fazer acontecer",
        "observacoes": "Sprint focada em finalizar integração de pagamento e iniciar sistema de notificações"
    },
    {
        "organizador": "ana.silva",
        "titulo": "Daily Standup - Equipe Dev",
        "duracao": 900,  # 15 minutos
        "participantes": ["Ana Paula Silva", "Roberto dos Santos", "Pedro Henrique Oliveira"],
        "transcricao": "ana bom dia pessoal vamos fazer nosso daily rapidinho roberto começa por favor como está o gateway roberto bom dia seguindo bem ontem consegui resolver o problema do certificado agora estou implementando a parte de webhooks para receber as confirmações de pagamento deve terminar hoje ana ótimo algum impedimento roberto não por enquanto está fluindo pedro e você pedro terminei os filtros de busca por data e categoria agora vou começar os filtros avançados com múltiplos critérios talvez precise de ajuda com a query do banco está ficando complexa ana posso te ajudar depois do daily com isso pedro valeu ana seria ótimo ana eu ontem revisei o pr do módulo de autenticação tinha alguns pontos de melhoria que comentei lá roberto já vi seus comentários vou ajustar hoje ana também comecei a documentação da api nova já tem uns endpoints documentados roberto ana quando você terminar a documentação me avisa preciso adicionar os exemplos de requisição ana com certeza até o final do dia deve estar pronta pedro pessoal vocês viram que o servidor de staging está lento ana vi sim já abri um chamado com a infra eles estão verificando roberto deve ser aquele problema de memória de novo pedro é provável toda sexta isso ana vou cobrar eles hoje então é isso pessoal alguma coisa mais todos não estamos bem ana então bom trabalho e qualquer coisa me chamem no slack",
        "observacoes": "Daily standup rápido, equipe alinhada e progredindo bem"
    },
    {
        "organizador": "fernando.lima",
        "titulo": "Apresentação de Resultados Q4 2024",
        "duracao": 5400,  # 1h30min
        "participantes": ["Fernando Augusto Lima", "Carlos Eduardo Mendes", "Mariana Ferreira Costa", "Juliana Martinez"],
        "transcricao": "fernando boa tarde a todos obrigado por estarem aqui vamos começar a apresentação dos resultados do quarto trimestre de dois mil e vinte e quatro primeiro slide por favor como vocês podem ver tivemos um crescimento de quinze por cento comparado ao mesmo período do ano anterior isso representa três milhões e meio a mais em receita carlos fernando esses números incluem o novo contrato com a multinacional fernando sim carlos inclusive foi o que mais impactou se não fosse esse contrato estaríamos em apenas oito por cento de crescimento mariana fernando e sobre as despesas com pessoal como ficamos fernando boa pergunta mariana as despesas com folha aumentaram doze por cento mas isso era esperado devido às contratações que fizemos no terceiro trimestre o importante é que a proporção despesa receita melhorou juliana fernando podemos ver os números por departamento fernando claro juliana próximo slide aqui temos a breakdown por departamento tecnologia cresceu vinte e dois por cento marketing quinze por cento e operações manteve estável carlos o crescimento de tecnologia está relacionado aos novos projetos fernando exatamente carlos os projetos de transformação digital dos clientes impulsionaram bastante também aumentamos a equipe em trinta por cento mariana e a retenção de talentos como está fernando a retenção está em noventa e dois por cento bem acima da média do mercado que é oitenta e cinco por cento o programa de benefícios que implementamos está funcionando juliana sobre o marketing tivemos retorno dos investimentos em mídia digital fernando sim o roi está em trezentos por cento cada real investido trouxe três de volta mas precisamos diversificar os canais estamos muito dependentes de google ads carlos concordo fernando qual a projeção para o primeiro trimestre fernando conservadoramente estamos projetando crescimento de dez por cento mas se fecharmos os dois contratos em negociação pode chegar a dezoito por cento mariana precisamos contratar mais gente fernando sim já está no planejamento mais quinze vagas para tecnologia e cinco para marketing juliana e o orçamento para isso fernando já está aprovado começamos as contratações em janeiro carlos algum risco que precisamos monitorar fernando o principal risco é a renovação do contrato com nosso maior cliente representa trinta por cento da receita mas as conversas estão avançadas mariana quando saberemos fernando até final de janeiro devemos ter uma posição carlos ok fernando bom trabalho a todos continuem assim e vamos focar nesses novos contratos todos obrigado fernando até a próxima",
        "observacoes": "Apresentação executiva com foco em números e estratégia"
    },
    {
        "organizador": "mariana.costa",
        "titulo": "Reunião de Alinhamento - Processo Seletivo",
        "duracao": 2700,  # 45 minutos
        "participantes": ["Mariana Ferreira Costa", "Carlos Eduardo Mendes", "Ana Paula Silva"],
        "transcricao": "mariana oi gente obrigada por separarem um tempo precisamos alinhar o processo seletivo para as novas vagas de tecnologia carlos quantas vagas são ao todo mariana carlos temos quinze vagas aprovadas cinco para desenvolvedores senior três para pleno quatro para júnior dois devops e um arquiteto de software ana mariana qual o prazo para preenchermos essas vagas mariana idealmente até final de fevereiro mas sei que está agressivo principalmente para os seniors carlos é bem agressivo mesmo o mercado está aquecido está difícil encontrar senior mariana por isso queria conversar sobre a estratégia podemos aumentar o range salarial carlos quanto você sugere mariana para senior sugiro aumentar vinte por cento do teto atual estamos perdendo candidatos para concorrentes ana concordo perdemos três excelentes candidatos mês passado por proposta salarial carlos ok vamos ajustar e sobre os benefícios mariana já melhoramos bastante temos vale alimentação e refeição separados plano de saúde premium gympass auxílio home office de trezentos reais ana podemos incluir auxílio educação mariana boa ideia ana quanto você sugere ana mil e quinhentos por ano para cursos e certificações carlos aprovado mais alguma coisa mariana sim sobre o processo em si quero implementar uma etapa de pair programming para os devs o que acham ana excelente ideia ajuda muito a avaliar como a pessoa trabalha em equipe carlos concordo mas não pode ser muito longa uma hora no máximo mariana perfeito uma hora de pair programming após a entrevista técnica ana e para os juniores mariana para júnior podemos fazer um desafio mais simples para fazer em casa carlos mas com prazo curto para não perdermos candidatos mariana sim quarenta e oito horas no máximo ana mariana como está o pipeline atual mariana temos oitenta cvs em análise já agendei quinze entrevistas para semana que vem carlos precisa de ajuda ana e eu podemos participar de algumas ana com certeza posso fazer as técnicas mariana ótimo vou montar uma agenda compartilhada carlos sobre o onboarding já temos o processo estruturado mariana sim criei um programa de duas semanas primeiro dia é com rh e apresentação da empresa depois cada um vai para sua equipe com um buddy definido ana importante definirmos os buddies com antecedência mariana com certeza vou falar com os líderes carlos perfeito mariana mais algum ponto todos acho que cobrimos tudo mariana então é isso vou ajustar as descrições de vaga com o novo salário e benefícios e começo a publicar amanhã carlos ótimo mantém a gente atualizado ana qualquer coisa estamos aqui mariana obrigada gente até mais",
        "observacoes": "Definição de estratégia de contratação e processo seletivo"
    }
]

# Inserir reuniões
print("\n🔄 Inserindo reuniões no Supabase...")
for dados_reuniao in transcricoes:
    try:
        # Buscar ID do organizador
        organizador = users.get(dados_reuniao["organizador"])
        if not organizador:
            print(f"❌ Organizador {dados_reuniao['organizador']} não encontrado")
            continue
        
        # Calcular timestamps
        start_time = datetime.now() - timedelta(days=random.randint(1, 30), hours=random.randint(0, 8))
        end_time = start_time + timedelta(seconds=dados_reuniao["duracao"])
        
        # Extrair pontos principais e decisões da transcrição (simulação)
        palavras = dados_reuniao["transcricao"].split()
        key_points = []
        decisions = []
        action_items = []
        
        # Simular extração de pontos principais (em produção seria feito por IA)
        if "sprint" in dados_reuniao["titulo"].lower():
            key_points = [
                "Revisão dos resultados da sprint anterior", 
                "Distribuição de tarefas para nova sprint",
                "Definição de prioridades e prazos",
                "Identificação de impedimentos técnicos"
            ]
            decisions = [
                "Usar WebSockets para sistema de notificações",
                "Priorizar correção do gateway de pagamento",
                "Atualizar documentação da API"
            ]
            action_items = [
                {"action": "Finalizar integração gateway de pagamento", "responsible": "Roberto dos Santos", "deadline": (start_time + timedelta(days=3)).isoformat()},
                {"action": "Criar designs das notificações", "responsible": "Patricia Rocha", "deadline": (start_time + timedelta(days=2)).isoformat()},
                {"action": "Implementar filtros de busca avançados", "responsible": "Pedro Henrique Oliveira", "deadline": (start_time + timedelta(days=5)).isoformat()}
            ]
        elif "daily" in dados_reuniao["titulo"].lower():
            key_points = [
                "Status das tarefas em andamento",
                "Identificação de bloqueios",
                "Alinhamento da equipe"
            ]
            decisions = [
                "Priorizar correção de performance no servidor staging",
                "Revisar PRs pendentes até final do dia"
            ]
            action_items = [
                {"action": "Resolver problema de webhooks", "responsible": "Roberto dos Santos", "deadline": start_time.isoformat()},
                {"action": "Ajudar com queries complexas", "responsible": "Ana Paula Silva", "deadline": start_time.isoformat()}
            ]
        elif "resultados" in dados_reuniao["titulo"].lower():
            key_points = [
                "Crescimento de 15% no trimestre",
                "Receita adicional de R$ 3.5 milhões",
                "Departamento de tecnologia cresceu 22%",
                "Taxa de retenção em 92%"
            ]
            decisions = [
                "Aprovar contratação de 15 pessoas para tecnologia",
                "Aumentar investimento em canais de marketing digital",
                "Focar na renovação do contrato principal"
            ]
            action_items = [
                {"action": "Iniciar processo de contratação", "responsible": "Mariana Ferreira Costa", "deadline": (start_time + timedelta(days=15)).isoformat()},
                {"action": "Negociar renovação contrato principal", "responsible": "Fernando Augusto Lima", "deadline": (start_time + timedelta(days=30)).isoformat()}
            ]
        else:
            key_points = [
                "Definir estratégia de contratação",
                "Ajustar faixa salarial para seniors",
                "Implementar novo processo seletivo",
                "Estruturar programa de onboarding"
            ]
            decisions = [
                "Aumentar salário senior em 20%",
                "Incluir auxílio educação de R$ 1.500/ano",
                "Adicionar etapa de pair programming no processo"
            ]
            action_items = [
                {"action": "Atualizar descrições de vaga", "responsible": "Mariana Ferreira Costa", "deadline": (start_time + timedelta(days=1)).isoformat()},
                {"action": "Agendar entrevistas técnicas", "responsible": "Ana Paula Silva", "deadline": (start_time + timedelta(days=7)).isoformat()}
            ]
        
        # Criar resumo executivo
        summary = f"Reunião realizada em {start_time.strftime('%d/%m/%Y')} com duração de {dados_reuniao['duracao']//60} minutos. "
        summary += f"Participaram {len(dados_reuniao['participantes'])} pessoas. "
        summary += f"Foram discutidos {len(key_points)} pontos principais e tomadas {len(decisions)} decisões importantes. "
        summary += dados_reuniao.get("observacoes", "")
        
        reuniao = {
            "user_id": organizador["id"],
            "title": dados_reuniao["titulo"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": dados_reuniao["duracao"],
            "status": "completed",
            "observations": dados_reuniao.get("observacoes", ""),
            "transcription_full": dados_reuniao["transcricao"],
            "transcription_summary": summary,
            "key_points": key_points,
            "decisions": decisions,
            "action_items": action_items,
            "participants": dados_reuniao["participantes"]
        }
        
        response = supabase.table('meetings').insert(reuniao).execute()
        print(f"✅ Reunião '{dados_reuniao['titulo']}' inserida com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao inserir reunião '{dados_reuniao['titulo']}': {str(e)}")

# Verificar inserção
print("\n📊 Verificando reuniões inseridas:")
try:
    meetings = supabase.table('meetings').select("*").order("start_time", desc=True).execute()
    print(f"Total de reuniões no banco: {len(meetings.data)}")
    for meeting in meetings.data:
        print(f"  - {meeting['title']} ({meeting['start_time'][:10]}) - {meeting['duration_seconds']//60} min")
except Exception as e:
    print(f"❌ Erro ao verificar reuniões: {str(e)}")

print("\n✅ Script de reuniões concluído!")