import streamlit as st

def render_header():
    """Renderiza o cabeçalho estilizado da aplicação."""
    st.markdown("""
    <style>
    .main-hero {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.4);
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #c7d2fe;
        max-width: 800px;
        line-height: 1.5;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #e0e7ff;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    </style>
    
    <div class="main-hero">
        <div class="hero-badge">✨ Powered by Gemini 2.5 AI & Open Data</div>
        <div class="hero-title">Estudo de Mercado & Inteligência Estratégica por IA</div>
        <div class="hero-subtitle">
            Transforme ideias e dados dispersos em análises competitivas completas, matriz SWOT, mapas de posicionamento e relatórios executivos acionáveis.
        </div>
    </div>
    """, unsafe_allow_html=True)
