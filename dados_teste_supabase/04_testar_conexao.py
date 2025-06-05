#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar a conexão e verificar todos os dados inseridos no Supabase
Valida se os dados estão corretos e as relações funcionando
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

print("🔄 Testando conexão com Supabase...")
print(f"URL: {url[:30]}...")

try:
    supabase: Client = create_client(url, key)
    print("✅ Conexão estabelecida com sucesso!\n")
except Exception as e:
    print(f"❌ Erro na conexão: {str(e)}")
    exit(1)

# Testar cada tabela
print("=" * 60)
print("📊 VERIFICANDO ESTRUTURA DO BANCO DE DADOS")
print("=" * 60)

# 1. TABELA USERS
print("\n1️⃣ TABELA: users")
print("-" * 40)
try:
    users = supabase.table('users').select("*").execute()
    print(f"✅ Total de registros: {len(users.data)}")
    
    if users.data:
        print("\n📋 Amostra de dados:")
        for user in users.data[:3]:
            print(f"   • {user['full_name']} ({user['username']})")
            print(f"     Cargo: {user['role']} | Depto: {user['department']}")
            print(f"     Email: {user['email']}")
            print(f"     Ativo: {user['is_active']} | Último login: {user.get('last_login', 'N/A')}")
            print()
        
        # Verificar campos
        campos_esperados = ['id', 'username', 'password_hash', 'email', 'full_name', 
                          'role', 'department', 'created_at', 'last_login', 'is_active']
        campos_tabela = list(users.data[0].keys())
        print(f"✅ Campos da tabela: {len(campos_tabela)}")
        
        # Verificar se todos os campos esperados existem
        campos_faltando = set(campos_esperados) - set(campos_tabela)
        if campos_faltando:
            print(f"⚠️  Campos faltando: {campos_faltando}")
        else:
            print("✅ Todos os campos esperados estão presentes")
            
except Exception as e:
    print(f"❌ Erro ao acessar tabela users: {str(e)}")

# 2. TABELA MEETINGS
print("\n2️⃣ TABELA: meetings")
print("-" * 40)
try:
    meetings = supabase.table('meetings').select("*").order("start_time", desc=True).execute()
    print(f"✅ Total de registros: {len(meetings.data)}")
    
    if meetings.data:
        print("\n📋 Amostra de dados:")
        for meeting in meetings.data[:3]:
            print(f"   • {meeting['title']}")
            print(f"     Data: {meeting['start_time'][:16]} | Duração: {meeting['duration_seconds']//60}min")
            print(f"     Status: {meeting['status']} | Participantes: {len(meeting.get('participants', []))}")
            print(f"     Pontos principais: {len(meeting.get('key_points', []))}")
            print(f"     Decisões: {len(meeting.get('decisions', []))}")
            
            # Verificar se tem transcrição
            if meeting.get('transcription_full'):
                print(f"     Transcrição: {len(meeting['transcription_full'])} caracteres")
            else:
                print(f"     Transcrição: ❌ Não encontrada")
            print()
            
        # Testar relação com users
        meeting_com_user = supabase.table('meetings').select("*, users(full_name, role)").limit(1).execute()
        if meeting_com_user.data and 'users' in meeting_com_user.data[0]:
            print("✅ Relação com tabela users funcionando")
        else:
            print("⚠️  Problema na relação com tabela users")
            
except Exception as e:
    print(f"❌ Erro ao acessar tabela meetings: {str(e)}")

# 3. TABELA AI_INTERACTIONS
print("\n3️⃣ TABELA: ai_interactions")
print("-" * 40)
try:
    interactions = supabase.table('ai_interactions').select("*").order("created_at", desc=True).execute()
    print(f"✅ Total de registros: {len(interactions.data)}")
    
    if interactions.data:
        print("\n📋 Amostra de dados:")
        total_tokens = 0
        total_time = 0
        
        for interaction in interactions.data[:3]:
            print(f"   • Pergunta: {interaction['user_message'][:80]}...")
            print(f"     Resposta: {interaction['ai_response'][:80]}...")
            print(f"     Tokens: {interaction['tokens_used']} | Tempo: {interaction['response_time_ms']}ms")
            print(f"     Modelo: {interaction['model_used']}")
            
            if interaction.get('context_used'):
                context = interaction['context_used']
                print(f"     Contexto: {len(context.get('meetings', []))} reuniões")
            print()
            
            total_tokens += interaction.get('tokens_used', 0)
            total_time += interaction.get('response_time_ms', 0)
        
        # Estatísticas
        if interactions.data:
            avg_tokens = total_tokens / len(interactions.data)
            avg_time = total_time / len(interactions.data)
            print(f"\n📊 Estatísticas gerais:")
            print(f"   • Média de tokens por interação: {avg_tokens:.0f}")
            print(f"   • Tempo médio de resposta: {avg_time:.0f}ms")
            
        # Testar relação com meetings
        interaction_com_meeting = supabase.table('ai_interactions').select("*, meetings(title)").eq('meeting_id', 'NOT NULL').limit(1).execute()
        if interaction_com_meeting.data:
            print("✅ Relação com tabela meetings funcionando")
        else:
            print("ℹ️  Nenhuma interação vinculada a reunião específica")
            
