# EstratÃ©gia de Pesquisa de Objetivos e Escopos de PeriÃ³dicos CientÃ­ficos

## VisÃ£o Geral

Esta estratÃ©gia visa coletar informaÃ§Ãµes sobre objetivos, missÃµes e escopos de periÃ³dicos cientÃ­ficos para enriquecer seu banco de dados, combinando mÃºltiplas fontes e abordagens.

## Etapa 1: AnÃ¡lise do Estado Atual

### Fontes Existentes JÃ¡ Implementadas
- **OpenAlex API** - Busca `description` + `summary` (script: `fetch_aims_scope.py`)
- **SciELO ArticleMeta API** - Busca `mission` em portuguÃªs/inglÃªs/espanhol
- **CrossRef API** - Busca `description` e `subjects` (script: `map_editorial_profile_v2.py`)
- **Scraping de Homepages** - ExtraÃ§Ã£o via BeautifulSoup

### Verificar Dados Atuais
```powershell
# Contar revistas com Aims & Scope preenchidos
python -c "
import pandas as pd
df = pd.read_csv('dados.csv', sep=';', encoding='utf-8-sig', low_memory=False)
col = [c for c in df.columns if 'aims' in c.lower() or 'escopo' in c.lower()][0]
total = len(df)
com_escopo = df[col].astype(str).str.len().apply(lambda x: x > 30).sum()
print(f'Total: {total}, Com escopo: {com_escopo}, % completo: {100*com_escopo/total:.1f}%')
"
```

## Etapa 2: EstratÃ©gia de Pesquisa por Homepage

### 2.1 Scraping Direto de Homepage
Para cada revista com Homepage vÃ¡lida, buscar:

```python
# URLs comuns para Aims & Scope (jÃ¡ implementado)
PATTERNS = [
    "/about", "/aims-and-scope", "/aims", "/scope", 
    "/about-the-journal", "/editorial-info", 
    "/journalAimsAndScope", "/pages/view/aims-scope"
]

# Palavras-chave para identificar links relevantes
KEYWORDS = ['aim', 'scope', 'about', 'mission', 'focus', 'overview', 'journal-info']
```

### 2.2 ExtraÃ§Ã£o via BeautifulSoup
- Procurar elementos `<div class="aims">`, `<section id="scope">`, `<div class="about">`
- Buscar parÃ¡grafos com conteÃºdo entre 100-2000 caracteres
- Limitar texto a 1500 caracteres para evitar conteÃºdo muito longo

## Etapa 3: EstratÃ©gia de Pesquisa Automatizada no Google

### 3.1 APIs Recomendadas (menos bloqueio)
**SerpAPI** - API oficial de busca Google
```python
import requests

SERP_API_KEY = "sua_chave"
query = f"site:{homepage} \"aims and scope\" OR \"missÃ£o e objetivos\""
url = f"https://serpapi.com/search?api_key={SERP_API_KEY}&q={query}&num=5"
```

**Google Programmable Search Engine**
- Mais estÃ¡vel para grandes volumes
- Requer configuraÃ§Ã£o no Google Cloud Console

### 3.2 Busca Direta via Google Search
```python
# Busca por: "Nome da Revista" + "aims and scope" + "journal"
# Extrai snippets e URLs diretos
# Usa biblioteca googlesearch-python ou requests + parsing
```

### 3.3 Pontos-Chave para Google Search
- **Rate limiting**: MÃ¡ximo 1 requisiÃ§Ã£o/segundo
- **User-Agent rotativo** para evitar bloqueio
- **Query patterns**:
  - `"{journal_name}" "aims and scope"`
  - `"{journal_name}" "mission statement"`
  - `"{journal_name}" site:springer.com OR site:elsevier.com OR site:wiley.com`

## Etapa 4: EstratÃ©gia HÃ­brida e Fallback

### Ordem de Busca Recomendada:
1. **OpenAlex API** (ISSN) â†’ Se encontrado, usa `description` + `summary`
2. **SciELO ArticleMeta** (ISSN) â†’ Se encontrado, usa `mission`
3. **CrossRef API** (ISSN) â†’ Se encontrado, usa `description`
4. **Scraping Homepage** â†’ URLs comuns + links internos
5. **Google Search** â†’ Como Ãºltimo recurso

