import streamlit as st
from services.gemini_client import GeminiMarketClient

def render_chat_assistant():
    """Renderiza a Etapa 4: Assistente Estratégico Interativo (Chatbot I.A.)."""
    st.markdown("### 💬 Assistente Estratégico de Mercado")
    st.write("Faça perguntas específicas sobre o seu estudo de mercado, concorrência, posicionamento ou objeções de clientes.")

    study_data = st.session_state.get("study_data")
    project_info = st.session_state.get("project_info")
    api_key = st.session_state.get("gemini_api_key")

    if not study_data or not project_info:
        st.warning("⚠️ Nenhuma análise ativa. Crie o estudo na Etapa 1 para conversar com o assistente.")
        return

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Exibe Histórico de Mensagens
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Sugestões Rápidas de Perguntas
    st.markdown("##### 💡 Perguntas Sugeridas:")
    cols = st.columns(3)
    prompt_to_send = None

    with cols[0]:
        if st.button("🎯 Como posso me diferenciar no preço?"):
            prompt_to_send = "Com base no estudo, como posso diferenciar minha estratégia de precificação contra a concorrência?"
    with cols[1]:
        if st.button("⚠️ Quais as 3 maiores objeções do cliente?"):
            prompt_to_send = "Quais são as 3 maiores objeções que o público-alvo pode ter e como superá-las?"
    with cols[2]:
        if st.button("🚀 Quais canais de aquisição usar?"):
            prompt_to_send = "Quais os 3 melhores canais de aquisição de clientes (Go-to-Market) para este segmento?"

    # Campo de Entrada de Mensagem do Usuário
    user_input = st.chat_input("Digite sua dúvida estratégica sobre o mercado...")
    if user_input:
        prompt_to_send = user_input

    if prompt_to_send:
        if not api_key:
            st.error("⚠️ Chave API do Gemini não configurada.")
            return

        # Adiciona pergunta do usuário ao histórico
        st.session_state["chat_history"].append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.write(prompt_to_send)

        # Monta prompt contextualizado
        context_prompt = f"""
        Você é um consultor sênior especialista no mercado de {project_info.get('segmento')}.
        Estudo do Projeto: {project_info.get('nome_projeto')} - {project_info.get('descricao')}
        Resumo Executivo da Análise: {study_data.get('resumo_executivo')}
        Matriz SWOT: {study_data.get('matriz_swot')}
        Concorrentes Mapeados: {study_data.get('concorrentes')}

        PERGUNTA DO USUÁRIO: {prompt_to_send}
        Responda objetivamente em 2-3 parágrafos estratégicos.
        """

        with st.chat_message("assistant"):
            with st.spinner("Pensando na resposta estratégica..."):
                try:
                    client = GeminiMarketClient(api_key=api_key)
                    answer = client.generate_content(context_prompt)
                    st.write(answer)
                    st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erro no assistente: {e}")
