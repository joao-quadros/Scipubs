def generate_markdown_report(study_data: dict, project_info: dict) -> str:
    """Gera um relatório completo formatado em Markdown profissional."""
    if not study_data:
        return "# Relatório de Estudo de Mercado\n\nNenhum dado de análise disponível."
        
    resumo = study_data.get("resumo_executivo", "Sem resumo disponível.")
    score = study_data.get("score_oportunidade", "N/A")
    concorrencia = study_data.get("nivel_concorrencia", "N/A")
    tam_mercado = study_data.get("tamanho_mercado_estimado", "N/A")
    
    swot = study_data.get("matriz_swot", {})
    concorrentes = study_data.get("concorrentes", [])
    rec = study_data.get("recomendacoes_estrategicas", [])
    riscos = study_data.get("principais_riscos", [])

    md = f"""# 📊 Relatório Estratégico de Estudo de Mercado
**Projeto:** {project_info.get('nome_projeto', 'N/A')}  
**Segmento:** {project_info.get('segmento', 'N/A')}  
**Abrangência:** {project_info.get('abrangencia', 'Brasil')}  
**Objetivo:** {project_info.get('objetivo_estudo', 'Análise de Viabilidade')}  

---

## 📌 1. Resumo Executivo
{resumo}

### 📈 Indicadores Chave de Mercado
- **Índice de Oportunidade:** {score} / 100
- **Nível de Concorrência:** {concorrencia}
- **Tamanho Estimado do Mercado:** {tam_mercado}

---

## 🧭 2. Matriz SWOT / FOFA

### 🟢 Forças (Strengths)
"""
    for f in swot.get("forcas", []):
        md += f"- {f}\n"

    md += "\n### 🚀 Oportunidades (Opportunities)\n"
    for o in swot.get("oportunidades", []):
        md += f"- {o}\n"

    md += "\n### 🔴 Fraquezas (Weaknesses)\n"
    for fr in swot.get("fraquezas", []):
        md += f"- {fr}\n"

    md += "\n### ⚠️ Ameaças (Threats)\n"
    for a in swot.get("ameacas", []):
        md += f"- {a}\n"

    md += "\n---\n\n## ⚔️ 3. Análise Competitiva (Benchmarking)\n\n"
    for c in concorrentes:
        md += f"### 🔹 {c.get('nome', 'Concorrente')}\n"
        md += f"- **Posicionamento:** {c.get('posicionamento')}\n"
        md += f"- **Pontos Fortes:** {c.get('pontos_fortes')}\n"
        md += f"- **Pontos Fracos:** {c.get('pontos_fracos')}\n"
        md += f"- **Diferencial Sugerido:** {c.get('diferencial_proposto')}\n\n"

    md += "---\n\n## 🎯 4. Recomendações Estratégicas\n"
    for r in rec:
        md += f"1. {r}\n"

    md += "\n## ⚠️ 5. Principais Riscos e Mitigações\n"
    for rsk in riscos:
        md += f"- {rsk}\n"

    return md
