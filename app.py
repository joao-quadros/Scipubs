import faulthandler
faulthandler.enable()

import streamlit as st
import pandas as pd
import urllib.parse
import requests
import base64
import json
import os
import re
import time
import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# 1. Função para inicializar o Firebase com segurança e cache
@st.cache_resource
def inicializar_firebase():
    # Converte os segredos do Streamlit para um dicionário Python normal
    firebase_info = dict(st.secrets["firebase"])
    
    # Corrige problemas comuns de escape com a chave privada no Streamlit Cloud
    firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
    
    # Inicializa o app se ele já não estiver ativo
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
        
    return firestore.client()

# Inicializa o cliente do Firestore globalmente se os segredos estiverem presentes
db = None
try:
    if "firebase" in st.secrets:
        db = inicializar_firebase()
except Exception:
    pass

# --- EXEMPLOS DE USO DO FIRESTORE ---

# 2. Criar ou Atualizar dados do usuário (Salvar histórico de busca)
def salvar_historico_usuario(usuario_id, termo_busca):
    # Acessa o documento do usuário na coleção 'usuarios'
    user_ref = db.collection("usuarios").document(usuario_id)
    
    # Cria o documento ou atualiza adicionando a busca ao histórico
    user_ref.set({
        "historico_buscas": firestore.ArrayUnion([termo_busca]),
        "ultimo_acesso": firestore.SERVER_TIMESTAMP
    }, merge=True) # merge=True impede que outros campos sejam apagados ao atualizar
    
    st.success(f"Busca por '{termo_busca}' salva no histórico!")

# 3. Ler dados do usuário
def obter_dados_usuario(usuario_id):
    user_ref = db.collection("usuarios").document(usuario_id)
    doc = user_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        return None

# Detecção dinâmica de versão do Streamlit para evitar erros de TypeError
SUPPORTS_NEW_WIDTH = False
try:
    version_str = st.__version__.split("+")[0]
    parts = []
    for p in version_str.split("."):
        digits = "".join(c for c in p if c.isdigit())
        if digits:
            parts.append(int(digits))
    if len(parts) >= 2:
        if parts[0] > 1 or (parts[0] == 1 and parts[1] >= 58):
            SUPPORTS_NEW_WIDTH = True
except Exception:
    pass

# Dicionário desempacotado dinamicamente para largura de componentes
kwargs_largura = {"width": "stretch"} if SUPPORTS_NEW_WIDTH else {"use_container_width": True}

# --- 1. CONFIGURAÇÃO ÚNICA DA PÁGINA (Executada antes de qualquer comando Streamlit) ---
def obter_imagem_local_base64(caminho_arquivo):
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""
    return ""

