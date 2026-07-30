# Estudo de Mercado por IA

Aplicativo inteligente para automação de estudos de mercado, análise competitiva, matriz SWOT e geração de relatórios executivos acionáveis utilizando Google Gemini 2.5.

## 📁 Estrutura do Projeto

```
estudo_mercado/
├── app.py                     # Arquivo principal Streamlit (Navegação & Estado)
├── components/                # Componentes reutilizáveis de UI
│   ├── __init__.py
│   ├── header.py              # Hero Header e Badges
│   ├── sidebar.py             # Configurações de API Key e Navegação
│   ├── form_input.py          # Formulário da Etapa 1 (Briefing)
│   ├── report_view.py         # Dashboard (Etapa 2), Benchmarking (Etapa 3), Export (Etapa 5)
│   └── chat_assistant.py      # Assistente Interativo (Etapa 4)
├── services/                  # Motores de IA e Dados
│   ├── __init__.py
│   ├── gemini_client.py       # Integração com Gemini 2.5 Flash / Pro
│   ├── openalex_client.py     # Coleta de artigos/dados científicos de mercado
│   ├── data_scraper.py        # Extrator de conteúdo de URLs concorrentes
│   └── report_generator.py   # Gerador de relatórios Markdown / HTML / PDF
├── utils/                     # Utilitários e Helpers
│   ├── __init__.py
│   ├── export.py              # Exportação Excel, PDF, JSON, Markdown
│   ├── validators.py          # Validação de formulários e chaves API
│   └── formatting.py          # Formatação de moedas, textos e badges
├── data/                      # Modelos e Cache
│   ├── templates/             # Templates de relatórios
│   └── cache/                 # Cache temporário
├── .env.example               # Modelo de variáveis de ambiente
├── requirements.txt           # Lista de dependências Python
└── README.md                  # Documentação do projeto
```

## 🚀 Como Executar

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure sua chave API do Gemini:**
   Crie um arquivo `.env` baseado no `.env.example`:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   ```

3. **Execute o aplicativo:**
   ```bash
   streamlit run app.py
   ```