### Cache e Checkpoints
- Salvar resultados em cada fonte para nÃ£o refazer buscas
- Usar CSV com colunas: `Homepage`, `Aims and Scope`, `Fonte_Dados`, `Data_Busca`
- HistÃ³rico de tentativas falhas para retry posterior

## Etapa 5: ImplementaÃ§Ã£o Python

### 5.1 Script Unificado (create_search_strategy.py)
```python
#!/usr/bin/env python3
"""
Busca objetivos/escopos usando mÃºltiplas fontes em ordem de prioridade.
"""

import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional

# ConfiguraÃ§Ãµes
BATCH_SIZE = 50
DELAY_BETWEEN_REQUESTS = 1.0  # segundos
MAX_TEXT_LENGTH = 1500

def search_from_homepage(url: str, title: str) -> Optional[str]:
    """Extrai Aims & Scope da homepage ou pÃ¡ginas relacionadas."""
    pass  # implementaÃ§Ã£o existente em map_editorial_profile_v2.py

def search_from_openalex(issn: str) -> Optional[str]:
    """Busca na API OpenAlex."""
    pass  # implementaÃ§Ã£o existente

def search_from_google(title: str, homepage: str) -> Optional[str]:
    """Busca informaÃ§Ãµes via Google Search (Ãºltimo recurso)."""
    pass  # nova implementaÃ§Ã£o

def main():
    df = pd.read_csv('dados.csv', sep=';', encoding='utf-8-sig')
    # ImplementaÃ§Ã£o completa...
```

### 5.2 Adicionar ao requirements.txt
```
beautifulsoup4>=4.12.0
serpapi>=1.0.0  # opcional, para Google Search
googlesearch-python>=3.0.0  # alternativa gratuita
```

## Etapa 6: ExecuÃ§Ã£o e Monitoramento

### 6.1 ExecuÃ§Ã£o em Lotes
```bash
# Executar script existente (jÃ¡ faz checkpoints)
python scripts/fetch_aims_scope.py

# Ou executar novo script hÃ­brido
python scripts/search_strategy.py --batch-size 100 --delay 1.5
```

### 6.2 Monitoramento
- Log de progresso a cada 50 registros
- Contagem de sucessos/falhas por fonte
- Arquivo de log separado: `logs/search_scope.log`

## Etapa 7: Melhorias e OtimizaÃ§Ãµes

### 7.1 DetecÃ§Ã£o de Dados Duplicados
- Comparar Aims & Scope entre duplicatas de ISSN
- Manter apenas texto Ãºnico e mais longo

### 7.2 TraduÃ§Ã£o de Textos
- Usar Google Translate API ou argostranslate
- Traduzir textos em francÃªs, alemÃ£o, chinÃªs para portuguÃªs

### 7.3 Limpeza de Texto
- Remover HTML entities (`&`, `&nbsp;`)
- Normalizar quebras de linha
- Remover caracteres nÃ£o imprimÃ­veis

## Fluxo Recomendado

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   CSV com ISSNs e Homepages     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚
              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  1. OpenAlex (ISSN)             â”‚
â”‚  Encontrou? â”€â”€â–º Usar descriÃ§Ã£o   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚ NÃ£o encontrou
              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  2. SciELO (ISSN)               â”‚
â”‚  Encontrou? â”€â”€â–º Usar missÃ£o      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚ NÃ£o encontrou
              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  3. CrossRef (ISSN)             â”‚
â”‚  Encontrou? â”€â”€â–º Usar descriÃ§Ã£o   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚ NÃ£o encontrou
              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  4. Scraping Homepage            â”‚
â”‚  Encontrou? â”€â”€â–º Usar texto      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚ NÃ£o encontrou
              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  5. Google Search (Ãºltimo)      â”‚
â”‚  Busca "aims and scope" + nome   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## PrÃ³ximos Passos

1. [ ] Executar anÃ¡lise de cobertura atual dos dados
2. [ ] Testar script existente `fetch_aims_scope.py`
3. [ ] Instalar dependÃªncias novas (serpapi se necessÃ¡rio)
4. [ ] Criar/abrir script de pesquisa hÃ­brida
5. [ ] Executar em lote e monitorar resultados

---
*Documento criado para orientar a coleta de dados de objetivos e escopos de periÃ³dicos cientÃ­ficas*
