import streamlit as st
from utils.validators import validate_briefing_form
from services.gemini_client import GeminiMarketClient

def render_form_input():
    """Renderiza o formulário da Etapa 1: Briefing & Ingestão de Dados."""
    st.markdown("### 📝 Etapa 1: Briefing & Ingestão de Dados do Projeto")
    st.write("Preencha as informações do seu produto, serviço ou ideia para que o assistente por IA analise o mercado.")

    with st.form("form_briefing", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_projeto = st.text_input(
                "Nome do Projeto / Produto / Serviço *",
                placeholder="Ex: EduTech Master, SciPubs, BioHealth App..."
            )
            segmento = st.text_input(
                "Segmento / Nicho de Mercado *",
                placeholder="Ex: SaaS B2B, EdTech, Biotecnologia, Mercado Editorial..."
            )
            
        with col2:
            publico_alvo = st.text_input(
                "Público-Alvo Pretendido *",
                placeholder="Ex: Pesquisadores acadêmicos, PMEs, Estudantes Universitários..."
            )
            abrangencia = st.selectbox(
                "Abrangência Geográfica",
                ["Brasil (Nacional)", "América Latina", "Global (Internacional)", "Regional / Local"]
            )

        descricao = st.text_area(
            "Descrição Completa do Produto/Serviço ou Problema a Resolver *",
            placeholder="Descreva detalhadamente o que é a solução, a proposta de valor principal, a dor que resolve e o modelo de receita pretendido...",
            height=130
        )

        col3, col4 = st.columns(2)
        with col3:
            objetivo_estudo = st.selectbox(
                "Objetivo Principal da Análise",
                [
                    "Análise de Viabilidade & Matriz SWOT completa",
                    "Benchmarking & Mapeamento de Concorrentes",
                    "Identificação de Tendências & Oportunidades",
                    "Precificação & Posicionamento Estratégico"
                ]
            )
        with col4:
            urls = st.text_input(
                "URLs / Links de Concorrentes (Opcional)",
                placeholder="https://concorrente1.com, https://concorrente2.com"
            )

        submitted = st.form_submit_button("🚀 Gerar Estudo de Mercado por IA", use_container_width=True, type="primary")

    if submitted:
        api_key = st.session_state.get("gemini_api_key")
        if not api_key:
            st.error("⚠️ Por favor, informe sua Chave API do Gemini na barra lateral antes de prosseguir.")
            return

        is_valid, errors = validate_briefing_form(nome_projeto, segmento, descricao)
        if not is_valid:
            for err in errors:
                st.error(f"❌ {err}")
            return

        # Guarda os dados do projeto na sessão
        project_info = {
            "nome_projeto": nome_projeto,
            "segmento": segmento,
            "publico_alvo": publico_alvo,
            "abrangencia": abrangencia,
            "descricao": descricao,
            "objetivo_estudo": objetivo_estudo,
            "urls": urls
        }
        st.session_state["project_info"] = project_info

        # Executa a análise via Gemini Client
        with st.spinner("🧠 Processando análise de inteligência de mercado via Gemini 2.5..."):
            try:
                client = GeminiMarketClient(api_key=api_key)
                study_data = client.run_market_study(project_info)
                st.session_state["study_data"] = study_data
                st.session_state["etapa_index"] = 1  # Avança para Etapa 2
                st.success("🎉 Estudo de Mercado gerado com sucesso! Redirecionando para o Painel Executivo...")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Falha ao processar estudo de mercado: {e}")
