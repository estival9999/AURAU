"""
Módulo de banco de dados do sistema AURALIS
"""

# Tentar importar o handler do Supabase
try:
    from .supabase_handler import SupabaseHandler, supabase_handler
    HAS_SUPABASE = True
except ImportError as e:
    print(f"[AVISO] Supabase não disponível: {e}")
    SupabaseHandler = None
    supabase_handler = None
    HAS_SUPABASE = False

__all__ = ['SupabaseHandler', 'supabase_handler', 'HAS_SUPABASE']