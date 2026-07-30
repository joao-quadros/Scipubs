import streamlit as st
import os

# Configuração da página Streamlit
st.set_page_config(
    page_title="Estudo de Mercado por IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importação dos Componentes
from components.header import render_header
from components.sidebar import render_sidebar
from components.form_input import render_form_input
from components.report_view import render_dashboard, render_benchmarking, render_export_center
from components.chat_assistant import render_chat_assistant

# Inicialização de Variáveis de Estado da Sessão
if "project_info" not in st.session_state:
    st.session_state["project_info"] = None
if "study_data" not in st.session_state:
    st.session_state["study_data"] = None
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "etapa_index" not in st.session_state:
    st.session_state["etapa_index"] = 0

def main():
    # Renderiza o Cabeçalho Principal
    render_header()

    # Renderiza a Barra Lateral e obtém a Etapa Selecionada
    selected_etapa = render_sidebar()

    # Roteamento de Telas baseada na seleção
    if selected_etapa.startswith("1."):
        render_form_input()
    elif selected_etapa.startswith("2."):
        render_dashboard()
    elif selected_etapa.startswith("3."):
        render_benchmarking()
    elif selected_etapa.startswith("4."):
        render_chat_assistant()
    elif selected_etapa.startswith("5."):
        render_export_center()

if __name__ == "__main__":
    main()