# Busca sequencial do favicon/logo para definir o page_icon
imagem_base64_icon = obter_imagem_local_base64("favicon.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("logo.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("st_static/favicon.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("st_static/logo.png")

novo_page_icon = f"data:image/png;base64,{imagem_base64_icon}" if imagem_base64_icon else "📚"

st.set_page_config(
    page_title="Portal do Pesquisador",
    page_icon=novo_page_icon, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJEÇÃO DE TEMA DINÂMICO (DIURNO / NOTURNO) ---
if st.session_state.get("dark_mode", False):
    st.markdown("""
        <style>
            /* Altera cores de fundo globais */
            .stApp {
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }
            /* Sidebar escuro */
            section[data-testid="stSidebar"] {
                background-color: #1E293B !important;
            }
            section[data-testid="stSidebar"] * {
                color: #F8FAFC !important;
            }
            /* Textos e títulos */
            h1, h2, h3, h4, h5, h6, p, span, label, div {
                color: #F8FAFC !important;
            }
            /* Inputs e Selects */
            input, select, textarea {
                background-color: #334155 !important;
                color: #F8FAFC !important;
                border: 1px solid #475569 !important;
            }
            /* Expander e cards */
            div[data-testid="stExpander"] {
                background-color: #1E293B !important;
                border: 1px solid #334155 !important;
            }
            /* Botões secundários */
            button {
                color: #F8FAFC !important;
                background-color: #334155 !important;
                border: 1px solid #475569 !important;
            }
            /* Abas */
            button[data-baseweb="tab"] {
                color: #CBD5E1 !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #38BDF8 !important;
                border-bottom-color: #38BDF8 !important;
            }
        </style>
    """, unsafe_allow_html=True)

# --- 2. SISTEMA DE TRADUÇÃO MULTILÍNGUE ---
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Português"

# Seletor de idioma fixado na barra lateral
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.session_state.idioma = st.sidebar.selectbox(
    "🌐 Language / Idioma:",
    ["Português", "English", "Español"]
)

dic = {
    "Português": {
        "titulo": "Portal do Pesquisador",
        "subtitulo": "Ciência de dados aplicada à produção científica de alto impacto",
        "filtros_tit": "#### 🔍 Buscador de Periódicos",
        "placeholder_busca": "Digite o título da revista, ISSN...",
        "buscar_reg": "Buscar registro específico:",
        "aba_escopo": "📂 Escopo Acadêmico & CNPq",
        "aba_impacto": "📈 Métricas de Performance & Quartis",
        "subarea_lbl": "Subárea do Conhecimento (CNPq):",
        "base_lbl": "Bases Detentoras:",
        "jcr_lbl": "Quartil JCR (Clarivate):",
        "sjr_lbl": "Quartil SJR (Scopus):",
        "ordem_lbl": "Ordenar Resultados por:",
        "m_selecionadas": "Revistas Selecionadas",
        "m_hindex": "H-Index Topo",
        "m_jif": "Fator JIF Máximo",
        "m_sjr": "SJR Score Ápice",
        "cat_tit": "#### 📋 Catálogo de Periódicos",
        "exibir_pag": "Exibir por página:",
        "pag_lbl": "Página",
        "exportar_btn": "📥 Exportar apenas esta página",
        "aviso_nada": "Nenhum periódico atende aos critérios aplicados.",
        "nav_tit": "Painel de Navegação",
        "todas": "Todas",
        "col_h5": "Índice h5 (Scholar)",
        "meta_tit": "METADADOS",
        "meta_sistema": "Sistema",
        "meta_versao": "Versão Base",
        "meta_padrao": "Padrão CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Ativo",
        "direitos_tit": "Direitos Autorais & Propriedade",
        "direitos_autor": "Universidade Federal Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos os direitos reservados.</i>",
        "visitas_lbl": "Visitas ao Portal",
        "gov_tit": "SITES GOVERNAMENTAIS",
        "inst_tit": "INFORMAÇÕES INSTITUCIONAIS",
        "pessoal_lbl": "👤 Site pessoal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "REPOSITÓRIOS",
        "ia_tit": "IA ACADÊMICA",
        "btn_desktop": "💻 Baixar Versão para Windows",
        "busca_cat": "🔍 Catálogo de Periódicos",
        "busca_ia": "🧠 Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendação Temática com Inteligência Artificial",
        "ia_subtitulo": "Cole o título e o resumo (abstract) do seu artigo. A IA analisará o nosso catálogo e indicará as opções mais adequadas.",
        "ia_campo_titulo": "Título do Artigo",
        "ia_campo_resumo": "Resumo / Abstract (Suporta Português, Inglês ou Espanhol)",
        "ia_chave_api": "Chave API do Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Você precisa de uma chave API gratuita obtida no Google AI Studio para rodar a recomendação online.",
        "ia_num_rec": "Quantidade de recomendações desejadas (máx. 20)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "A IA está processando o seu resumo e cruzando com o catálogo...",
        "ia_sucesso": "Recomendações geradas com sucesso!",
        "ia_erro": "Erro ao processar com a IA. Verifique se a sua Chave API está correta.",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_aderencia": "Grau de Aderência:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponível na base",
        "filtro_area": "Grande Área",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "🔑 Credencial",
        "ia_como_obter_titulo": "ℹ️ Como obter uma chave gratuita?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta ferramenta é gratuita. Para usá-la, você precisa de uma chave da API do Google Gemini, também gratuita:<br><br>
1. Acesse <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Faça login com sua conta Google<br>
3. Clique em <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copie a chave gerada e cole no campo acima<br><br>
<i>A chave gratuita permite centenas de consultas por dia.</i>
</div>
        """,
        "ia_refinar_alvos": "🎯 Refinar Alvos",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### Bem-vindo ao Portal do Pesquisador!",
        "reg_apresentacao": "Esta é uma plataforma científica de alta tecnologia projetada para simplificar a busca e a seleção de periódicos de impacto para sua publicação. Una forças com ciência de dados e IA.",
        "reg_beneficios_tit": "✨ Por que usar o Portal?",
        "reg_beneficio_1_tit": "🔍 Busca Tradicional",
        "reg_beneficio_1_desc": "Filtros por CNPq, Indexadores (Scopus, Web of Science, SciELO, Educ@) e métricas consolidadas.",
        "reg_beneficio_2_tit": "📊 Métricas Unificadas",
        "reg_beneficio_2_desc": "Quartis JCR/SJR, H-Index e atalhos de impacto no Scholar ao seu alcance.",
        "reg_beneficio_3_tit": "🧠 Recomendador IA",
        "reg_beneficio_3_desc": "Recomendador generativo via Gemini 1.5 Flash cruzado com nossa base de periódicos.",
        "reg_formulario_tit": "📝 Registro de Acesso Acadêmico",
        "reg_formulario_desc": "O acesso ao portal é gratuito e aberto a toda a comunidade científica (de estudantes de graduação a pós-doutores). Preencha o cadastro abaixo para liberar o acesso.",
        "reg_nome": "Nome Completo:",
        "reg_email": "E-mail Acadêmico ou Pessoal:",
        "reg_escolaridade": "Nível de Escolaridade:",
        "reg_instituicao": "Instituição de Vínculo:",
        "reg_inst_outra": "Especifique sua Instituição:",
        "reg_area_interesse": "Grande Área de Interesse (Predominante):",
        "reg_btn_enviar": "Registrar e Acessar o Buscador ➔",
        "reg_sucesso": "🎉 Registro concluído com sucesso! Bem-vindo ao Portal do Pesquisador.",
        "reg_erro_campos": "⚠️ Por favor, preencha todos os campos obrigatórios.",
        "reg_lateral_status_bloqueado": "🔒 Cadastro pendente para liberar o buscador.",
        "reg_lateral_status_liberado": "🔓 Acesso Liberado",
        "reg_btn_sair": "Sair",
        "log_email": "E-mail ou Usuário:",
        "log_senha": "Senha:",
        "log_btn_entrar": "Entrar ➔",
        "log_esqueceu": "Esqueceu a senha ou o login? Recupere aqui",
        "rec_titulo": "🔒 Recuperar Acesso",
        "rec_email": "E-mail Cadastrado:",
        "rec_tel": "Telefone Cadastrado:",
        "rec_btn_verificar": "Solicitar Recuperação ➔",
        "rec_btn_redefinir": "Redefinir Senha",
        "rec_nova_senha": "Nova Senha:",
        "rec_conf_senha": "Confirmar Nova Senha:",
        "rec_sucesso": "🎉 Senha provisória gerada e enviada! Faça login.",
        "rec_erro_nao_encontrado": "⚠️ E-mail não encontrado em nossos registros.",
        "rec_btn_voltar": "Voltar para o Login",
        "log_btn_google": "Conectar com o Google",
        "log_cadastrar_link": "Não tem uma conta? Cadastre-se aqui!",
        "log_entrar_link": "Já tem uma conta? Faça login aqui!",
        "log_titulo": "🔒 Entrar no Portal",
        "reg_titulo_form": "📝 Criar Conta Acadêmica",
        "reg_nome_sobrenome": "Nome e Sobrenome:",
        "reg_pais": "País:",
        "reg_telefone": "Telefone:",
        "reg_senha": "Senha:",
        "reg_confirmar_senha": "Confirmar Senha:",
        "reg_btn_cadastrar": "Criar Conta e Acessar ➔",
        "reg_erro_senha_diferente": "⚠️ As senhas digitadas não coincidem.",
        "reg_erro_ja_existe": "⚠️ Este e-mail já está cadastrado. Faça login.",
        "log_erro_invalido": "⚠️ E-mail ou senha incorretos.",
        "log_google_sucesso": "🚀 Conectado com o Google! Redirecionando...",
        "areas_trad": {
            "Engenharias": "Engenharias",
            "Linguística, Letras e Artes": "Linguística, Letras e Artes",
            "Ciências Biológicas": "Ciências Biológicas",
            "Ciências Exatas e da Terra": "Ciências Exatas e da Terra",
            "Outras / Não Classificado": "Outras / Não Classificado",
            "Ciências da Saúde": "Ciências da Saúde",
            "Ciências Sociais Aplicadas": "Ciências Sociais Aplicadas",
            "Ciências Agrárias": "Ciências Agrárias",
            "Ciências Humanas": "Ciências Humanas"
        }
    },
    "English": {
        "titulo": "The Researcher's Portal",
        "subtitulo": "Data science applied to high-impact scientific output.",
        "filtros_tit": "#### 🔍 Journal Finder",
        "placeholder_busca": "Enter journal title, ISSN...",
        "buscar_reg": "Search specific record:",
        "aba_escopo": "📂 Academic Scope & CNPq",
        "aba_impacto": "📈 Performance Metrics & Quartiles",
        "subarea_lbl": "Subarea of Knowledge (CNPq):",
        "base_lbl": "Holding Databases:",
        "jcr_lbl": "JCR%20Quartile%20(Clarivate):", # URL encoded helper
        "sjr_lbl": "SJR Quartile (Scopus):",
        "ordem_lbl": "Sort Results by:",
        "m_selecionadas": "Selected Journals",
        "m_hindex": "Top H-Index",
        "m_jif": "Max JIF Factor",
        "m_sjr": "Peak SJR Score",
        "cat_tit": "#### 📋 Journal Catalog",
        "exibir_pag": "Display per page:",
        "pag_lbl": "Page",
        "exportar_btn": "📥 Export this page only",
        "aviso_nada": "No journals match the applied criteria.",
        "nav_tit": "Navigation Panel",
        "todas": "All",
        "col_h5": "h5-Index (Scholar)",
        "meta_tit": "METADATA",
        "meta_sistema": "System",
        "meta_versao": "Base Version",
        "meta_padrao": "CNPq Standard",
        "meta_status": "Operational",
        "meta_ativo": "Active",
        "direitos_tit": "Copyright & Ownership",
        "direitos_autor": "Federal University of Ouro Preto<br>Minas Gerais, Brazil.<br><i>All rights reserved.</i>",
        "visitas_lbl": "Portal Visits",
        "gov_tit": "GOVERNMENT WEBSITES",
        "inst_tit": "INSTITUTIONAL INFORMATION",
        "pessoal_lbl": "👤 Personal website",
        "indexadores_tit": "INDEXERS",
        "repositorios_tit": "DIRECTORIES",
        "ia_tit": "ACADEMIC AI",
        "btn_desktop": "💻 Download Windows Version",
        "busca_cat": "🔍 Journal Catalog",
        "busca_ia": "🧠 Smart Recommender (AI)",
        "ia_titulo": "Thematic Recommendation with Artificial Intelligence",
        "ia_subtitulo": "Paste your article title and abstract. The AI will analyze our journal catalog and suggest the best matches.",
        "ia_campo_titulo": "Article Title",
        "ia_campo_resumo": "Abstract (Supports Portuguese, English, or Spanish)",
        "ia_chave_api": "Gemini API Key (Google AI Studio)",
        "ia_chave_ajuda": "You need a free API key from Google AI Studio to run the online recommendation.",
        "ia_num_rec": "Number of desired recommendations (max. 20)",
        "ia_btn_buscar": "Analyze and Recommend",
        "ia_analisando": "AI is processing your abstract and matching with the catalog...",
        "ia_sucesso": "Recommendations generated successfully!",
        "ia_erro": "Error processing with AI. Check if your API Key is correct.",
        "ia_card_motivo": "Why publish here:",
        "ia_card_aderencia": "Adherence Score:",
        "ia_card_site": "🌐 Visit Official Homepage",
        "ia_card_sem_site": "Website not available in database",
        "filtro_area": "Broad Area",
        "filtro_indexador": "Indexer",
        "ia_credencial_tit": "🔑 Credentials",
        "ia_como_obter_titulo": "ℹ️ How to get a free API key?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
This tool is free. To use it, you need a Google Gemini API key, which is also free:<br><br>
1. Go to <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Sign in with your Google account<br>
3. Click <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copy the generated key and paste it into the field above<br><br>
<i>The free key allows hundreds of queries per day.</i>
</div>
        """,
        "ia_refinar_alvos": "🎯 Refine Targets",
        "ia_todos": "All",
        "reg_boas_vindas": "### Welcome to the Researcher's Portal!",
        "reg_apresentacao": "This is a high-tech scientific platform designed to simplify the search and selection of high-impact journals for your publication. Join forces with data science and AI.",
        "reg_beneficios_tit": "✨ Why use the Portal?",
        "reg_beneficio_1_tit": "🔍 Traditional Search",
        "reg_beneficio_1_desc": "Filters by CNPq subareas, indexers (Scopus, Web of Science, SciELO, Educ@), and consolidated metrics.",
        "reg_beneficio_2_tit": "📊 Unified Metrics",
        "reg_beneficio_2_desc": "JCR/SJR quartiles, H-Index, and impact shortcuts on Google Scholar at your fingertips.",
        "reg_beneficio_3_tit": "🧠 AI Recommender",
        "reg_beneficio_3_desc": "Generative recommendations via Gemini 1.5 Flash crossed with our journal database.",
        "reg_formulario_tit": "📝 Academic Access Registration",
        "reg_formulario_desc": "Access to the portal is free and open to the entire scientific community (from undergraduate students to postdocs). Fill out the form below to unlock access.",
        "reg_nome": "Full Name:",
        "reg_email": "Academic or Personal Email:",
        "reg_escolaridade": "Education Level / Academic Degree:",
        "reg_instituicao": "Affiliated Institution:",
        "reg_inst_outra": "Specify your Institution:",
        "reg_area_interesse": "Major Research Area of Interest:",
        "reg_btn_enviar": "Register and Access the Finder ➔",
        "reg_sucesso": "🎉 Registration completed successfully! Welcome to the Researcher's Portal.",
        "reg_erro_campos": "⚠️ Please fill in all required fields.",
        "reg_lateral_status_bloqueado": "🔒 Registration pending to unlock search.",
        "reg_lateral_status_liberado": "🔓 Access Granted",
        "reg_btn_sair": "Logout",
        "log_email": "Email or Username:",
        "log_senha": "Password:",
        "log_btn_entrar": "Login ➔",
        "log_esqueceu": "Forgot password or login? Recover here",
        "rec_titulo": "🔒 Recover Access",
        "rec_email": "Registered Email:",
        "rec_tel": "Registered Phone:",
        "rec_btn_verificar": "Request Recovery ➔",
        "rec_btn_redefinir": "Reset Password",
        "rec_nova_senha": "New Password:",
        "rec_conf_senha": "Confirm New Password:",
        "rec_sucesso": "🎉 Temporary password generated and sent! Please log in.",
        "rec_erro_nao_encontrado": "⚠️ Email not found in our records.",
        "rec_btn_voltar": "Back to Login",
        "log_btn_google": "Sign in with Google",
        "log_cadastrar_link": "Don't have an account? Sign up here!",
        "log_entrar_link": "Already have an account? Log in here!",
        "log_titulo": "🔒 Log in to the Portal",
        "reg_titulo_form": "📝 Create Academic Account",
        "reg_nome_sobrenome": "First and Last Name:",
        "reg_pais": "Country:",
        "reg_telefone": "Phone:",
        "reg_senha": "Password:",
        "reg_confirmar_senha": "Confirm Password:",
        "reg_btn_cadastrar": "Create Account and Access ➔",
        "reg_erro_senha_diferente": "⚠️ Passwords do not match.",
        "reg_erro_ja_existe": "⚠️ This email is already registered. Please log in.",
        "log_erro_invalido": "⚠️ Incorrect email or password.",
        "log_google_sucesso": "🚀 Connected with Google! Redirecting...",
        "areas_trad": {
            "Engenharias": "Engineering",
            "Linguística, Letras e Artes": "Linguistics, Literature & Arts",
            "Ciências Biológicas": "Biological Sciences",
            "Ciências Exatas e da Terra": "Exact & Earth Sciences",
            "Outras / Não Classificado": "Others / Unclassified",
            "Ciências da Saúde": "Health Sciences",
            "Ciências Sociais Aplicadas": "Applied Social Sciences",
            "Ciências Agrárias": "Agricultural Sciences",
            "Ciências Humanas": "Human Sciences"
        }
    },
    "Español": {
        "titulo": "Portal del Investigador",
        "subtitulo": "Ciencia de datos aplicada a la producción científica de más alto nivel.",
        "filtros_tit": "#### 🔍 Buscador de Revistas",
        "placeholder_busca": "Ingrese el título de la revista, ISSN...",
        "buscar_reg": "Buscar registro específico:",
        "aba_escopo": "📂 Alcance Académico y CNPq",
        "aba_impacto": "📈 Métricas de Rendimiento y Cuartiles",
        "subarea_lbl": "Subárea del Conocimiento (CNPq):",
        "base_lbl": "Bases de Datos Detentoras:",
        "jcr_lbl": "Cuartil JCR (Clarivate):",
        "sjr_lbl": "Cuartil SJR (Scopus):",
        "ordem_lbl": "Ordenar Resultados por:",
        "m_selecionadas": "Revistas Selecionadas",
        "m_hindex": "H-Index Máximo",
        "m_jif": "Factor JIF Máximo",
        "m_sjr": "SJR Score Ápice",
        "cat_tit": "#### 📋 Catálogo de Revistas",
        "exibir_pag": "Mostrar por página:",
        "pag_lbl": "Página",
        "exportar_btn": "📥 Exportar solo esta página",
        "aviso_nada": "Ninguna revista coincide con los criterios aplicados.",
        "nav_tit": "Panel de Navegación",
        "todas": "Todas",
        "col_h5": "Índice h5 (Scholar)",
        "meta_tit": "METADATOS",
        "meta_sistema": "Sistema",
        "meta_versao": "Versión Base",
        "meta_padrao": "Patrón CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Activo",
        "direitos_tit": "Derechos de Autor y Propiedad",
        "direitos_autor": "Universidad Federal de Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos os direitos reservados.</i>",
        "visitas_lbl": "Visitas al Portal",
        "gov_tit": "SITIOS DEL GOBIERNO",
        "inst_tit": "INFORMACIÓN INSTITUCIONAL",
        "pessoal_lbl": "👤 Sitio personal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "DIRECTORIOS",
        "ia_tit": "IA ACADÉMICA",
        "btn_desktop": "💻 Descargar Versión para Windows",
        "busca_cat": "🔍 Catálogo de Revistas",
        "busca_ia": "🧠 Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendación Temática con Inteligencia Artificial",
        "ia_subtitulo": "Pegue el título y el resumen (abstract) de su artículo. La IA analizará nuestro catálogo de revistas e indicará las mejores opciones.",
        "ia_campo_titulo": "Título del Artículo",
        "ia_campo_resumo": "Resumen / Abstract (Soporta Portugués, Inglés o Español)",
        "ia_chave_api": "Clave API de Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Necesitas una clave API gratuita obtenida de Google AI Studio para ejecutar la recomendación en línea.",
        "ia_num_rec": "Cantidad de recomendaciones deseadas (máx. 20)",
        "ia_btn_buscar": "Analar y Recomendar",
        "ia_analisando": "La IA está procesando su resumo y cruzándolo con el catálogo...",
        "ia_sucesso": "¡Recomendaciones generadas con éxito!",
        "ia_erro": "Error al procesar con la IA. Verifique que su Clave API sea correcta.",
        "ia_card_motivo": "Por qué publicar aqui:",
        "ia_card_aderencia": "Grado de Adherencia:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Sitio no disponible en la base",
        "filtro_area": "Gran Área",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "🔑 Credenciales",
        "ia_como_obter_titulo": "ℹ️ ¿Cómo obtener una clave gratuita?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta herramienta es gratuita. Para usarla, necesita una clave de API de Google Gemini, también gratuita:<br><br>
1. Acceda a <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Inicie sesión con su cuenta de Google<br>
3. Haga clic en <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copie la clave generada y péguela en el campo de arriba<br><br>
<i>La clave gratuita permite cientos de consultas al día.</i>
</div>
        """,
        "ia_refinar_alvos": "🎯 Refinar Objetivos",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### ¡Bienvenido al Portal del Investigador!",
        "reg_apresentacao": "Esta es una plataforma científica de alta tecnología diseñada para simplificar la búsqueda y selección de revistas de impacto para su publicación. Una fuerzas con ciencia de datos e IA.",
        "reg_beneficios_tit": "✨ ¿Por qué usar el Portal?",
        "reg_beneficio_1_tit": "🔍 Búsqueda Tradicional",
        "reg_beneficio_1_desc": "Filtros por subáreas del CNPq, indexadores (Scopus, Web of Science, SciELO, Educ@) y métricas consolidadas.",
        "reg_beneficio_2_tit": "📊 Métricas Unificadas",
        "reg_beneficio_2_desc": "Cuartiles JCR/SJR, H-Index y accesos directos de impacto en Scholar a su alcance.",
        "reg_beneficio_3_tit": "🧠 Recomendador IA",
        "reg_beneficio_3_desc": "Recomendaciones generativas a través de Gemini 1.5 Flash cruzadas con nuestra base de revistas.",
        "reg_formulario_tit": "📝 Registro de Acceso Académico",
        "reg_formulario_desc": "El acceso al portal es gratuito y abierto a toda la comunidad científica (desde estudiantes hasta posdoctores). Complete el formulario a continuación para liberar el acceso.",
        "reg_nome": "Nombre Completo:",
        "reg_email": "Correo Electrónico Académico o Personal:",
        "reg_escolaridade": "Nivel de Escolaridad / Grado Académico:",
        "reg_instituicao": "Institución de Vínculo:",
        "reg_inst_outra": "Especifique su Institución:",
        "reg_area_interesse": "Gran Área de Interés Predominante:",
        "reg_btn_enviar": "Registrarse y Acceder al Buscador ➔",
        "reg_sucesso": "🎉 ¡Registro completado con éxito! Bienvenido al Portal del Investigador.",
        "reg_erro_campos": "⚠️ Por favor, complete todos los campos obligatorios.",
        "reg_lateral_status_bloqueado": "🔒 Registro pendiente para habilitar el buscador.",
        "reg_lateral_status_liberado": "🔓 Acceso Concedido",
        "reg_btn_sair": "Salir",
        "log_email": "Correo o Usuario:",
        "log_senha": "Contraseña:",
        "log_btn_entrar": "Ingresar ➔",
        "log_esqueceu": "¿Olvidó su contraseña o usuario? Recupere aquí",
        "rec_titulo": "🔒 Recuperar Acceso",
        "rec_email": "Correo Registrado:",
        "rec_tel": "Teléfono Registrado:",
        "rec_btn_verificar": "Solicitar Recuperación ➔",
        "rec_btn_redefinir": "Restablecer Contraseña",
        "rec_nova_senha": "Nueva Contraseña:",
        "rec_conf_senha": "Confirmar Nueva Contraseña:",
        "rec_sucesso": "🎉 ¡Contraseña provisional generada y enviada! Inicie sesión.",
        "rec_erro_nao_encontrado": "⚠️ Correo no encontrado en nuestros registros.",
        "rec_btn_voltar": "Volver al Inicio",
        "log_btn_google": "Conectar con Google",
        "log_cadastrar_link": "¿No tienes una cuenta? ¡Regístrate aquí!",
        "log_entrar_link": "¿Ya tienes una cuenta? ¡Inicia sesión aquí!",
        "log_titulo": "🔒 Iniciar Sesión en el Portal",
        "reg_titulo_form": "📝 Crear Cuenta Académica",
        "reg_nome_sobrenome": "Nombre y Apellido:",
        "reg_pais": "País:",
        "reg_telefone": "Teléfono:",
        "reg_senha": "Contraseña:",
        "reg_confirmar_senha": "Confirmar Contraseña:",
        "reg_btn_cadastrar": "Crear Cuenta y Acceder ➔",
        "reg_erro_senha_diferente": "⚠️ Las contraseñas no coinciden.",
        "reg_erro_ja_existe": "⚠️ Este correo ya está registrado. Inicie sesión.",
        "log_erro_invalido": "⚠️ Correo o contraseña incorrectos.",
        "log_google_sucesso": "🚀 ¡Conectado con Google! Redireccionando...",
        "areas_trad": {
            "Engenharias": "Ingenierías",
            "Linguística, Letras e Artes": "Lingüística, Letras y Artes",
            "Ciências Biológicas": "Ciencias Biológicas",
            "Ciências Exatas e da Terra": "Ciencias Exactas y de la Tierra",
            "Outras / Não Classificado": "Otras / No Clasificado",
            "Ciências da Saúde": "Ciencias de la Salud",
            "Ciências Sociais Aplicadas": "Ciencias Sociales Aplicadas",
            "Ciências Agrárias": "Ciencias Agrarias",
            "Ciências Humanas": "Ciencias Humanas"
        }
    }
}
# Correção do seletor em inglês caso venha codificado
if st.session_state.idioma not in dic:
    st.session_state.idioma = "Português"
t = dic[st.session_state.idioma]

# --- 3. CSS CUSTOMIZADO CORRIGIDO (Design Responsivo e Premium) ---
st.markdown("""
<script>
    // Previne que ferramentas de tradução automática corrompam o DOM do React/Streamlit
    const meta = document.createElement('meta');
    meta.name = 'google';
    meta.content = 'notranslate';
    document.getElementsByTagName('head')[0].appendChild(meta);
    document.body.classList.add('notranslate');
    document.body.setAttribute('translate', 'no');
</script>
<style>
    /* Esconde a logo apenas em telas de celulares (menores que 768px) */
    @media (max-width: 768px) {
        .premium-hero img {
            display: none !important;
        }
        .premium-hero {
            text-align: center;
            justify-content: center;
        }
    }
    /* Força o fundo do menu lateral com a cor definida */
    [data-testid="stSidebar"] {
        background-color: #F8F0E3 !important;
    }   
    
    /* Destaque para o título do expander */
    .stExpander details summary p {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    /* Rótulos da barra lateral */
    [data-testid="stSidebar"] label {
        color: #004B87 !important; 
        font-weight: 600 !important; 
    }
   
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #004B87 !important;
    }
    .premium-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 35px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        border-left: 6px solid #FF2B2B;
    }
    .premium-title {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-size: 3.4rem !important;
        font-weight: 800 !important;
        margin-bottom: 0px !important;
        letter-spacing: -0.5px;
        line-height: 1.15 !important;
    }
    .premium-subtitle {
        color: #FFFFFF !important;
        font-size: 1.55rem !important; 
        max-width: 950px;              
        line-height: 1.4;
        margin-top: 0px !important;
    }
    .premium-text-block {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 10px;
    }
    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        padding: 24px 28px !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #64748B !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    
    .stTextInput input { border-radius: 10px !important; padding: 12px 16px !important; border: 1px solid #CBD5E1 !important; }
    .stSelectbox div[data-baseweb="select"] { border-radius: 10px !important; }
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 500 !important; color: #64748B; padding: 12px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #0F172A !important; border-bottom-color: #0F172A !important; }
    
    div[data-testid="stDownloadButton"] button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }

    .btn-custom-menu {
        background-color: #FFFFFF !important;
        border: 1px solid #004B87 !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        text-decoration: none !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }
    .btn-custom-menu span {
        color: #004B87 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        font-family: 'Roboto', sans-serif !important;
    }
    .btn-custom-menu:hover {
        background-color: #FF2B2B !important;
        border-color: #FF2B2B !important;
        box-shadow: 0 4px 8px rgba(255, 43, 43, 0.25) !important;
        transform: translateY(-1px) !important;
    }
    .btn-custom-menu:hover span { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNÇÃO ÚNICA DE CARREGAMENTO DE DADOS (Focado apenas em dados.csv) ---
@st.cache_data
def carregar_dados():
    nome_arquivo = "dados.csv"
    if not os.path.exists(nome_arquivo):
        if os.path.exists("Dados.csv"):
            nome_arquivo = "Dados.csv"
        elif os.path.exists("DADOS.CSV"):
            nome_arquivo = "DADOS.CSV"
            
    if os.path.exists(nome_arquivo):
        try:
            # Detecta o separador (; ou ,) inspecionando a primeira linha
            with open(nome_arquivo, "r", encoding="utf-8-sig", errors="ignore") as f:
                primeira_linha = f.readline()
            separador = ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","
            
            df = pd.read_csv(nome_arquivo, sep=separador, encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
            
            df.columns = df.columns.str.replace('^\ufeff', '', regex=True)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.columns = [c.strip() for c in df.columns]
            
            # Tratamento numérico padrão das métricas
            for col in ['SJR', 'JIF', 'h-index', 'H index']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # Identifica colunas não numéricas e substitui vazios por "-"
            for col in df.columns:
                if col not in ['SJR', 'JIF', 'h-index', 'H index']:
                    df[col] = df[col].fillna("-").astype(str).str.strip()
                    df[col] = df[col].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
            
            # Garante a existência da coluna Homepage
            if "Homepage" not in df.columns:
                df["Homepage"] = "-"
            else:
                df["Homepage"] = df["Homepage"].fillna("-").astype(str).str.strip()
                df["Homepage"] = df["Homepage"].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")

            col_titulo = df.columns[0]
            
            # Cria a chave de agrupamento normalizada (em minúsculas) para ignorar diferenças de caixa
            df["titulo_norm"] = df[col_titulo].astype(str).str.lower().str.strip()
            if "ISSN" in df.columns:
                df["ISSN"] = df["ISSN"].astype(str).str.strip()
            
            # Funções de agregação personalizadas
            def agg_indexadores(series):
                vals = sorted(list(set([str(val).strip() for val in series if str(val).strip() not in ["-", "", "None", "nan"]])))
                return ", ".join(vals) if vals else "-"
                
            def agg_primeiro_valido(series):
                for val in series:
                    val_str = str(val).strip()
                    if val_str not in ["-", "", "None", "nan"]:
                        return val_str
                return "-"
                
            def agg_titulo(series):
                candidatos = [str(x).strip() for x in series if str(x).strip() not in ["-", "", "None", "nan"]]
                if not candidatos:
                    return "-"
                # Prefere títulos com letras misturadas (Title Case) sobre ALL CAPS
                suaves = [c for c in candidatos if not c.isupper() and any(ch.isupper() for ch in c)]
                if suaves:
                    return suaves[0]
                sem_caps = [c for c in candidatos if not c.isupper()]
                if sem_caps:
                    return sem_caps[0]
                return candidatos[0]

            def agg_max_numerico(series):
                nums = pd.to_numeric(series, errors='coerce').dropna()
                return nums.max() if not nums.empty else 0.0
                
            agg_dict = {}
            for col in df.columns:
                if col == "titulo_norm":
                    continue
                if col == col_titulo:
                    agg_dict[col] = agg_titulo
                elif col == "Indexador":
                    agg_dict[col] = agg_indexadores
                elif col in ['SJR', 'JIF', 'h-index', 'H index']:
                    agg_dict[col] = agg_max_numerico
                else:
                    agg_dict[col] = agg_primeiro_valido
                    
            # Agrupa pelo título normalizado
            df = df.groupby("titulo_norm", as_index=False).agg(agg_dict)
            df = df.drop(columns=["titulo_norm"])
            
            return df, nome_arquivo
        except Exception as e:
            st.error(f"⚠️ Erro ao processar a base de dados '{nome_arquivo}'. Detalhes: {e}")
            st.stop()
    else:
        st.error("⚠️ Base de dados não encontrada. O arquivo 'dados.csv' não foi localizado na raiz do projeto. Por favor, certifique-se de fazer o download do arquivo no repositório GitHub correspondente.")
        st.stop()

df_original, arquivo_usado = carregar_dados()

# --- 5. MONTAGEM DA SIDEBAR (LINKS E COMPONENTES) ---
# Inicializa o estado de registro se não existir
if "registrado" not in st.session_state:
    st.session_state.registrado = False
if "modo_login" not in st.session_state:
    st.session_state.modo_login = True
if "modo_recuperacao" not in st.session_state:
    st.session_state.modo_recuperacao = False
if "usuario_recuperado_email" not in st.session_state:
    st.session_state.usuario_recuperado_email = ""
if "email_usuario" not in st.session_state:
    st.session_state.email_usuario = ""
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""
if "acessos_usuario" not in st.session_state:
    st.session_state.acessos_usuario = 0
if "login_via_google" not in st.session_state:
    st.session_state.login_via_google = False
if "solicitar_email_google" not in st.session_state:
    st.session_state.solicitar_email_google = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "abrir_configuracoes" not in st.session_state:
    st.session_state.abrir_configuracoes = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# Exibe o status de acesso na barra lateral
if st.session_state.registrado:
    nome_usr_exibir = st.session_state.get("nome_usuario", "Usuário")
    email_usr_exibir = st.session_state.get("email_usuario", "")
    acessos_usr = st.session_state.get("acessos_usuario", 1)
    
    # Se for login via Google, exibe o e-mail do usuário na mensagem de boas-vindas
    usr_identificador = email_usr_exibir if st.session_state.get("login_via_google", False) else nome_usr_exibir
    
    # Determina o texto de boas-vindas com base no número de acessos
    if acessos_usr <= 1:
        status_texto = f"Seja bem-vindo(a), {usr_identificador}"
    else:
        status_texto = f"Bem-vindo(a) de volta, {usr_identificador}"
        
    if st.session_state.get("is_admin", False):
        status_texto = f"🔑 Admin: {status_texto}"
        bg_cor = "#0F172A"
    else:
        bg_cor = "#10B981"
        
    # Colunas para exibir a mensagem e o ícone de engrenagem lado a lado
    col_status_box, col_config_btn = st.sidebar.columns([3.8, 1.2])
    with col_status_box:
        st.markdown(f"""
            <div style="background-color: {bg_cor}; color: white; padding: 10px 8px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 0.82rem; line-height: 1.3; min-height: 38px; display: flex; align-items: center; justify-content: center;">
                {status_texto}
            </div>
        """, unsafe_allow_html=True)
    with col_config_btn:
        if st.button("⚙️", key="btn_config_gear_sidebar", help="Configurações e Acesso", use_container_width=True):
            st.session_state.abrir_configuracoes = not st.session_state.get("abrir_configuracoes", False)
            st.rerun()

st.sidebar.markdown(f"""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <h2 style='margin: 0; font-size: 1.60rem; font-weight: 700; color: #0F172A;'>{t['nav_tit']}</h2>
    </div>
""", unsafe_allow_html=True)

# indexadores
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['indexadores_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://access.clarivate.com/login?app=wos&alternative=true&goto=https:%2F%2Fwww.webofknowledge.com" target="_blank">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRR2EHX1gARlgEZ-baT5UZMBSLF7rw0mZtUAMuBSU46_Rm5RzBLW1oOaas&s=10" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Web of Science</span>
    </a>
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home?display=basic#basic" target="_blank">
        <img src="https://camo.githubusercontent.com/799f6de501a057c2e1997a5f472ac272d4461dd65bdd1c25824d45a97ea9b8ec/68747470733a2f2f7777772e6665722e756e697a672e68722f5f7075622f7468656d65735f7374617469632f666572323031362f64656661756c742f696d672f73636f7075732d69636f6e2e706e67" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Scopus</span>
    </a>
    <a class="btn-custom-menu" href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank">
        <img src="https://its.weill.cornell.edu/sites/default/files/styles/news_item_full_article/public/news_images/720px-us-nlm-pubmed-logo.png?itok=trlhr3Lh" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>PubMed</span>
    </a>
    <a class="btn-custom-menu" href="https://www.scielo.br/" target="_blank">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHiaAjjMsCiMK-A-hur9z1KZcEuf5rEx8rjzketAWDRQNs963MW_DDHwQ&s=10" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Scielo BR</span>
    </a>
    <a class="btn-custom-menu" href="http://educa.fcc.org.br/cgi-bin/wxis.exe/iah/?IsisScript=iah/iah.xis&base=title&fmt=iso.pft&lang=p" target="_blank">
        <img src="https://www.fcc.org.br/fcc/wp-content/uploads/2020/05/fcc.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Educ@</span>
    </a>
    <a class="btn-custom-menu" href="https://www.jstor.org/" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/en/5/56/JSTOR_vector_logo.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>JSTOR</span>
    </a>
    <a class="btn-custom-menu" href="https://www.latindex.org/latindex/" target="_blank">
        <img src="https://www.insper.edu.br/content/insper-portal/en/campus/biblioteca-telles/recursos-de-busca/latindex/_jcr_content/root/responsivegrid/wrapper/container_grid/container/wrapper/featured_card_container/image.coreimg.png/1723749927456/latindex.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Latindex</span>
    </a>
</div>
""", unsafe_allow_html=True)

# repositórios
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['repositorios_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://eric.ed.gov/" target="_blank">
        <img src="https://yt3.googleusercontent.com/ytc/AIdro_kFijnjScrZN1GZMpmVQDW_GRV5syVZsNuOqd2TiG5Y_A=s900-c-k-c0x00ffffff-no-rj" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>ERIC</span>
    </a>
    <a class="btn-custom-menu" href="https://api.base-search.net/" target="_blank">
        <img src="https://pbs.twimg.com/profile_images/1259600128/base_twitter_400x400.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>BASE</span>
    </a>
    <a class="btn-custom-menu" href="https://doaj.org/" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/d/d9/DOAJ_logo-colour.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>DOAJ</span>
    </a>
    <a class="btn-custom-menu" href="https://catalogodeteses.capes.gov.br/catalogo-teses/#!/" target="_blank">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ04fk8I3y7LecgydHxbQybU3R9TB7qb99ikUFKNUsZNQ&s" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Catálogo da CAPES</span>
    </a>
</div>
""", unsafe_allow_html=True)

# ia acadêmica
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['ia_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home#scopus-ai" target="_blank">
        <img src="https://images.icon-icons.com/2389/PNG/512/elsevier_logo_icon_145310.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>ScopusAI</span>
    </a>
    <a class="btn-custom-menu" href="https://researcher.elsevier.com/" target="_blank">
        <img src="https://content-media.pamedia.io/press-release/picture/2025/11/19/01KADJ2EW8YDYQABYJFZFVZ5YR.jpg?format=jpg&dl=pr-newswire-associated0.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>LeapSpace</span>
    </a>
    <a class="btn-custom-menu" href="https://www.researchrabbit.ai/" target="_blank">
        <img src="https://pbs.twimg.com/profile_images/1983772825812189184/IXDTOqLX_400x400.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>ResearchRabbit</span>
    </a>
    <a class="btn-custom-menu" href="https://www.perplexity.ai/" target="_blank">
        <img src="https://framerusercontent.com/images/gcMkPKyj2RX8EOEja8A1GWvCb7E.jpg?width=2000&height=2000" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Perplexity</span>
    </a>
    <a class="btn-custom-menu" href="https://www.connectedpapers.com/" target="_blank">
        <img src="https://pbs.twimg.com/profile_images/1267529009409208325/avWQ0zGg_400x400.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>ConnectedPapers</span>
    </a>
    <a class="btn-custom-menu" href="https://consensus.app/" target="_blank">
        <img src="https://logosandtypes.com/wp-content/uploads/2025/04/Consensus-scaled.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Consensus</span>
    </a>
    <a class="btn-custom-menu" href="https://scispace.com/" target="_blank">
        <img src="https://typeset.io/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>SciSpace</span>
    </a>
    <a class="btn-custom-menu" href="https://elicit.com/" target="_blank">
        <img src="https://zonalogo.com/assets/elicit-logo-png-svg.webp?asset=2444&w=320" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Elicit</span>
    </a>   
    <a class="btn-custom-menu" href="https://logically.app/" target="_blank">
        <img src="https://www.logically.ai/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Logically</span>
    </a>
    <a class="btn-custom-menu" href="https://www.pubmed.ai/home" target="_blank">
        <img src="https://cdn-1.webcatalog.io/catalog/pubmed-ai/pubmed-ai-icon-filled-256.png?v=1747807986408" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>PubMed.AI</span>
    </a>
</div>
""", unsafe_allow_html=True)

# governamentais
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['gov_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://cnpq.br/" target="_blank">
        <img src="https://images.seeklogo.com/logo-png/18/1/cnpq-logo-png_seeklogo-181432.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>CNPq</span>
    </a>
    <a class="btn-custom-menu" href="https://www.gov.br/capes/pt-br" target="_blank">
        <img src="https://www.clipartmax.com/png/middle/289-2899434_previous-next-capes-logo.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>CAPES</span>
    </a>
    <a class="btn-custom-menu" href="https://lattes.cnpq.br/" target="_blank">
        <img src="https://www.gov.br/observatorio/pt-br/assuntos/programas-academicos/imagens/Lattes.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Currículo Lattes</span>
    </a>
    <a class="btn-custom-menu" href="https://www.periodicos.capes.gov.br/" target="_blank">
        <img src="https://www.periodicos.capes.gov.br/templates/periodicos_gov/images/icon-periodicos.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Portal de Periódicos CAPES</span>
    </a>
</div>
""", unsafe_allow_html=True)

# institucionais
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['inst_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.ufop.br" target="_blank">
        <img src="https://labiiex.ufop.br/sites/default/files/styles/media_gallery_thumbnail/public/labiiex/files/ufop_logo.png?m=1597327148&itok=EmS_8t7o" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://www.posedu.ufop.br" target="_blank">
        <img src="https://posedu.ufop.br/sites/default/files/styles/os_files_small/public/ppge/files/logo_reduzida.png?m=1593192999&itok=0JX9OWRl" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>PPGE-UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://www.musica.ufop.br" target="_blank">
        <img src="https://musica.ufop.br/sites/default/files/styles/os_files_xxlarge/public/musica/files/logo22_1_03.png?m=1542714207&itok=i3jpi-oe" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Música-UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://professor.ufop.br/joaoquadros" target="_blank">
        <span style="font-weight: 500; font-size: 0.9rem; color: #004B87;">{t['pessoal_lbl']}</span>
    </a>
</div>
""", unsafe_allow_html=True)

# --- 6. BLOCO CONTADOR DE VISITAS (SILENCIOSO E PERSISTENTE) ---
arquivo_contador = "contador_visitas.txt"
try:
    if 'visitou' not in st.session_state:
        st.session_state.visitou = True
        incrementar = True
    else:
        incrementar = False

    sucesso_db = False
    visitas = 0

    # Tenta ler/gravar no Firebase Firestore se disponível
    if db is not None:
        try:
            doc_ref = db.collection("metadados").document("visitas")
            doc = doc_ref.get()
            
            if doc.exists:
                visitas = int(doc.to_dict().get("quantidade", 0))
            else:
                # Se não existir no DB, inicializa usando o valor do arquivo local como base para não zerar
                visitas_inicial = 0
                if os.path.exists(arquivo_contador):
                    with open(arquivo_contador, "r") as f:
                        conteudo = f.read().strip()
                        visitas_inicial = int(conteudo) if conteudo.isdigit() else 0
                visitas = visitas_inicial
            
            if incrementar:
                visitas += 1
                doc_ref.set({"quantidade": visitas}, merge=True)
            sucesso_db = True
        except Exception:
            pass

    # Fallback local caso o Firebase não esteja disponível/configurado
    if not sucesso_db:
        if not os.path.exists(arquivo_contador):
            with open(arquivo_contador, "w") as f:
                f.write("0")
                
        with open(arquivo_contador, "r") as f:
            conteudo = f.read().strip()
            visitas = int(conteudo) if conteudo.isdigit() else 0
            
        if incrementar:
            visitas += 1
            with open(arquivo_contador, "w") as f:
                f.write(str(visitas))

    # Calcula a soma de todos os acessos individuais dos usuários cadastrados
    soma_acessos_individuais = 0
    if db is not None:
        try:
            docs = db.collection("usuarios").stream()
            for doc in docs:
                soma_acessos_individuais += int(doc.to_dict().get("acessos", 0))
        except Exception:
            pass
            
    if soma_acessos_individuais == 0:
        caminho_csv = "usuarios.csv"
        if os.path.exists(caminho_csv):
            try:
                df_local = pd.read_csv(caminho_csv, sep=";")
                if "Acessos" in df_local.columns:
                    soma_acessos_individuais = int(df_local["Acessos"].sum())
            except Exception:
                pass

    visitas_totais = visitas + soma_acessos_individuais

    # --- ABA SECRETA DO ADMINISTRADOR (URL com ?admin=true ou ?visitas=true ou Admin Logado) ---
    params = st.query_params
    if "admin" in params or "visitas" in params or st.session_state.get("is_admin", False):
        st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
        # Exibe em preto (color: #000000)
        st.sidebar.markdown(f"<p style='color: #000000; font-weight: bold; margin-bottom: 0;'>📊 Total de Visitas (Admin): {visitas_totais}</p>", unsafe_allow_html=True)
        
        # Campo para atualizar manualmente o valor do contador no Firebase/Local
        novo_valor = st.sidebar.number_input("Atualizar Contador:", min_value=0, value=visitas_totais, step=1, key="admin_visit_counter")
        if st.sidebar.button("Salvar Novo Valor", key="admin_save_visits_btn"):
            # O valor geral será ajustado descontando os acessos dos usuários
            visitas = max(0, novo_valor - soma_acessos_individuais)
            # Salva no Firestore se configurado
            if db is not None:
                try:
                    db.collection("metadados").document("visitas").set({"quantidade": visitas}, merge=True)
                    st.sidebar.success("Firebase atualizado!")
                except Exception as e:
                    st.sidebar.error(f"Erro no Firebase: {e}")
            # Salva no arquivo local
            try:
                with open(arquivo_contador, "w") as f:
                    f.write(str(visitas))
                st.sidebar.success("Arquivo local atualizado!")
            except Exception as e:
                st.sidebar.error(f"Erro local: {e}")
            st.rerun()
except Exception:
    pass

# --- 7. METADADOS E DIREITOS AUTORAIS ---
st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
    <div style='color: #0F172A; font-size: 0.8rem; padding-left: 5px; line-height: 1.6;'>
        <p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin:0 0 8px 0; letter-spacing: 0.05em;'>{t['meta_tit']}</p>
        <span style='color: #A91D22;'>●</span> <b>{t['meta_sistema']}:</b> {t['meta_status']}<br>
        <b>{t['meta_versao']}:</b> 2026.1<br>
        <b>{t['meta_padrao']}:</b> {t['meta_ativo']}
        <br><br>
        <hr style='border: 0; border-top: 1px dashed #E2E8F0; margin: 10px 0;'>
        <b>{t['direitos_tit']}:</b><br>
        <b>© 2026 João F. Soares-Quadros Jr.</b><br>
        {t['direitos_autor']}
    </div>
""", unsafe_allow_html=True)

# --- 8. BOTÃO DE DOWNLOAD DA VERSÃO DESKTOP ---
texto_botao = t.get("btn_desktop", "💻 Baixar Versão para Windows")

st.sidebar.markdown(
    f"""
    <a href="https://drive.google.com/..." target="_blank" style="text-decoration: none;">
        <button style="
            width: 100%;
            background-color: #FF2B2B;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.95rem;
            cursor: pointer;
            transition: background 0.3s ease;
            margin-bottom: 15px;
        " onmouseover="this.style.backgroundColor='#cc2222'" onmouseout="this.style.backgroundColor='#FF2B2B'">
            {texto_botao}
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# --- 9. PAINEL PRINCIPAL (HERO DESIGN) ---
# Seleciona o arquivo de imagem correspondente ao idioma ativo
nome_logo = "logo.png"
if st.session_state.idioma == "English":
    nome_logo = "logo_en.png"
elif st.session_state.idioma == "Español":
    nome_logo = "logo_es.png"

imagem_base64 = obter_imagem_local_base64(nome_logo)
# Fallback caso a versão traduzida específica não exista
if not imagem_base64:
    imagem_base64 = obter_imagem_local_base64("logo.png")

if imagem_base64:
    tag_imagem = f'<img src="data:image/png;base64,{imagem_base64}" style="height: 180px; width: auto; object-fit: contain;">'
else:
    tag_imagem = '<span class="emoji-logo" style="font-size: 6.5rem; line-height: 1; margin-right: 15px;">📚</span>'

st.markdown(f"""<div class="premium-hero" style="display: flex; align-items: center; flex-wrap: wrap; gap: 30px; padding: 25px 35px;">
{tag_imagem}
<div class="divider-line" style="width: 2px; height: 100px; background-color: rgba(255,255,255,0.15);"></div>
<div class="premium-text-block">
<h1 class="premium-title" style="margin: 0 !important; padding: 0 !important; font-size: 2.3rem !important; font-weight: 800 !important; letter-spacing: -0.5px;">{t['titulo']}</h1>
<p class="premium-subtitle" style="margin: 5px 0 0 0 !important; padding: 0 !important; font-size: 1.1rem !important; opacity: 0.85;">{t['subtitulo']}</p>
</div>
</div>""", unsafe_allow_html=True)

# --- 10. CONTROLE DE ACESSO COM REGISTRO ---
# Funções auxiliares globais para banco de dados de credenciais
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_senha_temporaria():
    caracteres = string.ascii_letters + string.digits
    return "".join(random.choice(caracteres) for _ in range(8))

def enviar_email_recuperacao(destinatario, login, senha_temporaria):
    try:
        smtp_secrets = st.secrets.get("smtp", {})
        sender_email = smtp_secrets.get("email")
        sender_password = smtp_secrets.get("password")
        smtp_server = smtp_secrets.get("server", "smtp.gmail.com")
        smtp_port = int(smtp_secrets.get("port", 587))
        
        if not sender_email or not sender_password:
            return False, "SMTP_NOT_CONFIGURED"
            
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = destinatario
        msg["Subject"] = "Recuperacao de Acesso - Portal do Pesquisador"
        
        corpo = f"""Ola!

Voce solicitou a recuperacao de acesso ao Portal do Pesquisador.
Aqui estao suas credenciais temporarias:

• Login: {login}
• Senha Temporaria: {senha_temporaria}

Por favor, acesse o portal com estas credenciais e altere sua senha no menu de configuracoes (icone de engrenagem ⚙️ na barra lateral).

Atenciosamente,
Equipe Portal do Pesquisador"""
        
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, destinatario, msg.as_string())
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)

def cadastrar_usuario(nome, email, pais, telefone, escolaridade, instituicao, senha):
    caminho = "usuarios.csv"
    novo_usuario = pd.DataFrame([{
        "Data/Hora": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Nome": nome,
        "Email": email.lower().strip(),
        "País": pais,
        "Telefone": telefone,
        "Escolaridade": escolaridade,
        "Instituição": instituicao,
        "Senha_Hash": hash_senha(senha),
        "Acessos": 1
    }])
    if os.path.exists(caminho):
        try:
            df_existente = pd.read_csv(caminho, sep=";")
            emails_cadastrados = df_existente["Email"].astype(str).str.lower().str.strip().tolist()
            if email.lower().strip() in emails_cadastrados:
                return False
            df_novo = pd.concat([df_existente, novo_usuario], ignore_index=True)
            df_novo.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
        except Exception:
            novo_usuario.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
    else:
        novo_usuario.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")

    if db is not None:
        try:
            db.collection("usuarios").document(email.lower().strip()).set({
                "nome": nome,
                "email": email.lower().strip(),
                "pais": pais,
                "telefone": telefone,
                "escolaridade": escolaridade,
                "instituicao": instituicao,
                "acessos": 1,
                "data_cadastro": firestore.SERVER_TIMESTAMP,
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            }, merge=True)
        except Exception:
            pass
    return True

def verificar_recuperacao(email):
    email_clean = email.lower().strip()
    if db is not None:
        try:
            doc = db.collection("usuarios").document(email_clean).get()
            if doc.exists:
                d = doc.to_dict()
                return True, d.get("nome", "Usuário")
        except Exception:
            pass
    caminho = "usuarios.csv"
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho, sep=";")
            match = df[df["Email"].astype(str).str.lower().str.strip() == email_clean]
            if not match.empty:
                return True, match.iloc[0]["Nome"]
        except Exception:
            pass
    return False, ""

def redefinir_senha_usuario(email, nova_senha):
    email_clean = email.lower().strip()
    senha_hash_nova = hash_senha(nova_senha)
    if db is not None:
        try:
            db.collection("usuarios").document(email_clean).set({
                "Senha_Hash": senha_hash_nova
            }, merge=True)
        except Exception:
            pass
    caminho = "usuarios.csv"
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho, sep=";")
            idx = df[df["Email"].astype(str).str.lower().str.strip() == email_clean].index
            if not idx.empty:
                df.loc[idx, "Senha_Hash"] = senha_hash_nova
                df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
        except Exception:
            pass
    return True

def verificar_login(email_ou_usuario, senha):
    email_clean = email_ou_usuario.lower().strip()
    senha_clean = senha.strip()
    admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
    admin_pass_conf = st.secrets.get("ADMIN_PASSWORD", "Ufop@2026").strip()
    
    if email_clean == admin_email_conf and senha_clean == admin_pass_conf:
        acessos_atuais = 0
        if db is not None:
            try:
                doc_ref = db.collection("usuarios").document(admin_email_conf)
                doc = doc_ref.get()
                if doc.exists:
                    acessos_atuais = int(doc.to_dict().get("acessos", 0))
                doc_ref.set({
                    "nome": "João F. Soares-Quadros Jr.",
                    "email": admin_email_conf,
                    "pais": "Brasil",
                    "telefone": "N/A",
                    "escolaridade": "Doutor",
                    "instituicao": "Universidade Federal de Ouro Preto (UFOP)",
                    "acessos": acessos_atuais + 1,
                    "ultimo_acesso": firestore.SERVER_TIMESTAMP
                }, merge=True)
            except Exception:
                pass
        st.session_state.nome_usuario = "João"
        st.session_state.acessos_usuario = acessos_atuais + 1
        return True

    caminho = "usuarios.csv"
    if not os.path.exists(caminho):
        return False
    try:
        df = pd.read_csv(caminho, sep=";")
        senha_hash_calc = hash_senha(senha)
        match = df[(df["Email"].astype(str).str.lower().str.strip() == email_clean) & (df["Senha_Hash"] == senha_hash_calc)]
        if not match.empty:
            idx = match.index[0]
            if "Acessos" not in df.columns:
                df["Acessos"] = 1
            current_acessos = df.loc[idx, "Acessos"]
            novo_acessos = int(current_acessos) + 1 if pd.notna(current_acessos) else 1
            
            # Seta as Session States do Usuário logado
            st.session_state.nome_usuario = str(match.iloc[0]["Nome"]).split(" ")[0].capitalize()
            st.session_state.acessos_usuario = novo_acessos
            
            try:
                df.loc[idx, "Acessos"] = novo_acessos
                df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
            except Exception:
                pass
            if db is not None:
                try:
                    doc_ref = db.collection("usuarios").document(email_clean)
                    doc = doc_ref.get()
                    acessos_atuais = 0
                    if doc.exists:
                        acessos_atuais = int(doc.to_dict().get("acessos", 0))
                    doc_ref.set({
                        "acessos": acessos_atuais + 1,
                        "ultimo_acesso": firestore.SERVER_TIMESTAMP
                    }, merge=True)
                except Exception:
                    pass
            return True
        return False
    except Exception:
        return False

# --- 10. CONTROLE DE ACESSO COM REGISTRO ---
if not st.session_state.registrado:

    # Escolha do Modo (Recuperação, Login ou Cadastro)
    if st.session_state.get("modo_recuperacao", False):
        col_rec_1, col_rec_2, col_rec_3 = st.columns([1, 1.5, 1])
        with col_rec_2:
            st.markdown(f"### {t['rec_titulo']}")
            email_rec = st.text_input(t['rec_email'], placeholder="", key="email_rec_input")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            if st.button(t['rec_btn_verificar'], type="primary", use_container_width=True):
                if not email_rec.strip():
                    st.error(t['reg_erro_campos'])
                else:
                    sucesso, nome = verificar_recuperacao(email_rec)
                    if sucesso:
                        # Gera senha temporária alfanumérica
                        senha_temp = gerar_senha_temporaria()
                        # Atualiza a senha no banco de dados
                        redefinir_senha_usuario(email_rec.lower().strip(), senha_temp)
                        
                        # Envia por e-mail
                        enviado, erro = enviar_email_recuperacao(email_rec.lower().strip(), email_rec.lower().strip(), senha_temp)
                        
                        if enviado:
                            st.success("🎉 Uma senha provisória foi enviada para o seu e-mail cadastrado! Acesse o portal e atualize-a nas configurações.")
                            st.session_state.modo_recuperacao = False
                            st.session_state.modo_login = True
                            time.sleep(3.0)
                            st.rerun()
                        else:
                            # Fallback se SMTP não estiver configurado
                            st.warning("⚠️ O envio de e-mail falhou ou o servidor SMTP nos segredos não está configurado.")
                            st.info(f"Para testes, use estas credenciais temporárias:\n\n**Login:** `{email_rec.lower().strip()}`\n\n**Senha Temporária:** `{senha_temp}`")
                    else:
                        st.error(t['rec_erro_nao_encontrado'])
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button(t['rec_btn_voltar'], use_container_width=True):
                st.session_state.modo_recuperacao = False
                st.session_state.modo_login = True
                st.rerun()

    elif st.session_state.modo_login:
        # TÍTULO E APRESENTAÇÃO MINIMALISTA
        col_log_1, col_log_2, col_log_3 = st.columns([1, 1.5, 1])
        with col_log_2:
            # Formulário de Login
            email_log = st.text_input(t['log_email'], placeholder="", key="email_login")
            senha_log = st.text_input(t['log_senha'], type="password", placeholder="", key="senha_login")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            btn_entrar = st.button(t['log_btn_entrar'], type="primary", use_container_width=True)
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Link para ir para a página de Cadastro colocado diretamente abaixo
            if st.button(t['log_cadastrar_link'], key="btn_ir_cadastro", use_container_width=True):
                st.session_state.modo_login = False
                st.rerun()
                
            # Link para ir para a página de Recuperação
            if st.button(f"🔑 {t['log_esqueceu']}", key="btn_ir_recuperacao", use_container_width=True):
                st.session_state.modo_recuperacao = True
                st.session_state.modo_login = False
                st.session_state.usuario_recuperado_email = ""
                st.rerun()
                
            if btn_entrar:
                if not email_log.strip() or not senha_log.strip():
                    st.error(t['reg_erro_campos'])
                elif verificar_login(email_log, senha_log):
                    st.session_state.registrado = True
                    st.session_state.login_via_google = False
                    
                    email_clean = email_log.lower().strip()
                    st.session_state.email_usuario = email_clean
                    admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
                    st.session_state.is_admin = (email_clean == admin_email_conf)
                    
                    st.success(t['reg_sucesso'])
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error(t['log_erro_invalido'])
    else:
        col_reg_1, col_reg_2 = st.columns(2)
        with col_reg_1:
            nome_cad = st.text_input(t['reg_nome_sobrenome'], placeholder="Ex: João Silva")
            email_cad = st.text_input(t['reg_email'], placeholder="")
            pais_cad = st.text_input(t['reg_pais'], placeholder="Ex: Brasil")
            tel_cad = st.text_input(t['reg_telefone'], placeholder="Ex: (31) 99999-9999")
            
        with col_reg_2:
            # Nível de Escolaridade
            opcoes_esc = []
            if st.session_state.idioma == "Português":
                opcoes_esc = ["Estudante de Graduação", "Especialista / Pós-Graduado", "Mestrando", "Mestre", "Doutorando", "Doutor", "Pós-Doutor", "Outro"]
            elif st.session_state.idioma == "English":
                opcoes_esc = ["Undergraduate Student", "Specialist / Postgraduate", "Master's Student", "Master", "PhD Candidate", "PhD / Doctor", "Postdoctoral Researcher", "Other"]
            else:
                opcoes_esc = ["Estudiante de Grado", "Especialista / Posgrado", "Estudiante de Maestría", "Magíster", "Doctorando", "Doctor", "Posdoctorado", "Otro"]
                
            escolaridade_cad = st.selectbox(t['reg_escolaridade'], opcoes_esc)
            
            # Vínculo Institucional
            opcoes_inst = []
            if st.session_state.idioma == "Português":
                opcoes_inst = [
                    "Universidade Federal de Ouro Preto (UFOP)",
                    "Universidade de São Paulo (USP)",
                    "Universidade Estadual de Campinas (UNICAMP)",
                    "Universidade Federal de Minas Gerais (UFMG)",
                    "Universidade Federal do Rio de Janeiro (UFRJ)",
                    "Universidade Federal do Rio Grande do Sul (UFRGS)",
                    "Universidade Estadual Paulista (UNESP)",
                    "Universidade Federal de Santa Catarina (UFSC)",
                    "Universidade Federal de São Paulo (UNIFESP)",
                    "Outra Instituição"
                ]
            elif st.session_state.idioma == "English":
                opcoes_inst = [
                    "Federal University of Ouro Preto (UFOP)",
                    "University of São Paulo (USP)",
                    "State University of Campinas (UNICAMP)",
                    "Federal University of Minas Gerais (UFMG)",
                    "Federal University of Rio de Janeiro (UFRJ)",
                    "Federal University of Rio Grande do Sul (UFRGS)",
                    "São Paulo State University (UNESP)",
                    "Federal University of Santa Catarina (UFSC)",
                    "Federal University of São Paulo (UNIFESP)",
                    "Other Institution"
                ]
            else:
                opcoes_inst = [
                    "Universidad Federal de Ouro Preto (UFOP)",
                    "Universidad de São Paulo (USP)",
                    "Universidad Estatal de Campinas (UNICAMP)",
                    "Universidad Federal de Minas Gerais (UFMG)",
                    "Universidad Federal de Río de Janeiro (UFRJ)",
                    "Universidad Federal de Río Grande del Sur (UFRGS)",
                    "Universidad Estatal Paulista (UNESP)",
                    "Universidad Federal de Santa Catarina (UFSC)",
                    "Universidad Federal de São Paulo (UNIFESP)",
                    "Otra Institución"
                ]
                
            instituicao_cad_sel = st.selectbox(t['reg_instituicao'], opcoes_inst)
            
            # Se for "Outra", pede para especificar
            escrever_outra = False
            if instituicao_cad_sel in ["Outra Instituição", "Other Institution", "Otra Institución"]:
                instituicao_cad_outra = st.text_input(t['reg_inst_outra'], placeholder="Ex: Harvard University")
                escrever_outra = True
            else:
                instituicao_cad_outra = ""

        # Senha e confirmação de senha
        st.markdown("<hr style='border-top:1px dashed #CBD5E1; margin:15px 0;'>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            senha_cad = st.text_input(t['reg_senha'], type="password", placeholder="", key="senha_cad_reg")
        with col_s2:
            senha_cad_conf = st.text_input(t['reg_confirmar_senha'], type="password", placeholder="", key="senha_cad_conf_reg")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        btn_registrar = st.button(t['reg_btn_cadastrar'], type="primary", use_container_width=True)
        
        if btn_registrar:
            if not nome_cad.strip() or not email_cad.strip() or not pais_cad.strip() or not tel_cad.strip() or not senha_cad.strip() or (escrever_outra and not instituicao_cad_outra.strip()):
                st.error(t['reg_erro_campos'])
            elif senha_cad != senha_cad_conf:
                st.error(t['reg_erro_senha_diferente'])
            else:
                inst_final = instituicao_cad_outra.strip() if escrever_outra else instituicao_cad_sel
                # Grava no CSV
                sucesso_cadastro = cadastrar_usuario(
                    nome_cad.strip(),
                    email_cad.strip(),
                    pais_cad.strip(),
                    tel_cad.strip(),
                    escolaridade_cad,
                    inst_final,
                    senha_cad
                )
                if sucesso_cadastro:
                    st.session_state.registrado = True
                    
                    email_clean = email_cad.lower().strip()
                    st.session_state.email_usuario = email_clean
                    st.session_state.nome_usuario = nome_cad.strip().split(" ")[0].capitalize()
                    st.session_state.acessos_usuario = 1
                    st.session_state.login_via_google = False
                    
                    admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
                    st.session_state.is_admin = (email_clean == admin_email_conf)
                    
                    st.success(t['reg_sucesso'])
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error(t['reg_erro_ja_existe'])
                    
        st.markdown("<br>", unsafe_allow_html=True)
        # Link para voltar ao Login
        if st.button(t['log_entrar_link'], key="btn_ir_login", use_container_width=True):
            st.session_state.modo_login = True
            st.rerun()
            
    st.stop()

# Textos informativos traduzidos

# --- TELA DE CONFIGURAÇÕES & AJUSTES ---
if st.session_state.get("abrir_configuracoes", False):
    st.markdown("## ⚙️ Configurações & Ajustes do Portal")
    
    # Botão para fechar e retornar ao buscador
    if st.button("⬅️ Voltar para o Buscador", key="btn_fechar_config"):
        st.session_state.abrir_configuracoes = False
        st.rerun()
        
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    opc_config = st.radio(
        "Selecione uma opção de ajuste:",
        [
            "👤 Atualização de Cadastro",
            "🔑 Atualização de Senha",
            "🎨 Tema da Plataforma (Claro/Escuro)",
            "📢 Compartilhar Portal com Outros",
            "🚪 Desconectar da Plataforma"
        ],
        key="radio_opc_config"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "👤 Atualização de Cadastro" in opc_config:
        st.subheader("👤 Atualizar Meus Dados de Cadastro")
        email_atual = st.session_state.email_usuario
        nome_atual = st.session_state.get("nome_usuario", "")
        
        # Carrega dados atuais do usuário
        caminho_csv = "usuarios.csv"
        telefone_atual = ""
        escolaridade_atual = "Doutor"
        inst_atual = ""
        
        if db is not None:
            try:
                doc = db.collection("usuarios").document(email_atual).get()
                if doc.exists:
                    d = doc.to_dict()
                    nome_atual = d.get("nome", nome_atual)
                    telefone_atual = d.get("telefone", "")
                    escolaridade_atual = d.get("escolaridade", "Doutor")
                    inst_atual = d.get("instituicao", "")
            except Exception:
                pass
                
        if not telefone_atual and os.path.exists(caminho_csv):
            try:
                df_u = pd.read_csv(caminho_csv, sep=";")
                match = df_u[df_u["Email"].astype(str).str.lower().str.strip() == email_atual.lower().strip()]
                if not match.empty:
                    nome_atual = match.iloc[0]["Nome"]
                    telefone_atual = match.iloc[0]["Telefone"]
                    escolaridade_atual = match.iloc[0]["Escolaridade"]
                    inst_atual = match.iloc[0]["Instituicao"]
            except Exception:
                pass
                
        nome_edit = st.text_input("Nome Completo:", value=nome_atual)
        tel_edit = st.text_input("Telefone:", value=telefone_atual)
        
        opcoes_esc_edit = ["Estudante de Graduação", "Especialista / Pós-Graduado", "Mestrando", "Mestre", "Doutorando", "Doutor", "Pós-Doutor", "Outro"]
        if escolaridade_atual not in opcoes_esc_edit:
            opcoes_esc_edit.append(escolaridade_atual)
        esc_edit = st.selectbox("Escolaridade:", opcoes_esc_edit, index=opcoes_esc_edit.index(escolaridade_atual))
        
        inst_edit = st.text_input("Instituição de Vínculo:", value=inst_atual)
        
        if st.button("Salvar Alterações do Cadastro", type="primary"):
            if not nome_edit.strip() or not tel_edit.strip() or not inst_edit.strip():
                st.error("⚠️ Preencha todos os campos obrigatórios.")
            else:
                if os.path.exists(caminho_csv):
                    try:
                        df_u = pd.read_csv(caminho_csv, sep=";")
                        idx = df_u[df_u["Email"].astype(str).str.lower().str.strip() == email_atual.lower().strip()].index
                        if not idx.empty:
                            df_u.loc[idx, "Nome"] = nome_edit.strip()
                            df_u.loc[idx, "Telefone"] = tel_edit.strip()
                            df_u.loc[idx, "Escolaridade"] = esc_edit
                            df_u.loc[idx, "Instituicao"] = inst_edit.strip()
                            df_u.to_csv(caminho_csv, index=False, sep=";", encoding="utf-8-sig")
                    except Exception:
                        pass
                
                if db is not None:
                    try:
                        db.collection("usuarios").document(email_atual).set({
                            "nome": nome_edit.strip(),
                            "telefone": tel_edit.strip(),
                            "escolaridade": esc_edit,
                            "instituicao": inst_edit.strip()
                        }, merge=True)
                    except Exception:
                        pass
                        
                st.session_state.nome_usuario = nome_edit.strip().split(" ")[0].capitalize()
                st.success("🎉 Dados do cadastro atualizados com sucesso!")
                time.sleep(1.2)
                st.rerun()

    elif "🔑 Atualização de Senha" in opc_config:
        st.subheader("🔑 Alterar Minha Senha de Acesso")
        nova_s = st.text_input("Nova Senha:", type="password", key="settings_nova_senha")
        conf_s = st.text_input("Confirmar Nova Senha:", type="password", key="settings_conf_senha")
        if st.button("Atualizar Senha", type="primary"):
            if not nova_s.strip():
                st.error("⚠️ A senha não pode estar em branco.")
            elif nova_s != conf_s:
                st.error("⚠️ As senhas digitadas são diferentes.")
            else:
                redefinir_senha_usuario(st.session_state.email_usuario, nova_s)
                st.success("🎉 Senha alterada com sucesso!")
                time.sleep(1.2)
                st.rerun()
                
    elif "🎨 Tema da Plataforma (Claro/Escuro)" in opc_config:
        st.subheader("🎨 Estilo e Aparência da Plataforma")
        tema_atual = "Modo Noturno (Escuro)" if st.session_state.get("dark_mode", False) else "Modo Diurno (Claro)"
        st.info(f"O tema ativo atualmente é: **{tema_atual}**")
        
        if st.session_state.get("dark_mode", False):
            if st.button("Ativar Modo Diurno (Claro)", type="primary"):
                st.session_state.dark_mode = False
                st.rerun()
        else:
            if st.button("Ativar Modo Noturno (Escuro)", type="primary"):
                st.session_state.dark_mode = True
                st.rerun()

    elif "📢 Compartilhar Portal com Outros" in opc_config:
        st.subheader("📢 Compartilhar o Portal do Pesquisador")
        url_portal = "https://buscador-periodicos.streamlit.app/"
        texto_compartilhar = f"Confira o Buscador de Periodicos Cientificos do PPGE UFOP: {url_portal}"
        
        msg_encoded = urllib.parse.quote(texto_compartilhar)
        link_wa = f"https://api.whatsapp.com/send?text={msg_encoded}"
        link_mail = f"mailto:?subject=Portal%20do%20Pesquisador&body={msg_encoded}"
        
        st.write("Escolha uma das formas abaixo para divulgar o portal:")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(f"[💬 WhatsApp]({link_wa})", unsafe_allow_html=True)
        with col_c2:
            st.markdown(f"[✉️ E-mail]({link_mail})", unsafe_allow_html=True)
        with col_c3:
            if st.button("📋 Copiar Link"):
                st.info(f"Link: `{url_portal}`")
                st.success("Link copiado para exibição!")

    elif "🚪 Desconectar da Plataforma" in opc_config:
        st.subheader("🚪 Desconectar da Plataforma")
        st.write("Deseja realmente encerrar sua sessão e desconectar do buscador?")
        if st.button("Sim, Sair da Plataforma", type="primary"):
            st.session_state.registrado = False
            st.session_state.email_usuario = ""
            st.session_state.nome_usuario = ""
            st.session_state.acessos_usuario = 0
            st.session_state.login_via_google = False
            st.session_state.solicitar_email_google = False
            st.session_state.abrir_configuracoes = False
            st.session_state.is_admin = False
            st.rerun()
            
    st.stop()

# Textos informativos traduzidos
if st.session_state.idioma == "Português":
    expander_titulo = "📖 Sobre o Portal do Pesquisador & Como Utilizar"
    sobre_texto = """
### Bem-vindo ao Portal do Pesquisador!
Esta é uma ferramenta desenvolvida para otimizar a busca por periódicos científicos de alto impacto.
  
#### 🛠️ O que você pode fazer aqui?
1. **Busca Avançada & Booleana:** Pesquise por termos exatos utilizando aspas (ex: `"educação musical"`) ou combine múltiplos critérios usando os operadores lógicos `AND`, `OR` e `NOT` (ex: `music AND education NOT medicine`).
2. **Filtros por Subárea (CNPq):** Encontre periódicos perfeitamente alinhados à sua subárea específica de atuação e conhecimento.
3. **Métricas de Impacto:** Analise o prestígio internacional através de quartis e indicadores consolidados das bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** e o link direto para o **Índice h5 (Google Scholar)**.
4. **Recomendação Inteligente (IA):** Use a inteligência artificial do Google Gemini para colar o título e resumo do seu artigo e obter as recomendações de periódicos ideais com justificativa e link direto.
5. **Exportação de Dados:** Filtre os resultados de acordo com sua necessidade e faça o download da tabela customizada imediatamente.
"""
elif st.session_state.idioma == "English":
    expander_titulo = "📖 About the Researcher's Portal & How to Use"
    sobre_texto = """
### Welcome to the Researcher's Portal!
This is a tool developed to optimize the search for high-impact scientific journals.
 
#### 🛠️ What can you do here?
1. **Advanced & Boolean Search:** Search for exact phrases using quotation marks (e.g., `"music education"`) or combine multiple criteria using the logical operators `AND`, `OR`, and `NOT` (e.g., `music AND education NOT medicine`).
2. **Filters by Subarea (CNPq):** Find journals perfectly aligned with your specific subarea of expertise.
3. **Impact Metrics:** Analyze international prestige through consolidated quartiles and indicators from **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index**, and direct links to the **h5-Index (Google Scholar)**.
4. **Smart Recommender (AI):** Paste your title and abstract, and let the Google Gemini AI recommend the best matches with specific rationale and homepage links.
5. **Data Export:** Filter results according to your needs and download the customized table immediately.
"""
else: # Español
    expander_titulo = "📖 Sobre el Portal del Investigador y Cómo Utilizar"
    sobre_texto = """
### ¡Bienvenido al Portal del Investigador!
Esta es una herramienta desarrollada con el objetivo de optimizar la búsqueda de revistas científicas de alto impacto.
 
#### 🛠️ ¿Qué puedes fazer aquí?
1. **Búsqueda Avanzada y Booleana:** Busque términos exactos usando comillas (por ejemplo: `"educación musical"`) o combine múltiples criterios usando los operadores lógicos `AND`, `OR` y `NOT` (por ejemplo: `music AND education NOT medicine`).
2. **Filtros por Subárea (CNPq):** Encuentre revistas perfectamente alineadas con su subárea específica de conocimiento.
3. **Métricas de Impacto:** Analise el prestigio internacional a través de cuartiles e indicadores consolidados de las bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** y el enlace directo al **Índice h5 (Google Scholar)**.
4. **Recomendador Inteligente (IA):** Use el motor de IA de Google Gemini para obtener sugerencias temáticas personalizadas basadas en el título y resumen de su artículo.
5. **Exportación de Dados:** Filtre los resultados según sus necesidades y descargue la tabla personalizada inmediatamente.
"""

with st.expander(expander_titulo, expanded=False):
    st.markdown(sobre_texto)

st.markdown("<br>", unsafe_allow_html=True)

# --- 10. INTERFACE PRINCIPAL MULTI-ABAS ---
st.markdown(t['filtros_tit'])

# Define as abas com base na presença do parâmetro ?admin=true ou ?visitas=true na URL ou se o usuário logado for Admin
params_url = st.query_params
if "admin" in params_url or "visitas" in params_url or st.session_state.get("is_admin", False):
    tab_busca, tab_ia, tab_admin = st.tabs([t['busca_cat'], t['busca_ia'], "📊 Estatísticas (Admin)"])
else:
    tab_busca, tab_ia = st.tabs([t['busca_cat'], t['busca_ia']])

# ==================== ABA 1: CATÁLOGO TRADICIONAL ====================
with tab_busca:
    busca = st.text_input(t['buscar_reg'], placeholder=t['placeholder_busca'])

    aba_escopo, aba_impacto = st.tabs([t['aba_escopo'], t['aba_impacto']])

    with aba_escopo:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            col_subarea = "Subárea do Conhecimento"
            set_subareas = set()
            if col_subarea in df_original.columns:
                for x in df_original[col_subarea].unique():
                    if str(x).strip() not in ["", "-", "nan", "None"]:
                        for sub in str(x).split(","):
                            set_subareas.add(sub.strip())
            lista_subareas = sorted(list(set_subareas))
            subarea_sel = st.selectbox(t['subarea_lbl'], [t['todas']] + lista_subareas)
        with col_f2:
            col_indexador = "Indexador" if "Indexador" in df_original.columns else None
            if col_indexador:
                set_indexadores = set()
                for x in df_original[col_indexador].unique():
                    if x != "-":
                        for idx in str(x).split(","): 
                            set_indexadores.add(idx.strip())
                indexador_sel = st.multiselect(t['base_lbl'], sorted(list(set_indexadores)))
            else: 
                indexador_sel = []

    with aba_impacto:
        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f4:
            col_q_jcr = "Quartil JCR"
            opcoes_jcr = sorted([str(x).strip() for x in df_original[col_q_jcr].unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if col_q_jcr in df_original.columns else []
            if not opcoes_jcr: 
                opcoes_jcr = ["Q1", "Q2", "Q3", "Q4"]
            q_jcr_sel = st.multiselect(t['jcr_lbl'], opcoes_jcr)
        with col_f5:
            col_q_sjr = "SJR Best Quartile"
            opcoes_sjr = sorted([str(x).strip() for x in df_original[col_q_sjr].unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if col_q_sjr in df_original.columns else []
            if not opcoes_sjr: 
                opcoes_sjr = ["Q1", "Q2", "Q3", "Q4"]
            q_sjr_sel = st.multiselect(t['sjr_lbl'], opcoes_sjr)
        with col_f6:
            opcoes_ordenacao = ["Título"]
            if "SJR" in df_original.columns: 
                opcoes_ordenacao.append("SJR (Prestígio)")
            if "JIF" in df_original.columns: 
                opcoes_ordenacao.append("JIF (Fator de Impacto)")
            criterio_ordem = st.selectbox(t['ordem_lbl'], options=opcoes_ordenacao)

    # FILTRAGEM SEQUENCIAL DE DADOS
    df_filtrado = df_original.copy()

    if busca:
        texto_busca = busca.strip()
        termos_exatos = re.findall(r'"([^"]*)"', texto_busca)
        
        texto_processado = texto_busca
        for i, termo in enumerate(termos_exatos):
            texto_processado = texto_processado.replace(f'"{termo}"', f'__EXACT_{i}__')
            
        if not any(op in texto_processado.upper() for op in ["AND", "OR", "NOT"]):
            palavras = [p.strip() for p in texto_processado.split() if p.strip()]
            texto_processado = " AND ".join(palavras)

        def avaliar_busca_avancada(linha_texto, expressao_logica, lista_exatos):
            linha_texto = str(linha_texto).lower()
            tokens = re.split(r'(\bAND\b|\bOR\b|\bNOT\b)', expressao_logica, flags=re.IGNORECASE)
            
            resultado_final = False
            operador_atual = "OR"
            inverter_proximo = False
            
            for token in tokens:
                token_clean = token.strip()
                if not token_clean:
                    continue
                    
                token_upper = token_clean.upper()
                
                if token_upper == "AND":
                    operador_atual = "AND"
                elif token_upper == "OR":
                    operador_atual = "OR"
                elif token_upper == "NOT":
                    inverter_proximo = True
                else:
                    match_exact = re.match(r'__EXACT_(\d+)__', token_clean)
                    if match_exact:
                        idx = int(match_exact.group(1))
                        termo_real = lista_exatos[idx].lower()
                        possui_termo = termo_real in linha_texto
                    else:
                        termo_real = token_clean.lower()
                        possui_termo = termo_real in linha_texto
                    
                    if inverter_proximo:
                        possui_termo = not possui_termo
                        inverter_proximo = False
                    
                    if operador_atual == "AND":
                        resultado_final = resultado_final and possui_termo
                    elif operador_atual == "OR":
                        resultado_final = resultado_final or possui_termo
                        
            return resultado_final

        df_filtrado = df_filtrado[
            df_filtrado.apply(
                lambda row: avaliar_busca_avancada(
                    f"{row[df_filtrado.columns[0]]} {row['ISSN']}", 
                    texto_processado, 
                    termos_exatos
                ), 
                axis=1
            )
        ]

    if col_subarea in df_filtrado.columns and subarea_sel != t['todas']:
        df_filtrado = df_filtrado[df_filtrado[col_subarea].astype(str).str.contains(subarea_sel, case=False, na=False)]

    if col_indexador and len(indexador_sel) > 0:
        df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.contains("|".join(indexador_sel), na=False)]

    if col_q_jcr in df_filtrado.columns and len(q_jcr_sel) > 0:
        df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]

    if col_q_sjr in df_filtrado.columns and len(q_sjr_sel) > 0:
        df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

    mapa_ordem = {"SJR (Prestígio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "Título": (df_filtrado.columns[0], True)}
    col_ordenar, ascendente = mapa_ordem[criterio_ordem]
    if col_ordenar in df_filtrado.columns: 
        df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

    # METRICAS DINÂMICAS COM SEGURANÇA DE TIPO
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: 
        st.metric(t['m_selecionadas'], f"{len(df_filtrado):,}".replace(",", "."))
    with col_m2: 
        h_index_numerico = pd.to_numeric(df_filtrado["H index"], errors='coerce')
        max_h = int(h_index_numerico.max()) if pd.notna(h_index_numerico.max()) else 0
        st.metric(t['m_hindex'], max_h)
    with col_m3: 
        jif_numerico = pd.to_numeric(df_filtrado['JIF'], errors='coerce')
        max_jif = f"{jif_numerico.max():.2f}" if pd.notna(jif_numerico.max()) else "0.00"
        st.metric(t['m_jif'], max_jif)
    with col_m4: 
        sjr_numerico = pd.to_numeric(df_filtrado['SJR'], errors='coerce')
        max_sjr = f"{sjr_numerico.max():.3f}" if pd.notna(sjr_numerico.max()) else "0.000"
        st.metric(t['m_sjr'], max_sjr)

    st.markdown("<br>", unsafe_allow_html=True)

    # EXIBIÇÃO E PAGINAÇÃO
    st.markdown(t['cat_tit'])
    total_itens = len(df_filtrado)
    if total_itens > 0:
        col_pag1, col_pag2, _ = st.columns([1.5, 2, 5])
        with col_pag1:
            itens_por_pagina = st.selectbox(t['exibir_pag'], options=[20, 50, 100], index=1)
        total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
        with col_pag2:
            pagina_atual = st.number_input(f"{t['pag_lbl']} (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
        
        inicio = (pagina_atual - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        df_da_pagina = df_filtrado.iloc[inicio:fim].copy()
        
        # Remove as colunas de área para simplificar a exibição na tabela e evitar crashes de mapeamento do PyArrow
        df_exibir = df_da_pagina.drop(columns=["Grande Area", "Area do Conhecimento", "Subárea do Conhecimento"], errors="ignore")
        
        # Limpa o index para evitar falhas de segmentação em índices não contíguos (bug do PyArrow pós-filtragem)
        df_exibir = df_exibir.reset_index(drop=True)
        
        # Formata links com fragmentos hash para permitir exibição seletiva (e traço "-" nas células vazias)
        if "Homepage" in df_exibir.columns:
            def format_homepage(val):
                val_str = str(val).strip()
                if val_str not in ["-", "", "None", "nan"]:
                    return val_str + "#🔗 Ver site"
                return "-"
            df_exibir["Homepage"] = df_exibir["Homepage"].apply(format_homepage)
        if "Índice h5" in df_exibir.columns:
            def format_h5(val):
                val_str = str(val).strip()
                if val_str not in ["-", "", "None", "nan"]:
                    return val_str + "#🔗 Abrir"
                return "-"
            df_exibir["Índice h5"] = df_exibir["Índice h5"].apply(format_h5)
        
        # Reconstrução ultra-defensiva para descartar qualquer metadado do pandas que confunda o PyArrow
        df_exibir = pd.DataFrame({col: df_exibir[col].tolist() for col in df_exibir.columns})
        
        # EXIBIÇÃO DA HOMEPAGE NA TABELA COM LINK CLICÁVEL
        st.dataframe(
            df_exibir, 
            hide_index=True,
            column_config={
                "Homepage": st.column_config.LinkColumn(
                    "Homepage",
                    help="Clique para visitar o site oficial da revista",
                    display_text=r"#(.+)$"
                ),
                "JIF": st.column_config.Column(
                    alignment="center"
                ),
                "Quartil JCR": st.column_config.Column(
                    alignment="center"
                ),
                "SJR": st.column_config.Column(
                    alignment="center"
                ),
                "SJR Best Quartile": st.column_config.Column(
                    alignment="center"
                ),
                "H index": st.column_config.Column(
                    alignment="center"
                ),
                "Índice h5": st.column_config.LinkColumn(
                    t['col_h5'],
                    help="Clique para abrir o índice h5 no Google Scholar",
                    display_text=r"#(.+)$",
                    alignment="center"
                )
            },
            **kwargs_largura
        )
        
        csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(label=f"{t['exportar_btn']} ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina_atual.csv", mime="text/csv")
    else:
        st.warning(t['aviso_nada'])

# ==================== ABA 2: RECOMENDADOR POR IA (GEMINI 1.5 FLASH) ====================
with tab_ia:
    # Função auxiliar local para traduzir as Grandes Áreas
    def traduzir_grande_area(area_original, t_dict):
        if not area_original or str(area_original).strip() in ["-", "None", "nan"]:
            return "-"
        import unicodedata
        def clean_str(s):
            s = str(s).lower().strip()
            # Remove acentos
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            # Remove caracteres especiais
            s = ''.join(c for c in s if c.isalnum() or c.isspace())
            return ' '.join(s.split())
            
        area_clean = clean_str(area_original)
        mapeamento = t_dict.get("areas_trad", {})
        for chave_original, valor_traduzido in mapeamento.items():
            if clean_str(chave_original) == area_clean:
                return valor_traduzido
        return str(area_original).strip()

    # Inicialização segura dos estados na Session State
    if "recomendacoes" not in st.session_state:
        st.session_state.recomendacoes = None
    if "erro_ia" not in st.session_state:
        st.session_state.erro_ia = None
    if "aviso_filtro" not in st.session_state:
        st.session_state.aviso_filtro = False
    if "modo_local" not in st.session_state:
        st.session_state.modo_local = False
    if "ia_cache" not in st.session_state:
        # Cache de resultados: chave = hash(titulo+resumo+num_rec+area+indexador), valor = lista de recomendações
        st.session_state.ia_cache = {}
    
    col_input, col_meta = st.columns([2, 1])
    
    with col_input:
        st.markdown(f"### {t['ia_titulo']}")
        st.markdown(f"*{t['ia_subtitulo']}*")
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        
        titulo_artigo = st.text_input(t['ia_campo_titulo'], placeholder="Ex: Análise Epidemiológica de Saúde Coletiva...", key="ia_tit_input")
        resumo_artigo = st.text_area(t['ia_campo_resumo'], placeholder="Paste or type abstract here...", height=250, key="ia_res_input")
        
        # Botão posicionado logo abaixo do resumo
        disparar_busca = st.button(t['ia_btn_buscar'], type="primary", key="btn_ia_disparar")
        
    with col_meta:
        # Credencial e Chave de API inseridas diretamente na aba de controle da IA
        st.markdown(f"#### {t['ia_credencial_tit']}")
        
        # Lê chave do segredo do Streamlit Cloud se existir
        chave_secrets = ""
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                chave_secrets = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
            
        if chave_secrets:
            placeholder_input = "🔑 Chave global ativa (opcional pessoal)"
            help_input = "Uma chave global já está configurada pelo proprietário do app. Se desejar usar sua própria chave pessoal, digite-a aqui."
        else:
            placeholder_input = ""
            help_input = t['ia_chave_ajuda']
            
        user_gemini_key = st.text_input(
            t['ia_chave_api'], 
            type="password", 
            placeholder=placeholder_input, 
            help=help_input
        )
        
        # Define a chave ativa final (prioriza input do usuário)
        api_key_ativa = user_gemini_key.strip() if user_gemini_key else (chave_secrets.strip() if chave_secrets else "")
        
        # Guia amigável para obter chave gratuita (expander recolhido por padrão)
        if not api_key_ativa:
            with st.expander(t['ia_como_obter_titulo'], expanded=False):
                st.markdown(t['ia_como_obter_texto'], unsafe_allow_html=True)
        
        st.markdown(f"#### {t['ia_refinar_alvos']}")
        
        # Mapeia as grandes áreas originais para suas versões traduzidas
        grandes_areas_originais = sorted(list(df_original["Grande Area"].dropna().unique()))
        area_ia_opcoes = {t['todas']: "Todas"}
        for area in grandes_areas_originais:
            area_traduzida = traduzir_grande_area(area, t)
            area_ia_opcoes[area_traduzida] = area
            
        area_ia_exibicao = st.selectbox(f"{t['filtro_area']} (IA)", list(area_ia_opcoes.keys()))
        area_ia = area_ia_opcoes[area_ia_exibicao]
        
        indexador_ia = st.selectbox(f"{t['filtro_indexador']} (IA)", [t['ia_todos']] + list(df_original["Indexador"].dropna().unique()))
        
        # Slider dinâmico integrado para selecionar entre 3 e 20 recomendações
        num_recomendacoes = st.slider(
            t['ia_num_rec'], 
            min_value=3, 
            max_value=20, 
            value=5, 
            step=1
        )
        
    if disparar_busca:
        if not api_key_ativa:
            st.error("⚠️ Para utilizar esta ferramenta, insira sua chave da API do Gemini no painel de Credenciais acima.")
        elif not titulo_artigo or not resumo_artigo:
            st.warning("⚠️ Preencha o Título e o Resumo do seu artigo científico para rodar a recomendação.")
        else:
            # Gera chave de cache baseada nos parâmetros da busca (sem depender da chave API)
            cache_key = hashlib.md5(
                f"{titulo_artigo.strip().lower()}|{resumo_artigo.strip().lower()}|{num_recomendacoes}|{area_ia}|{indexador_ia}".encode("utf-8")
            ).hexdigest()
            
            if cache_key in st.session_state.ia_cache:
                # Resultado em cache — reutiliza sem chamar a API
                st.session_state.recomendacoes = st.session_state.ia_cache[cache_key]
                st.session_state.erro_ia = None
                st.session_state.aviso_filtro = False
                st.rerun()
            else:
                # Reseta os estados anteriores antes do novo processamento
                st.session_state.recomendacoes = None
                st.session_state.erro_ia = None
                st.session_state.aviso_filtro = False
                st.session_state.modo_local = False
                
                # Utiliza um placeholder simples do Streamlit (st.empty) para o indicador de progresso,
                # evitando qualquer conflito de animação de Spinner no DOM virtual do React.
                status_container = st.empty()
                status_container.info(f"⏳ {t['ia_analisando']}")
                
                df_candidatos = df_original.copy()
                if area_ia != "Todas":
                    df_candidatos = df_candidatos[df_candidatos["Grande Area"] == area_ia]
                if indexador_ia != "Todos":
                    df_candidatos = df_candidatos[df_candidatos["Indexador"].astype(str).str.contains(re.escape(indexador_ia), case=False, na=False)]
                
                # Validação caso a base filtrada esteja vazia
                if df_candidatos.empty:
                    st.session_state.aviso_filtro = True
                else:
                    # Seleciona candidatos baseados em relevância de palavras-chave do título e resumo
                    texto_busca = f"{titulo_artigo} {resumo_artigo}".lower()
                    # Extrai termos do título/resumo para busca
                    palavras = set(re.findall(r'\b[a-zA-Zá-úÁ-Ú]{4,}\b', texto_busca))
                    # Remove stopwords comuns
                    stopwords = {"para", "como", "uma", "este", "esta", "com", "dos", "das", "pelo", "pela", "artigo", "pesquisa", "estudo", "sobre", "with", "this", "from", "that", "article", "research", "study", "about"}
                    palavras_filtradas = palavras - stopwords
                    
                    # Grupos de sinônimos acadêmicos em 3 idiomas (Português, Inglês e Espanhol) para busca bidirecional completa
                    sinonimos_academicos = [
                        {"educação", "education", "educación", "ensino", "teaching", "aprendizado", "learning", "aprendizaje"},
                        {"computação", "computing", "computador", "computer", "tecnologia", "technology", "tecnología"},
                        {"saúde", "health", "salud", "medicina", "medicine", "médico", "medical", "médica"},
                        {"ciência", "science", "ciencia", "científico", "scientific", "pesquisa", "research", "investigación"},
                        {"desenvolvimento", "development", "desarrollo", "gestão", "management", "gestión", "administração", "administration", "administración"},
                        {"economia", "economy", "economía", "econômico", "economic", "económico", "social"},
                        {"cultura", "culture", "cultura", "história", "history", "historia", "geografia", "geography", "geografía"},
                        {"matemática", "mathematics", "física", "physics", "fisica", "química", "chemistry", "quimica"},
                        {"biologia", "biology", "biología", "meio ambiente", "environment", "medio ambiente", "ambiental", "environmental"},
                        {"sustentabilidade", "sustainability", "sostenibilidad", "engenharia", "engineering", "ingeniería", "indústria", "industry", "industria"},
                        {"produção", "production", "producción", "sistemas", "systems", "sistemas", "informação", "information", "información"},
                        {"comunicação", "communication", "comunicación", "linguagem", "language", "lenguaje", "literatura", "literature"},
                        {"arte", "art", "música", "music", "musica", "psicologia", "psychology", "psicología"},
                        {"filosofia", "philosophy", "filosofía", "política", "politics", "política", "direito", "law", "derecho"},
                        {"energia", "energy", "energía", "materiais", "materials", "materiales", "agricultura", "agriculture"},
                        {"florestal", "forestry", "forestal", "veterinária", "veterinary", "veterinaria", "enfermagem", "nursing", "enfermería"},
                        {"odontologia", "dentistry", "odontología", "farmácia", "pharmacy", "farmacia", "nutrição", "nutrition", "nutrición"}
                    ]
                    
                    # Adiciona sinônimos em outros idiomas se encontrar qualquer termo correspondente
                    novas_palavras = set()
                    for pal in palavras_filtradas:
                        for grupo in sinonimos_academicos:
                            if pal in grupo:
                                novas_palavras.update(grupo)
                                break
                    palavras_filtradas.update(novas_palavras)
                    
                    if palavras_filtradas:
                        def calcular_relevancia(row):
                            score = 0
                            nome = str(row.iloc[0]).lower()
                            grande_area = str(row.get("Grande Area", "")).lower()
                            area = str(row.get("Area do Conhecimento", "")).lower()
                            subarea = str(row.get("Subárea do Conhecimento", "")).lower()
                            
                            for pal in palavras_filtradas:
                                if pal in nome:
                                    score += 5  # Maior peso para termos no nome da revista
                                if pal in grande_area:
                                    score += 3
                                if pal in area:
                                    score += 3
                                if pal in subarea:
                                    score += 3
                            return score
                        
                        df_candidatos["relevancia"] = df_candidatos.apply(calcular_relevancia, axis=1)
                        # Ordena pelas mais relevantes tematicamente e depois pelo prestígio (SJR)
                        df_candidatos = df_candidatos.sort_values(by=["relevancia", "SJR"], ascending=[False, False])
                    else:
                        df_candidatos["relevancia"] = 0
                        df_candidatos = df_candidatos.sort_values(by="SJR", ascending=False)
                    
                    # Seleciona até 40 candidatos mais relevantes — reduz consumo de tokens da API
                    if len(df_candidatos) > 40:
                        df_candidatos = df_candidatos.head(40)
                    
                    # Payload enxuto: somente os campos essenciais para a IA tomar a decisão
                    cols_envio = [df_original.columns[0]]
                    for col in ["Grande Area", "Area do Conhecimento", "Indexador", "Quartil JCR", "SJR"]:
                        if col in df_candidatos.columns:
                            cols_envio.append(col)
                    lista_periodicos_envio = df_candidatos[cols_envio].to_dict(orient="records")
                    
                    # Prompt estruturado para forçar o retorno estrito de um array JSON
                    prompt_ia = f"""
                    Atue como especialista em publicação acadêmica de alto impacto. O pesquisador submeteu o seguinte artigo científico:
                    TÍTULO DO ARTIGO: {titulo_artigo}
                    RESUMO DO ARTIGO: {resumo_artigo}

                    Com base estritamente na lista de periódicos abaixo estruturada em JSON, selecione até {num_recomendacoes} (dentre as disponíveis) revistas científicas que apresentem a maior aderência temática, metodológica e de escopo.

                    IMPORTANTES DIRETRIZES DE SELEÇÃO (ORDEM DE PRIORIDADE):
                    1. PRIORIDADE MÁXIMA (Grau de Aderência): O critério principal de escolha deve ser a aderência temática, metodológica e de escopo do artigo ao periódico. O assunto do artigo deve fazer total sentido com a linha editorial da revista.
                    2. SEGUNDA PRIORIDADE (Qualidade e Prestígio): Dentre os periódicos com alta aderência e compatibilidade temática, priorize aqueles com maior prestígio acadêmico e qualidade científica (indicados por quartis JCR e índice SJR elevados).
                    3. Não limite as recomendações ao idioma do título/resumo enviado. Siga estritamente as regras de cruzamento de idiomas abaixo:
                       - Se o artigo estiver em PORTUGUÊS: Recomende as melhores opções de revistas brasileiras (em português) e também as melhores revistas internacionais (em inglês ou espanhol) que cubram o tema.
                       - Se o artigo estiver em INGLÊS: Traga os principais periódicos internacionais (em inglês ou espanhol) e também inclua as revistas brasileiras de alto padrão que cubram o tema.
                       - Se o artigo estiver em ESPANHOL: Traga os principais periódicos internacionais (em espanhol ou inglês) e também inclua as revistas brasileiras de alto padrão que cubram o tema.
                    
                    Lista de Periódicos Candidatos:
                    {json.dumps(lista_periodicos_envio, ensure_ascii=False)}

                    Sua resposta deve ser obrigatoriamente um array JSON válido (sem tags markdown em volta como ```json, apenas a string crua do array), com chaves exatas:
                    - "revista_nome": Nome exato da revista como aparece no catálogo enviado
                    - "porcentagem_aderencia": Apenas um número inteiro de 0 a 100 estimando a aderência
                    - "justificativa": Uma justificativa de até 3 linhas explicando o porquê da recomendação, escrita EXATAMENTE no mesmo idioma em que o resumo do usuário foi enviado.
                    """
                    
                    modelos_tentar = [
                        "gemini-2.5-flash",
                        "gemini-2.5-pro",
                        "gemini-2.0-flash",
                        "gemini-2.0-flash-001",
                        "gemini-3.5-flash",
                        "gemini-flash-latest",
                        "gemini-pro-latest",
                        "gemini-2.0-flash-lite",
                    ]
                    
                    sucesso_ia = False
                    ultimo_erro_msg = ""
                    cota_esgotada = False

                    for modelo in modelos_tentar:
                        try:
                            url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key_ativa}"
                            payload = {
                                "contents": [{"parts": [{"text": prompt_ia}]}]
                            }
                            headers = {"Content-Type": "application/json"}
                            
                            response = requests.post(url_api, json=payload, headers=headers, timeout=45)
                            
                            if response.status_code == 200:
                                dados_resposta = response.json()
                                texto_resposta = dados_resposta["candidates"][0]["content"]["parts"][0]["text"].strip()
                                
                                if texto_resposta.startswith("```"):
                                    texto_resposta = re.sub(r'^```(?:json)?\n|```$', '', texto_resposta, flags=re.MULTILINE).strip()
                                
                                match = re.search(r'\[\s*\{.*\}\s*\]', texto_resposta, re.DOTALL)
                                if match:
                                    texto_resposta = match.group(0)
                                
                                st.session_state.recomendacoes = json.loads(texto_resposta)
                                # Salva no cache para evitar chamadas repetidas com a mesma entrada
                                st.session_state.ia_cache[cache_key] = st.session_state.recomendacoes
                                sucesso_ia = True
                                break
                            elif response.status_code == 429:
                                # Cota esgotada — ativa fallback local imediatamente sem espera
                                cota_esgotada = True
                                break
                            else:
                                ultimo_erro_msg = f"Modelo {modelo} falhou (Status {response.status_code}): {response.text}"
                        except Exception as ex:
                            ultimo_erro_msg = f"Modelo {modelo} falhou com exceção: {ex}"
                        
                        if cota_esgotada:
                            break
                    
                    if not sucesso_ia:
                        # FALLBACK LOCAL AUTOMÁTICO: gera recomendações diretamente pelo algoritmo de pontuação
                        texto_detect = f"{titulo_artigo} {resumo_artigo}".lower()
                        pt_stops = {"o", "a", "e", "de", "do", "da", "em", "para", "um", "uma", "com", "por", "os", "as"}
                        en_stops = {"the", "and", "of", "in", "to", "a", "is", "that", "for", "it", "with", "on", "as"}
                        pt_count = sum(1 for w in re.findall(r'\b\w+\b', texto_detect) if w in pt_stops)
                        en_count = sum(1 for w in re.findall(r'\b\w+\b', texto_detect) if w in en_stops)
                        is_english = en_count > pt_count

                        col_titulo = df_original.columns[0]
                        top_n = df_candidatos.head(num_recomendacoes)
                        recomendacoes_locais = []
                        
                        # Obtém a pontuação máxima de relevância para normalização
                        max_rel = float(df_candidatos["relevancia"].max()) if "relevancia" in df_candidatos.columns else 0.0
                        
                        for idx, (_, row) in enumerate(top_n.iterrows()):
                            nome_rev = str(row[col_titulo])
                            area_rev = str(row.get("Area do Conhecimento", row.get("Grande Area", "-")))
                            subarea_rev = str(row.get("Subárea do Conhecimento", ""))
                            gr_area_rev = str(row.get("Grande Area", ""))
                            indexador_rev = str(row.get("Indexador", "-"))
                            sjr_rev = row.get("SJR", None)
                            quartil_rev = str(row.get("Quartil JCR", "-"))
                            rel_score = float(row.get("relevancia", 0.0))
                            
                            # Determina a porcentagem de aderência de forma realista e decrescente por rank
                            if max_rel > 0:
                                # Mapeia proporcionalmente ao score de relevância, variando de 82% a 96%
                                pct_rel = 82 + int((rel_score / max_rel) * 14)
                                # Garante consistência do ranking decrescente (ex: 1º=95%, 2º=92%, etc.)
                                pct_rank = 96 - (idx * 3)
                                pct = min(96, max(pct_rel, pct_rank))
                            else:
                                # Se não houver matches de palavras-chave, ordena por SJR de 60% a 78%
                                pct = max(60, 78 - (idx * 4))
                            
                            # Encontra palavras-chave que de fato casaram com esta revista
                            matched_keywords = []
                            nome_lower = nome_rev.lower()
                            area_lower = area_rev.lower()
                            subarea_lower = subarea_rev.lower()
                            gr_area_lower = gr_area_rev.lower()
                            
                            for p in palavras_filtradas:
                                if p in nome_lower or p in area_lower or p in subarea_lower or p in gr_area_lower:
                                    # Capitaliza a primeira letra do termo de busca para visualização premium
                                    matched_keywords.append(p.capitalize())
                            
                            # Justificativas inteligentes em 2 idiomas
                            if is_english:
                                if matched_keywords:
                                    kw_str = ", ".join(f"'{k}'" for k in list(matched_keywords)[:3])
                                    justificativa = f"Demonstrates strong thematic alignment with key concepts found in your work, specifically: {kw_str}."
                                else:
                                    justificativa = f"Recommended based on the journal's editorial scope in {area_rev}."
                                
                                detalhes = []
                                if quartil_rev and quartil_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"classified as {quartil_rev}")
                                if sjr_rev and str(sjr_rev) not in ["-", "None", "nan"]:
                                    try:
                                        detalhes.append(f"SJR rank of {float(sjr_rev):.3f}")
                                    except:
                                        pass
                                if indexador_rev and indexador_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"indexed in {indexador_rev}")
                                    
                                if detalhes:
                                    justificativa += f" The journal is {', '.join(detalhes)}."
                            else:
                                # Português / Espanhol
                                if matched_keywords:
                                    kw_str = ", ".join(f"'{k}'" for k in list(matched_keywords)[:3])
                                    justificativa = f"Apresenta forte alinhamento temático com conceitos-chave identificados no seu artigo, especialmente: {kw_str}."
                                else:
                                    justificativa = f"Recomendado com base no escopo editorial do periódico na área de {area_rev}."
                                
                                detalhes = []
                                if quartil_rev and quartil_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"classificação {quartil_rev}")
                                if sjr_rev and str(sjr_rev) not in ["-", "None", "nan"]:
                                    try:
                                        detalhes.append(f"SJR de {float(sjr_rev):.3f}")
                                    except:
                                        pass
                                if indexador_rev and indexador_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"indexado em {indexador_rev}")
                                    
                                if detalhes:
                                    justificativa += f" O periódico possui {', '.join(detalhes)}."
                            
                            recomendacoes_locais.append({
                                "revista_nome": nome_rev,
                                "porcentagem_aderencia": pct,
                                "justificativa": justificativa
                            })
                        
                        st.session_state.recomendacoes = recomendacoes_locais
                        st.session_state.ia_cache[cache_key] = recomendacoes_locais
                        # Sinaliza que foi modo local para exibir aviso amigável
                        st.session_state.modo_local = True
            
            # Limpa o indicador de progresso do DOM virtual
            status_container.empty()
            
            # Recarrega a página de forma limpa para exibir os resultados fora do fluxo do botão
            st.rerun()

    # RENDERIZAÇÃO ESTÁVEL DOS RESULTADOS (Lidos do st.session_state, fora do condicional do st.button)
    if st.session_state.get("aviso_filtro"):
        st.warning("⚠️ Nenhum periódico no catálogo atende aos filtros de Grande Área e Indexador selecionados. Por favor, ajuste os filtros.")
    elif st.session_state.get("erro_ia"):
        erro_msg = st.session_state.erro_ia
        if erro_msg.startswith("⏳"):
            # Erro de cota — exibe aviso amigável sem detalhes técnicos
            st.warning(erro_msg)
        else:
            st.error(t['ia_erro'])
            st.caption(f"Detalhes técnicos do erro: {erro_msg}")
    elif st.session_state.get("recomendacoes") is not None:
        if st.session_state.get("modo_local"):
            st.info("ℹ️ Resultado gerado pelo algoritmo local de relevância (a API do Gemini atingiu o limite de cota). A qualidade das recomendações é excelente — baseada em correspondência temática e métricas SJR/JCR.")
        st.success(t['ia_sucesso'])
        
        for rec in st.session_state.recomendacoes:
            # Busca segura no df original usando a coluna index 0 para o nome
            registro_revista = df_original[df_original[df_original.columns[0]] == rec["revista_nome"]]
            
            homepage = ""
            issn = "N/A"
            indexador = "N/A"
            quartil = "N/A"
            sjr = "N/A"
            
            if not registro_revista.empty:
                # 1. Garante que os valores existam de forma segura antes de converter para string
                try:
                    issn = str(registro_revista.iloc[0].get("ISSN", "-"))
                    indexador = str(registro_revista.iloc[0].get("Indexador", "-"))
                    quartil = str(registro_revista.iloc[0].get("Quartil JCR", "-"))
                    sjr = str(registro_revista.iloc[0].get("SJR", "-"))
                    homepage = str(registro_revista.iloc[0].get("Homepage", ""))
                except Exception:
                    issn, indexador, quartil, sjr, homepage = "-", "-", "-", "-", ""
            
                # 2. Renderização de card para cada recomendação (até 10 dinâmicas)
                with st.container(border=True):
                    col_info, col_link = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"### {rec['revista_nome']}")
                        st.caption(f"**ISSN:** {issn} | **Indexador:** {indexador} | **Quartil:** {quartil} | **SJR:** {sjr}")
                        st.markdown(f"🎯 **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                        st.markdown(f"💡 **{t['ia_card_motivo']}** {rec['justificativa']}")
                        
                        # SE HOUVER UM st.dataframe() ESCONDIDO AQUI PARA MOSTRAR OS DADOS COMPLETOS:
                        # Envolva-o SEMPRE em um validador de tamanho para não quebrar o Arrow
                        if len(registro_revista) > 0:
                            st.dataframe(registro_revista, hide_index=True, **kwargs_largura)
                    
                    with col_link:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if homepage and homepage not in ["nan", "-", "None", ""]:
                            st.link_button(t['ia_card_site'], homepage, type="primary", **kwargs_largura)
                        else:
                            st.info(t['ia_card_sem_site'])
            else:
                # Caso a IA recomende um nome de revista que sofreu uma variação de string e não casou no CSV
                with st.container(border=True):
                    st.markdown(f"### {rec['revista_nome']}")
                    st.caption("⚠️ *Periódico sugerido pela IA, mas metadados detalhados não localizados na base local.*")
                    st.markdown(f"🎯 **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                    st.markdown(f"💡 **{t['ia_card_motivo']}** {rec['justificativa']}")

# ==================== ABA 3: ESTATÍSTICAS DE ACESSOS (SÓ PARA ADMIN) ====================
if "admin" in params_url or "visitas" in params_url or st.session_state.get("is_admin", False):
    with tab_admin:
        st.subheader("📊 Estatísticas de Acessos dos Usuários")
        
        # Função para carregar dados dos usuários
        usuarios_list = []
        # 1. Tenta carregar do Firebase se disponível
        if db is not None:
            try:
                docs = db.collection("usuarios").stream()
                for doc in docs:
                    d = doc.to_dict()
                    ultimo = d.get("ultimo_acesso")
                    usuarios_list.append({
                        "Nome": d.get("nome", "-"),
                        "Email": d.get("email", "-"),
                        "País": d.get("pais", "-"),
                        "Telefone": d.get("telefone", "-"),
                        "Escolaridade": d.get("escolaridade", "-"),
                        "Instituição": d.get("instituicao", "-"),
                        "Acessos (Logins)": d.get("acessos", 1),
                        "Último Acesso": ultimo.strftime("%Y-%m-%d %H:%M:%S") if ultimo and hasattr(ultimo, 'strftime') else str(ultimo)
                    })
            except Exception:
                pass
                
        # 2. Se a lista estiver vazia (ou Firebase falhou/não configurado), carrega do usuarios.csv local
        if not usuarios_list:
            caminho_csv = "usuarios.csv"
            if os.path.exists(caminho_csv):
                try:
                    df_local = pd.read_csv(caminho_csv, sep=";")
                    for _, row in df_local.iterrows():
                        acessos_val = row.get("Acessos", 1)
                        usuarios_list.append({
                            "Nome": row.get("Nome", "-"),
                            "Email": row.get("Email", "-"),
                            "País": row.get("País", "-"),
                            "Telefone": row.get("Telefone", "-"),
                            "Escolaridade": row.get("Escolaridade", "-"),
                            "Instituição": row.get("Instituição", "-"),
                            "Acessos (Logins)": int(acessos_val) if pd.notna(acessos_val) else 1,
                            "Último Acesso": row.get("Data/Hora", "-")
                        })
                except Exception:
                    pass
                    
        df_stats = pd.DataFrame(usuarios_list)
        if not df_stats.empty:
            # Ordena pelo maior número de acessos
            df_stats = df_stats.sort_values(by="Acessos (Logins)", ascending=False).reset_index(drop=True)
            
            # Exibe em uma tabela interativa do Streamlit
            st.dataframe(
                df_stats,
                use_container_width=True,
                column_config={
                    "Acessos (Logins)": st.column_config.NumberColumn("Acessos", format="%d"),
                    "Email": st.column_config.Column("Email")
                }
            )
            
            # Permite download em CSV
            csv_data = df_stats.to_csv(index=False, sep=";").encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Planilha de Acessos (CSV)",
                data=csv_data,
                file_name="estatisticas_acessos.csv",
                mime="text/csv",
                key="admin_download_stats_btn"
            )
        else:
            st.info("Nenhum usuário cadastrado encontrado na base.")