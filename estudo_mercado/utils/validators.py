def validate_api_key(api_key):
    """Valida o formato básico da chave API do Gemini (Google AI Studio)."""
    if not api_key:
        return False, "Por favor, informe uma chave API válida do Gemini."
    api_key_str = str(api_key).strip()
    if len(api_key_str) < 20 or not api_key_str.startswith("AIza"):
        return False, "A chave API informada não possui o formato esperado do Google AI Studio (iniciando com 'AIza...')."
    return True, "Chave API válida!"

def validate_briefing_form(nome_projeto, segmento, descricao):
    """Valida os campos obrigatórios do formulário de Briefing da Etapa 1."""
    errors = []
    if not nome_projeto or len(str(nome_projeto).strip()) < 3:
        errors.append("O 'Nome do Projeto' deve ter pelo menos 3 caracteres.")
    if not segmento or len(str(segmento).strip()) < 2:
        errors.append("O 'Segmento / Nicho de Mercado' é obrigatório.")
    if not descricao or len(str(descricao).strip()) < 20:
        errors.append("A 'Descrição do Produto/Serviço' deve ter pelo menos 20 caracteres para garantir uma análise precisa da IA.")
    
    if errors:
        return False, errors
    return True, []
