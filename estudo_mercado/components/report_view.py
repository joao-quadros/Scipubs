import streamlit as st
import pandas as pd
from utils.export import export_to_excel, export_to_json
from services.report_generator import generate_markdown_report

def render_dashboard():
    """Renderiza a Etapa 2: Painel Executivo & Matriz SWOT."""
    study_data = st.session_state.get("study_data")
    project_info = st.session_state.get("project_info")

    if not study_data or not project_info:
        st.warning("⚠️ Nenhuma análise disponível. Preencha o briefing na Etapa 1 para gerar o estudo.")
        return

    st.markdown(f"### 📊 Painel Executivo: {project_info.get('nome_projeto')}")
    st.caption(f"Segmento: {project_info.get('segmento')} | Abrangência: {project_info.get('abrangencia')}")

    # Cards de Métricas Principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Índice de Oportunidade",
            value=f"{study_data.get('score_oportunidade', 80)} / 100",
            delta="Alta Atratividade"
        )
    with col2:
        st.metric(
            label="Nível de Concorrência",
            value=study_data.get("nivel_concorrencia", "Médio")
        )
    with col3:
        st.metric(
            label="Tamanho Est. de Mercado",
            value=study_data.get("tamanho_mercado_estimado", "R$ 1,0 Bi+")
        )

    st.markdown("---")

    # Resumo Executivo
    st.markdown("#### 📌 Resumo Executivo da IA")
    st.info(study_data.get("resumo_executivo", "Sem resumo."))

    st.markdown("---")

    # Matriz SWOT / FOFA
    st.markdown("#### 🧭 Matriz SWOT / FOFA Interativa")
    swot = study_data.get("matriz_swot", {})

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🟢 Forças (Strengths)")
        for item in swot.get("forcas", []):
            st.success(f"• {item}")

        st.markdown("##### 🚀 Oportunidades (Opportunities)")
        for item in swot.get("oportunidades", []):
            st.info(f"• {item}")

    with c2:
        st.markdown("##### 🔴 Fraquezas (Weaknesses)")
        for item in swot.get("fraquezas", []):
            st.warning(f"• {item}")

        st.markdown("##### ⚠️ Ameaças (Threats)")
        for item in swot.get("ameacas", []):
            st.error(f"• {item}")

def render_benchmarking():
    """Renderiza a Etapa 3: Análise Competitiva & Benchmarking."""
    study_data = st.session_state.get("study_data")
    if not study_data:
        st.warning("⚠️ Nenhuma análise disponível. Execute a Etapa 1.")
        return

    st.markdown("### ⚔️ Análise Competitiva & Benchmarking")
    concorrentes = study_data.get("concorrentes", [])

    if not concorrentes:
        st.info("Nenhum concorrente mapeado.")
        return

    # Tabela Comparativa
    df_comp = pd.DataFrame(concorrentes)
    st.dataframe(df_comp, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔍 Detalhamento dos Competidores")

    for c in concorrentes:
        with st.expander(f"🔹 {c.get('nome')} — {c.get('posicionamento')}"):
            st.markdown(f"**Pontos Fortes:** {c.get('pontos_fortes')}")
            st.markdown(f"**Pontos Fracos:** {c.get('pontos_fracos')}")
            st.markdown(f"**Diferencial Sugerido:** {c.get('diferencial_proposto')}")

def render_export_center():
    """Renderiza a Etapa 5: Central de Relatórios & Exportação."""
    study_data = st.session_state.get("study_data")
    project_info = st.session_state.get("project_info")

    if not study_data or not project_info:
        st.warning("⚠️ Nenhuma análise disponível. Execute a Etapa 1.")
        return

    st.markdown("### 📥 Central de Relatórios & Exportação")
    st.write("Baixe a análise completa em diferentes formatos para apresentações e relatórios de diretoria.")

    md_report = generate_markdown_report(study_data, project_info)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="📄 Baixar Relatório (Markdown)",
            data=md_report,
            file_name=f"Estudo_Mercado_{project_info.get('nome_projeto')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col2:
        excel_data = export_to_excel(study_data.get("concorrentes", []), study_data.get("matriz_swot", {}), project_info)
        st.download_button(
            label="📊 Baixar Tabelas (Excel)",
            data=excel_data,
            file_name=f"Estudo_Mercado_{project_info.get('nome_projeto')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col3:
        json_data = export_to_json(study_data)
        st.download_button(
            label="⚙️ Baixar Dados Brutos (JSON)",
            data=json_data,
            file_name=f"Estudo_Mercado_{project_info.get('nome_projeto')}.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("#### 📄 Pré-visualização do Relatório")
    st.markdown(md_report)
