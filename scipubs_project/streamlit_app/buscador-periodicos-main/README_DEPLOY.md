# Guia de Deploy - SciPubs Hybrid Recommender

Este guia explica passo a passo como subir a nova arquitetura híbrida (PostgreSQL + pgvector + FastAPI) e conectar ao Streamlit Cloud já configurado.

## Visão Geral da Arquitetura

```
Streamlit Cloud (app.py)
         │
         │ POST /recommend
         ▼
   FastAPI (Render/Railway/fly.io)
         │
         │ SQL functions
         ▼
PostgreSQL + pgvector (Neon/Supabase)
```

---

## Passo 1: Criar o Banco PostgreSQL + pgvector

### Opção A: Neon (Recomendado - free tier generoso)

1. Acesse [https://neon.tech](https://neon.tech)
2. Crie uma conta (pode usar GitHub/Google)
3. Crie um novo projeto chamado `scipubs`
4. Crie um banco de dados chamado `scipubs_db`
5. No dashboard, copie a **Connection String** (formato `postgresql://usuario:senha@host:5432/scipubs_db`)
6. O pgvector já vem habilitado no Neon. Se não estiver, abra o **SQL Editor** e execute:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

### Opção B: Supabase

1. Acesse [https://supabase.com](https://supabase.com)
2. Crie um projeto novo
3. Vá em **Database → Extensions**
4. Habilite as extensões `vector` e `pg_trgm`
5. Copie a **Connection string** em **Project Settings → Database**

---

## Passo 2: Configurar Variáveis de Ambiente Local

1. No projeto local, copie o arquivo de exemplo:
   ```bash
   copy .env.example .env
   ```
2. Edite `.env` e preencha:
   ```env
   DATABASE_URL=postgresql://usuario:senha@host-neon.supabase.co:5432/scipubs_db
   EMBEDDING_PROVIDER=tfidf
   GEMINI_API_KEY=sua_chave_aqui
   GROQ_API_KEY=sua_chave_groq
   LLM_PROVIDER=groq
   OPENALEX_EMAIL=seu_email@example.com
   ```
   > O provider `tfidf` é 100% gratuito e não requer chave de API. O Groq oferece um generoso free tier para as justificativas via LLM.
3. No Windows PowerShell, carregue as variáveis:
   ```powershell
   Get-Content .env | ForEach-Object { if ($_ -match '^(.*?)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
   ```

---

## Passo 3: Criar as Tabelas no Banco

Execute o script de setup:

```bash
python scripts/setup_database.py
```

Se der certo, você verá: `Schema criado com sucesso.`

---

## Passo 4: Ingerir as Revistas no Banco

Este passo pode demorar (cada revista gera embeddings e busca artigos no OpenAlex).

### Teste com 50 revistas primeiro (TF-IDF, sem custo)

```bash
python scripts/ingest_journals.py --limit 50 --provider tfidf --skip-articles
```

### Ingestão completa (53.564 revistas)

```bash
python scripts/ingest_journals.py --provider tfidf --skip-articles
```

> **Dica de custo/tempo:** Com TF-IDF a ingestão é 100% gratuita. A busca de artigos no OpenAlex pode ser feita depois removendo `--skip-articles`, mas é lenta. Para testes iniciais, `--skip-articles` é recomendado.

---

## Passo 5: Testar a API Localmente

1. Inicie a API:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. Teste o health check:
   ```bash
   curl http://localhost:8000/health
   ```
3. Teste uma recomendação:
   ```bash
   curl -X POST "http://localhost:8000/recommend" `
     -H "Content-Type: application/json" `
     -d '{"title":"Machine Learning for Early Detection of Alzheimer Disease","abstract":"This study proposes a deep learning approach...","top_n":5}'
   ```

---

## Passo 6: Publicar a API na Nuvem

### Opção A: Render (Recomendada - free tier)

1. Acesse [https://render.com](https://render.com) e conecte sua conta GitHub
2. Clique em **New → Web Service**
3. Selecione o repositório `joaoquadros83/buscador-periodicos`
4. Configure:
   - **Name:** `scipubs-api`
   - **Runtime:** Docker
   - **Branch:** `main`
   - **Root Directory:** `./`
   - O Render detectará automaticamente o `Dockerfile` e `render.yaml`
5. Em **Environment Variables**, adicione:
    ```
    DATABASE_URL=postgresql://...
    GROQ_API_KEY=sua_chave_groq
    EMBEDDING_PROVIDER=tfidf
    LLM_PROVIDER=groq
    ```
    > `GEMINI_API_KEY` é opcional. Se você preferir usar Gemini, altere `EMBEDDING_PROVIDER=gemini` e `LLM_PROVIDER=gemini`.
6. Clique em **Create Web Service**
7. Aguarde o deploy (pode levar alguns minutos)
8. Anote a URL gerada (ex: `https://scipubs-api.onrender.com`)

### Opção B: Railway

1. Acesse [https://railway.app](https://railway.app)
2. Crie um novo projeto a partir do GitHub
3. Adicione as mesmas env vars acima
4. Deploy automático

---

## Passo 7: Conectar Streamlit Cloud à API

1. No [Streamlit Cloud](https://streamlit.io/cloud), acesse seu app
2. Vá em **Settings → Secrets**
3. Adicione:
   ```toml
   HYBRID_API_URL = "https://sua-url-da-api.onrender.com"
   ```
4. Clique em **Save**
5. Reinicie o app

---

## Passo 8: Testar o Sistema Completo

1. Acesse seu app no Streamlit Cloud
2. Vá até a aba **Smart Recommender (AI)**
3. Cole um título e abstract
4. Clique em **Analyze and Recommend**
5. O resultado deve vir da API híbrida

Se a API estiver offline, o app mostrará um aviso e usará o motor local como fallback.

---

## Solução de Problemas

### Erro: "API híbrida indisponível"
- Verifique se a URL da API está correta nos Secrets do Streamlit
- Verifique se a API está online acessando `/health`
- Verifique os logs do Render/Railway

### Erro de conexão com o banco
- Confirme se a `DATABASE_URL` está correta
- Verifique se o IP do Render está na whitelist do Neon/Supabase
- No Neon: vá em **Project Settings → Allowed IPs** e habilite `Allow access from any cloud service`

### Ingestão lenta
- Use `--limit 100 --provider tfidf --skip-articles` primeiro para testar
- A busca de artigos no OpenAlex é lenta; use `--skip-articles` para ingerir só revistas
- O Gemini gratuito tem rate limit de 1.500 requests/dia (opcional)

---

## Próximos Passos Opcionais

- [ ] Configurar CI/CD no GitHub Actions
- [ ] Adicionar cache Redis para queries repetidas
- [ ] Implementar autenticação na API
- [ ] Monitorar custos do Gemini via Google Cloud Console
