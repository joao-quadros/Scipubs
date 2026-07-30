# Setup do Ollama para SciPubs

O Ollama é uma solução gratuita para rodar modelos de IA localmente, sem custos de API.

## Instalação

### Windows
1. Baixe o instalador em: https://ollama.ai/download
2. Execute o instalador e siga as instruções
3. Após instalação, abra o terminal (PowerShell ou CMD)

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## Instalar o Modelo Llama 3

Após instalar o Ollama, instale o modelo Llama 3:

```bash
ollama pull llama3
```

Isso baixará o modelo Llama 3 8B (aprox. 4.7GB). Para um modelo mais potente (mas mais lento), use:

```bash
ollama pull llama3:70b
```

## Verificar Instalação

Teste se o Ollama está funcionando:

```bash
ollama run llama3 "Olá, como você está?"
```

## Instalar Biblioteca Python

No ambiente do seu projeto:

```bash
pip install ollama
```

## Configurar no SciPubs

No arquivo `app.py`, o modelo será usado automaticamente. Certifique-se de que:

1. O Ollama está rodando em background
2. O modelo Llama 3 está instalado
3. A biblioteca Python `ollama` está instalada

## Solução de Problemas

### Ollama não é reconhecido
- Verifique se o serviço Ollama está rodando
- No Windows: verifique se o Ollama está no PATH
- Reinicie o terminal após instalação

### Modelo lento
- Use Llama 3 8B em vez de 70B
- Verifique se há memória RAM disponível
- Feche outros aplicativos pesados

### Erro de conexão
- Verifique se o Ollama está rodando: `ollama list`
- Reinicie o serviço Ollama se necessário

## Uso no Código

```python
import ollama

response = ollama.generate(
    model='llama3',
    prompt='Seu prompt aqui',
    stream=False
)

print(response['response'])
```

## Alternativa: Groq (Ultra-rápido)

Se preferir uma solução cloud ultra-rápida com free tier generoso:

1. Crie conta em: https://groq.com/
2. Obtenha API key gratuita
3. Instale: `pip install groq`
4. Configure no código (similar ao Gemini atual)

O Groq é significativamente mais rápido (500 tokens/s) mas depende de internet.