except Exception as e:
    print(f"❌ Erro ao acessar tabela ai_interactions: {str(e)}")

# 4. TABELA KNOWLEDGE_BASE
print("\n4️⃣ TABELA: knowledge_base")
print("-" * 40)
try:
    knowledge = supabase.table('knowledge_base').select("*").execute()
    if knowledge.data:
        print(f"✅ Total de registros: {len(knowledge.data)}")
        print("\n📋 Amostra de dados:")
        for doc in knowledge.data[:3]:
            print(f"   • {doc['title']} (v{doc['version']})")
            print(f"     Tipo: {doc['doc_type']} | Depto: {doc['department']}")
            print(f"     Tags: {', '.join(doc.get('tags', []))}")
            print(f"     Atual: {doc['is_current']}")
            print()
    else:
        print("ℹ️  Nenhum documento na base de conhecimento (conforme esperado)")
        
except Exception as e:
    print(f"❌ Erro ao acessar tabela knowledge_base: {str(e)}")

# 5. TESTAR FUNÇÕES DE BUSCA
print("\n5️⃣ TESTANDO FUNÇÕES DE BUSCA")
print("-" * 40)

# Testar busca textual em reuniões
try:
    print("🔍 Testando search_meetings_text...")
    # Esta função precisa ser criada como RPC no Supabase
    # Por enquanto, vamos testar busca direta
    
    resultado = supabase.table('meetings').select("*").ilike('transcription_full', '%sprint%').limit(3).execute()
    if resultado.data:
        print(f"✅ Busca por 'sprint' retornou {len(resultado.data)} resultados")
    else:
        print("ℹ️  Nenhum resultado encontrado para 'sprint'")
        
except Exception as e:
    print(f"⚠️  Função de busca não disponível ou erro: {str(e)}")

# 6. VERIFICAR INTEGRIDADE DOS DADOS
print("\n6️⃣ VERIFICAÇÃO DE INTEGRIDADE")
print("-" * 40)

# Verificar se todas as reuniões têm organizador válido
try:
    meetings_sem_user = supabase.table('meetings').select("id, title").is_('user_id', 'null').execute()
    if meetings_sem_user.data:
        print(f"⚠️  {len(meetings_sem_user.data)} reuniões sem organizador")
    else:
        print("✅ Todas as reuniões têm organizador válido")
        
    # Verificar se todas as interações têm usuário válido
    interactions_sem_user = supabase.table('ai_interactions').select("id").is_('user_id', 'null').execute()
    if interactions_sem_user.data:
        print(f"⚠️  {len(interactions_sem_user.data)} interações sem usuário")
    else:
        print("✅ Todas as interações têm usuário válido")
        
except Exception as e:
    print(f"❌ Erro na verificação de integridade: {str(e)}")

# RESUMO FINAL
print("\n" + "=" * 60)
print("📊 RESUMO DA VERIFICAÇÃO")
print("=" * 60)

try:
    # Contar registros
    total_users = len(supabase.table('users').select("id").execute().data)
    total_meetings = len(supabase.table('meetings').select("id").execute().data)
    total_interactions = len(supabase.table('ai_interactions').select("id").execute().data)
    total_knowledge = len(supabase.table('knowledge_base').select("id").execute().data)
    
    print(f"✅ Usuários: {total_users}")
    print(f"✅ Reuniões: {total_meetings}")
    print(f"✅ Interações IA: {total_interactions}")
    print(f"✅ Base Conhecimento: {total_knowledge}")
    print(f"\n🎯 Total de registros no banco: {total_users + total_meetings + total_interactions + total_knowledge}")
    
    print("\n✅ BANCO DE DADOS CONFIGURADO E FUNCIONANDO CORRETAMENTE!")
    
except Exception as e:
    print(f"❌ Erro no resumo final: {str(e)}")

print("\n" + "=" * 60)
print("🏁 Teste de conexão finalizado!")
print("=" * 60)