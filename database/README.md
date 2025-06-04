# 🗄️ AURALIS Database Setup Guide

## 📋 Overview

This directory contains all SQL scripts needed to set up the AURALIS database in Supabase. The scripts are organized in a specific order to ensure proper table creation with all dependencies.

## 🚀 Quick Setup

To set up the complete database, run the scripts in the following order:

```bash
# 1. Initial setup and extensions
psql -f 00_setup.sql

# 2. Core tables (in order)
psql -f migrations/01_users_auth.sql
psql -f migrations/02_meetings.sql
psql -f migrations/03_transcriptions.sql
psql -f migrations/04_ai_agents.sql
psql -f migrations/05_knowledge_base.sql
psql -f migrations/06_embeddings.sql
psql -f migrations/07_cache_optimization.sql
psql -f migrations/08_statistics.sql
```

## 📁 File Structure

```
database/
├── README.md                    # This file
├── 00_setup.sql                # Initial setup, extensions, and helper functions
├── migrations/
│   ├── 01_users_auth.sql      # User management and authentication
│   ├── 02_meetings.sql        # Meeting and recording tables
│   ├── 03_transcriptions.sql  # Transcriptions and analysis
│   ├── 04_ai_agents.sql       # AI agent system
│   ├── 05_knowledge_base.sql  # Document management
│   ├── 06_embeddings.sql      # Vector search (pgvector)
│   ├── 07_cache_optimization.sql # Performance optimization
│   └── 08_statistics.sql      # Analytics and statistics
├── seeds/                      # Initial data (if needed)
├── functions/                  # Additional functions (if needed)
├── policies/                   # Additional RLS policies (if needed)
└── indexes/                    # Additional indexes (if needed)
```

## 🔧 Prerequisites

### Required Extensions
- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `pg_trgm` - Trigram matching for fuzzy search
- `unaccent` - Accent-insensitive search
- `vector` - pgvector for embeddings (must be enabled in Supabase)

### Optional Extensions
- `pg_cron` - For scheduled jobs (if available)

## 📊 Database Schema Overview

### Core Modules

1. **User Management** (`01_users_auth.sql`)
   - Extended user profiles
   - Session management
   - Role-based access control

2. **Meetings** (`02_meetings.sql`)
   - Meeting lifecycle management
   - Participant tracking
   - Recording metadata

3. **Transcriptions** (`03_transcriptions.sql`)
   - Full transcriptions
   - Speaker-segmented text
   - Action items and decisions

4. **AI Agents** (`04_ai_agents.sql`)
   - Agent configurations
   - Interaction tracking
   - Inter-agent messaging

5. **Knowledge Base** (`05_knowledge_base.sql`)
   - Document management
   - Version control
   - Full-text search

6. **Vector Search** (`06_embeddings.sql`)
   - Semantic search with pgvector
   - Meeting and document embeddings
   - Search cache

7. **Performance** (`07_cache_optimization.sql`)
   - Query result caching
   - Token usage tracking
   - System metrics

8. **Analytics** (`08_statistics.sql`)
   - User statistics
   - Agent performance metrics
   - Automated aggregations

## 🔐 Security Features

- **Row Level Security (RLS)** enabled on all tables
- **Policies** for data isolation
- **Secure functions** with SECURITY DEFINER
- **Input validation** through constraints

## 🎯 Key Features

### 1. Automatic Calculations
- Meeting durations
- Token costs
- Completion rates
- Cache expiration

### 2. Full-Text Search
- Portuguese language support
- Trigram matching
- Accent-insensitive search

### 3. Vector Search
- 1536-dimensional embeddings (OpenAI)
- IVFFlat indexing for performance
- Similarity search functions

### 4. Performance Optimization
- Intelligent caching with TTL
- Batch processing support
- Comprehensive indexes
- Materialized views

### 5. Audit Trail
- Automatic timestamps
- User activity tracking
- System metrics logging

## 🛠️ Maintenance

### Regular Tasks

1. **Cache Cleanup** (hourly)
   ```sql
   SELECT public.cleanup_expired_cache();
   ```

2. **Embedding Cache Cleanup** (monthly)
   ```sql
   SELECT public.cleanup_embedding_cache(30, 2);
   ```

3. **Statistics Refresh** (daily)
   ```sql
   SELECT public.refresh_statistics_views();
   ```

### Performance Monitoring

Check cache statistics:
```sql
SELECT * FROM public.get_cache_statistics(7);
```

Check agent performance:
```sql
SELECT * FROM public.get_agent_performance_summary();
```

Check user activity:
```sql
SELECT * FROM public.get_user_activity_summary(user_id, 30);
```

## 🔄 Migration Notes

### From Development to Production

1. **Adjust cache TTLs** based on usage patterns
2. **Scale vector indexes** - increase lists parameter for larger datasets
3. **Enable pg_cron** for automated maintenance
4. **Configure backup policies**
5. **Set up monitoring alerts**

### Rollback Strategy

Each migration file includes DROP statements at the beginning, allowing for clean rollback if needed.

## 📝 Best Practices

1. **Always backup** before running migrations
2. **Test in development** environment first
3. **Monitor performance** after deployment
4. **Review RLS policies** for your use case
5. **Adjust indexes** based on query patterns

## 🚨 Troubleshooting

### Common Issues

1. **pgvector not available**
   - Enable it in Supabase dashboard under Extensions

2. **Permission denied**
   - Ensure you're running as superuser or have proper grants

3. **Foreign key violations**
   - Run scripts in the correct order

4. **Performance issues**
   - Check index usage with `EXPLAIN ANALYZE`
   - Review cache hit rates
   - Consider partitioning large tables

## 📞 Support

For issues or questions:
1. Check the main README_DATABASE_SCHEMA.md for detailed documentation
2. Review individual SQL files for inline comments
3. Consult Supabase documentation for platform-specific features