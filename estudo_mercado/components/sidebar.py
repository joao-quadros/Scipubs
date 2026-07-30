import streamlit as st
import os

def render_sidebar():
    """Renderiza a barra lateral com configurações de API, navegação e informações do projeto."""
    st.sidebar.image("https://img.icons8.com/color/96/market-analysis.png", width=64)
    st.sidebar.title("Estudo de Mercado")
    st.sidebar.caption("Inteligência Estratégica por IA")

    st.sidebar.markdown("---")
    
    # Gerenciamento da Chave API do Gemini
    st.sidebar.subheader("🔑 Configuração da API")
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    
    api_key_input = st.sidebar.text_input(
        "Chave API Gemini (Google AI Studio)",
        value=st.session_state.get("gemini_api_key", env_api_key),
        type="password",
        help="Obtenha uma chave gratuita em: https://aistudio.google.com/"
    )
    
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input
        st.sidebar.success("Chave API configurada!", icon="✅")
    else:
        st.sidebar.warning("Cole sua chave API para habilitar as análises por IA.", icon="⚠️")

    st.sidebar.markdown("---")
    
    # Navegação entre as 5 Etapas
    st.sidebar.subheader("📌 Etapas do Estudo")
    etapa_options = [
        "1. Briefing & Ingestão",
        "2. Painel Executivo & SWOT",
        "3. Benchmarking Competitivo",
        "4. Chatbot Estratégico",
        "5. Central de Exportação"
    ]
    
    selected_etapa = st.sidebar.radio(
        "Selecione a tela:",
        etapa_options,
        index=st.session_state.get("etapa_index", 0)
    )

    st.sidebar.markdown("---")

    # Informações do Estudo Atual na Sessão
    if st.session_state.get("project_info"):
        proj = st.session_state["project_info"]
        st.sidebar.subheader("📁 Projeto Ativo")
        st.sidebar.markdown(f"**Nome:** {proj.get('nome_projeto')}")
        st.sidebar.markdown(f"**Nicho:** {proj.get('segmento')}")
        if st.sidebar.button("🗑️ Limpar Estudo Atual", use_container_width=True):
            st.session_state["project_info"] = None
            st.session_state["study_data"] = None
            st.session_state["chat_history"] = []
            st.session_state["etapa_index"] = 0
            st.rerun()

    return selected_etapa
