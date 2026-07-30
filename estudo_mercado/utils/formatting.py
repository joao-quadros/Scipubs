import re

def format_currency_brl(val):
    """Formata um valor numérico como moeda em Real (R$)."""
    try:
        val_float = float(val)
        return f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def clean_markdown_codeblocks(text):
    """Remove delimitadores markdown ```json ou ```markdown do texto retornado pela IA."""
    if not text:
        return ""
    text = str(text).strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json|markdown|html)?\n|```$', '', text, flags=re.MULTILINE).strip()
    return text

def truncate_text(text, max_len=150):
    """Trunca um texto longo adicionando reticências."""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."
