import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Safe lazy imports for services
def _safe_import(name):
    try:
        __import__(name)
        return True
    except Exception:
        return False

_discovery_ok = _safe_import("services.discovery_recommender")
_similar_ok = _safe_import("services.similar_articles_finder")
_evaluator_ok = _safe_import("services.article_evaluator")
_cache_ok = _safe_import("services.cache_manager")
_logger_ok = _safe_import("utils.logger")

    

def get_texto_termos(lang):
    if st.session_state.get("idioma", "English") == "English":
        return '''### SciPubs Terms of Use and Privacy Policy

**Last Updated:** July 13, 2026

**1. INTRODUCTION AND ACCEPTANCE**

1.1. Welcome to SciPubs: The Researcher's Portal ("Platform"). This document ("Terms") governs your relationship with our Platform, establishing the conditions of use and personal data processing practices.

1.2. ACCEPTANCE: By clicking the "I have read and accept the Terms of Use" button and completing your registration, you ("Data Subject") declare to have read, understood, and fully agreed with all provisions contained herein, expressing your free, informed, and unambiguous consent for the processing of your personal data for the purposes described herein. If you do not agree with these Terms, you should not use the Platform.

**2. PURPOSE AND GRATUITY**

2.1. The Platform aims to assist researchers in the production and publication of scientific articles, offering a journal search tool, integrated with Artificial Intelligence (Google Gemini), and links to external academic resources.

2.2. The access and use of all functionalities of the Platform are, as of the present date, entirely free. The Data Subject will be notified at least 30 (thirty) days in advance in the event of any changes to the business model.

**3. VOLUNTARY DONATIONS**

3.1. The Data Subject who wishes to support the maintenance and continuous development of the Platform may do so through voluntary donations, made in a specific section within the application.

3.2. ABSENCE OF COUNTERPART: Donations are acts of mere liberality and do not grant the donating Data Subject any exclusive rights, benefits, features, products, or services in return. The access and resources of the Platform remain identical for all Data Subjects, whether donors or not.

3.3. PAYMENT INTERMEDIARY: Donation transactions will be processed through third-party payment platforms (e.g., Buy Me a Coffee). By choosing to donate, the Data Subject will be directed to the intermediary's secure environment and will be subject to the Terms of Use and Privacy Policies of the respective payment platform.

3.4. DISCLAIMER: SciPubs is not responsible for any failures, security breaches, or data collection carried out by the payment platform. The financial transaction and the data associated with it (such as credit card data) are the responsibility of the chosen intermediary.

3.5. NON-REFUNDABLE: Due to their nature as voluntary acts without a counterpart, donations made are, as a rule, final and non-refundable.

**4. DATA PROCESSING AGENTS AND DPO**

4.1. SciPubs acts as the Controller of personal data. For the technical viability of the service, we use the infrastructure of Google LLC (Firebase), which acts as the Operator.

4.2. DATA PROTECTION OFFICER (DPO): For any questions regarding these Terms or the exercise of your rights, the Data Subject may contact our Officer via email: support@scipubs.com.

**5. PROCESSING OF PERSONAL DATA**

5.1. LEGAL BASIS: The processing of all personal data collected by the Platform is based exclusively on the Data Subject's Consent, provided at the time of registration.

5.2. DATA COLLECTED FOR PLATFORM OPERATION (MANDATORY): We collect the minimum data necessary for specific purposes, whose consent is provided at the time of main registration: Full Name and Email Address.

5.3. DATA FOR USAGE RESEARCH PURPOSES (SECONDARY PURPOSE): With your specific consent, the data may be used for the elaboration of studies, articles, and scientific research. * ANONYMIZATION GUARANTEE: For this purpose, all data will be previously submitted to an anonymization process.

5.4. DATA FOR DEMOGRAPHIC PROFILE RESEARCH (OPTIONAL AND SENSITIVE): The Platform offers the Data Subject the optional opportunity to contribute to research on diversity and inclusion. Participation is optional and uses an enhanced anonymization process.

**6. DATA SUBJECT RIGHTS**

6.1. The Data Subject has the right to, at any time: access their data, correct incomplete data, request deletion, or revoke consent.

**7. SECURITY AND INTERNATIONAL TRANSFER**

7.1. We employ technical and administrative measures to protect personal data from unauthorized access. Data is stored on secure cloud infrastructure (Google Firebase).

7.2. INTERNATIONAL TRANSFER: By using Google's global infrastructure, personal data may be transferred and processed on servers located outside your country.

**8. CHANGES AND JURISDICTION**

8.1. These Terms may be updated. The Data Subject will be notified of substantial changes.

8.2. JURISDICTION: The courts of the judicial district where the *SciPubs* is headquartered are designated to resolve any disputes arising from these Terms, with the express waiver of any other jurisdiction, however privileged it may be.'''
    elif st.session_state.get("idioma", "English") == "Español":
        return '''### Términos de Uso y Política de Privacidad de SciPubs

**Última Actualización:** 13 de julio de 2026

**1. INTRODUCCIÓN Y ACEPTACIÓN**

1.1. Bienvenido a SciPubs: El Portal del Investigador ("Plataforma"). Este documento ("Términos") rige su relación con nuestra Plataforma, estableciendo las condiciones de uso y las prácticas de tratamiento de datos personales.

1.2. ACEPTACIÓN: Al hacer clic en el botón "He leído y acepto los Términos de Uso" y completar su registro, usted ("Titular") declara haber leído, comprendido y aceptado íntegramente todas las disposiciones aquí contenidas, manifestando su consentimiento libre e informado para el tratamiento de sus datos personales. Si no está de acuerdo con estos Términos, no debe utilizar la Plataforma.

**2. OBJETO Y GRATUIDAD**

2.1. La Plataforma tiene como objetivo ayudar a los investigadores en la producción y publicación de artículos científicos, ofreciendo una herramienta de búsqueda de revistas, integrada con Inteligencia Artificial (Google Gemini), y enlaces a recursos académicos externos.

2.2. El acceso y uso de todas las funcionalidades de la Plataforma son, a la fecha actual, totalmente gratuitos. El Titular será notificado con al menos 30 (treinta) días de antelación en caso de cualquier cambio en el modelo de negocio.

**3. DONACIONES VOLUNTARIAS**

3.1. El Titular que desee apoyar el mantenimiento y el desarrollo continuo de la Plataforma podrá hacerlo a través de donaciones voluntarias, realizadas en una sección específica dentro de la aplicación.

3.2. AUSENCIA DE CONTRAPARTIDA: Las donaciones son actos de mera liberalidad y no confieren al Titular donante ningún derecho, beneficio, característica, producto o servicio exclusivo a cambio. El acceso y los recursos de la Plataforma siguen siendo idénticos para todos los Titulares, sean donantes o no.

3.3. INTERMEDIARIO DE PAGO: Las transacciones de donación se procesarán a través de plataformas de pago de terceros (ej. Buy Me a Coffee). Al optar por donar, el Titular será dirigido al entorno seguro del intermediario y estará sujeto a los Términos de Uso y Políticas de Privacidad de la respectiva plataforma de pago.

3.4. EXENCIÓN DE RESPONSABILIDAD: SciPubs no se hace responsable de posibles fallos, brechas de seguridad o la recopilación de datos realizada por la plataforma de pago. La transacción financiera y los datos asociados a ella (como los datos de la tarjeta de crédito) son responsabilidad del intermediario elegido.

3.5. NO REEMBOLSABLE: Debido a su naturaleza de acto voluntario sin contrapartida, las donaciones realizadas son, por regla general, finales y no reembolsables.

**4. AGENTES DE TRATAMIENTO DE DATOS Y DPO**

4.1. SciPubs actúa como Controlador de los datos personales. Para la viabilidad técnica del servicio, utilizamos la infraestructura de Google LLC (Firebase), que actúa como Operador.

4.2. OFICIAL DE PROTECCIÓN DE DATOS (DPO): Para cualquier consulta sobre estos Términos, el Titular puede contactar a nuestro Oficial a través del correo electrónico: support@scipubs.com.

**5. TRATAMIENTO DE DATOS PERSONALES**

5.1. BASE LEGAL: El tratamiento de todos los datos personales recopilados por la Plataforma se basa exclusivamente en el Consentimiento del Titular, proporcionado en el momento del registro.

5.2. DATOS RECOPILADOS PARA EL FUNCIONAMIENTO DE LA PLATAFORMA (OBLIGATORIO): Recopilamos los datos mínimos necesarios para fines específicos: Nombre Completo y Dirección de Correo Electrónico.

5.3. DATOS PARA FINES DE INVESTIGACIÓN DE USO (PROPÓSITO SECUNDARIO): Con su consentimiento específico, los datos podrán ser utilizados para la elaboración de estudios e investigaciones científicas. * GARANTÍA DE ANONIMIZACIÓN: Todos los datos serán previamente sometidos a un proceso de anonimización.

5.4. DATOS PARA INVESTIGACIÓN DE PERFIL DEMOGRÁFICO (OPCIONAL Y SENSIBLE): La Plataforma ofrece al Titular la oportunidad opcional de contribuir a la investigación sobre diversidad e inclusión. La participación es opcional y utiliza un proceso de anonimización mejorado.

**6. DERECHOS DEL TITULAR**

6.1. El Titular tiene el derecho de, en cualquier momento: acceder a sus datos, corregir datos incompletos, solicitar eliminación o revocar el consentimiento.

**7. SEGURIDAD Y TRANSFERENCIA INTERNACIONAL**

7.1. Empleamos medidas técnicas y administrativas para proteger los datos personales. Los datos se almacenan en infraestructura de nube segura (Google Firebase).

7.2. TRANSFERENCIA INTERNACIONAL: Al utilizar la infraestructura global de Google, los datos personales pueden ser transferidos y procesados en servidores ubicados fuera de su país.

**8. CAMBIOS Y JURISDICCIÓN**

8.1. Estos Términos pueden ser actualizados. El Titular será notificado de cambios sustanciales.

8.2. JURISDICCIÓN: Para resolver cualquier disputa que surja de estos Términos, se elegirá la jurisdicción del tribunal donde se encuentra la sede del SciPubs, renunciando expresamente a cualquier otra, por muy privilegiada que sea.'''
    else:
        return '''### Termos de Uso e Política de Privacidade do SciPubs

**Data da Última Atualização:** 13 de julho de 2026

**1. INTRODUÇÃO E ACEITAÇÃO**

1.1. Bem-vindo ao SciPubs: O Portal do Pesquisador ("Plataforma"). Este documento ("Termos") rege a sua relação com a nossa Plataforma, estabelecendo as condições de uso e as práticas de tratamento de dados pessoais.

1.2. ACEITAÇÃO: Ao clicar no botão "Eu li e aceito os Termos de Uso e Política de Privacidade" e concluir o seu cadastro, você ("Titular") declara ter lido, compreendido e concordado integralmente com todas as disposições aqui contidas, manifestando seu consentimento livre, informado e inequívoco para o tratamento de seus dados pessoais. Caso não concorde com estes Termos, você não deverá utilizar a Plataforma.

**2. OBJETO E GRATUIDADE**

2.1. A Plataforma tem como objetivo auxiliar pesquisadores na produção e publicação de artigos científicos, oferecendo uma ferramenta de busca em periódicos, integrada com Inteligência Artificial (Google Gemini), e links para recursos acadêmicos externos.

2.2. O acesso e uso de todas as funcionalidades da Plataforma são, na presente data, inteiramente gratuitos. O Titular será notificado com antecedência mínima de 30 (trinta) dias caso haja qualquer alteração no modelo de negócio.

**3. DOAÇÕES VOLUNTÁRIAS**

3.1. O Titular que desejar apoiar a manutenção e o desenvolvimento contínuo da Plataforma poderá fazê-lo através de doações voluntárias, realizadas em seção específica dentro do aplicativo.

3.2. AUSÊNCIA DE CONTRAPARTIDA: As doações são atos de mera liberalidade e não conferem ao Titular doador quaisquer direitos, benefícios, funcionalidades exclusivas, produtos ou serviços em contrapartida. O acesso e os recursos da Plataforma permanecem idênticos para todos os Titulares, doadores ou não.

3.3. INTERMEDIADOR DE PAGAMENTO: As transações de doação serão processadas por meio de plataformas de pagamento de terceiros (ex: Buy Me a Coffee). Ao optar por doar, o Titular será direcionado ao ambiente seguro do intermediador e estará sujeito aos Termos de Uso e Políticas de Privacidade da respectiva plataforma de pagamento.

3.4. ISENÇÃO DE RESPONSABILIDADE: O SciPubs não se responsabiliza por eventuais falhas, violações de segurança ou pela coleta de dados realizada pela plataforma de pagamento. A transação financeira e os dados a ela associados (como dados de cartão de crédito) são de responsabilidade do intermediador escolhido.

3.5. NÃO REEMBOLSO: Por sua natureza de ato voluntário e sem contrapartida, as doações realizadas são, em regra, finais e não reembolsáveis.

**4. AGENTES DE TRATAMIENTO E ENCARREGADO (DPO)**

4.1. Para os fins da LGPD, o SciPubs atua como Controlador dos dados pessoais. Para a viabilização técnica do serviço, utilizamos a infraestrutura da Google LLC (Firebase), que atua como Operadora.

4.2. ENCARREGADO PELO TRATAMENTO DE DADOS (DPO): Para qualquer questão relativa a estes Termos, o Titular poderá contatar nosso Encarregado através do e-mail: support@scipubs.com.

**5. TRATAMENTO DE DADOS PESSOAIS**

5.1. BASE LEGAL: O tratamento de todos os dados pessoais coletados pela Plataforma fundamenta-se exclusivamente no Consentimento do Titular, fornecido no ato do cadastro.

5.2. DADOS COLETADOS PARA FUNCIONAMENTO DA PLATAFORMA (OBRIGATÓRIO): Coletamos o mínimo de dados necessários para as seguintes finalidades específicas: Nome Completo e Endereço de E-mail.

5.3. DADOS PARA FINS DE PESQUISA DE USO (FINALIDADE SECUNDÁRIA): Com o seu consentimento específico, os dados poderão ser utilizados para a elaboração de estudos, artigos e pesquisas científicas. * GARANTIA DE ANONIMIZAÇÃO: Para esta finalidade, todos os dados serão previamente submetidos a um processo de anonimização.

5.4. DADOS PARA PESQUISA DE PERFIL DEMOGRÁFICO (OPCIONAL E SENSÍVEL): A Plataforma oferece ao Titular a oportunidade opcional de contribuir com pesquisas sobre diversidade e inclusão. A participação é opcional e utiliza anonimização reforçada.

**6. DIREITOS DO TITULAR**

6.1. O Titular tem o direito de, a qualquer momento: acessar seus dados, corrigir dados incompletos, solicitar a eliminação ou revogar o consentimento.

**7. SEGURANÇA E TRANSFERENCIA INTERNACIONAL**

7.1. Empregamos medidas técnicas e administrativas aptas a proteger os dados pessoais. Os dados são armazenados em infraestrutura de nuvem segura (Google Firebase).

7.2. TRANSFERÊNCIA INTERNACIONAL: Ao utilizar a infraestrutura global da Google, os dados pessoais do Titular podem ser transferidos e processados em servidores localizados fora do Brasil.

**8. ALTERAÇÕES E FORO**

8.1. Estes Termos poderão ser atualizados. Ocorrendo alterações substanciais, o Titular será notificado.

8.2. FORO: Para dirimir quaisquer controvérsias oriundas destes Termos, fica eleito o foro da Comarca da sede do SciPubs, com renúncia expressa a qualquer outro, por mais privilegiado que seja.
'''

@st.dialog("📄 Termos de Uso e Política de Privacidade / Terms of Use / Términos de Uso", width="large")
def modal_termos():
    lang = st.session_state.get('idioma', 'Português')
    texto_termos = get_texto_termos(lang)
    st.markdown(texto_termos)
    
    fechar_btn = "Fechar"
    if st.session_state.get("idioma", "English") == "English": fechar_btn = "Close"
    elif st.session_state.get("idioma", "English") == "Español": fechar_btn = "Cerrar"
        
    if st.button(fechar_btn, type="primary"):
        st.rerun()

@st.dialog("❤️ Apoie o SciPubs! / Support SciPubs!", width="large")
def modal_doacao():
    lang = st.session_state.get('idioma', 'Português')
    
    if st.session_state.get("idioma", "English") == "English":
        st.markdown('''
        ### Thank you for supporting Science!
        Your voluntary donation is essential for us to keep our servers active and continue developing new technological tools for the academic and scientific community.
        
        **How to donate:**
        We use **Buy Me a Coffee**, a secure international platform. It's very simple:
        1. Click the link below to go to our official page.
        2. Choose the number of "coffees" you want to donate (each coffee represents a small symbolic amount).
        3. Complete the payment securely using a credit card or other available local methods.
        
        👉 **[Click here to donate via Buy Me a Coffee](https://buymeacoffee.com/scipubs)**
        
        *Important: Your donation is completely voluntary and does not require any service counterpart from our platform.*
        ''')
        btn_close = "Close"
    elif st.session_state.get("idioma", "English") == "Español":
        st.markdown('''
        ### ¡Gracias por apoyar la Ciencia!
        Su donación voluntaria es fundamental para mantener nuestros servidores activos y continuar desarrollando nuevas herramientas tecnológicas para la comunidad académica y científica.
        
        **Cómo donar:**
        Utilizamos **Buy Me a Coffee**, una plataforma internacional segura. Es muy sencillo:
        1. Haga clic en el enlace de abajo para ir a nuestra página oficial.
        2. Elija la cantidad de "cafés" que desea donar (cada café representa una pequeña cantidad simbólica).
        3. Complete el pago de forma segura utilizando una tarjeta de crédito u otros métodos locales disponibles.
        
        👉 **[Haga clic aquí para donar a través de Buy Me a Coffee](https://buymeacoffee.com/scipubs)**
        
        *Importante: Su donación es completamente voluntaria y no exige ninguna contrapartida de servicios de nuestra plataforma.*
        ''')
        btn_close = "Cerrar"
    else:
        st.markdown('''
        ### Obrigado por apoiar a Ciência!
        A sua doação voluntária é fundamental para mantermos os nossos servidores ativos e continuarmos desenvolvendo novas ferramentas tecnológicas para a comunidade acadêmica e científica.
        
        **Como realizar a sua doação:**
        Nós utilizamos o **Buy Me a Coffee**, uma plataforma internacional segura. É muito simples:
        1. Clique no link abaixo para acessar a nossa página oficial.
        2. Escolha a quantidade de "cafés" que deseja doar (cada café representa um pequeno valor simbólico, geralmente $5).
        3. Conclua o pagamento de forma segura utilizando seu cartão de crédito, Apple Pay, Google Pay ou outros métodos disponíveis.
        
        👉 **[Clique aqui para doar pelo Buy Me a Coffee](https://buymeacoffee.com/scipubs)**
        
        *Importante: A sua doação é totalmente espontânea e não exige nenhuma contrapartida de serviços da nossa plataforma.*
        ''')
        btn_close = "Fechar"
        
    if st.button(btn_close, type="primary"):
        if st.session_state.get('modo_cadastro', False):
            st.session_state.modo_cadastro = False
            st.session_state.modo_login = True
        st.rerun()
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

# Imports diretos dos módulos de serviço (evita dependência do __init__.py no GitHub)

def call_hybrid_api(title: str, abstract: str, api_url: str, top_n: int = 10,
                    min_year: int = 2021, max_apc_usd: float = None,
                    max_decision_days: int = None, require_oa: bool = False) -> dict:
    """Chama a API FastAPI híbrida /recommend"""
    import requests
    payload = {
        "title": title,
        "abstract": abstract,
        "top_n": top_n,
        "min_year": min_year,
        "max_apc_usd": max_apc_usd,
        "max_decision_days": max_decision_days,
        "require_oa": require_oa,
        "generate_justifications": True
    }
    response = requests.post(f"{api_url}/recommend", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_discovery_api(title: str, abstract: str, api_url: str, top_n: int = 20,
                       idioma: str = "Português") -> dict:
    """
    Chama a API Discovery-First /recommend/discovery.
    Usa classificação de área + busca vetorial + proxy de aceitação.
    """
    import requests
    payload = {
        "title": title,
        "abstract": abstract,
        "top_n": top_n,
        "idioma": idioma
    }
    response = requests.post(f"{api_url}/recommend/discovery", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def get_similar_articles_finder(email_openalex=None):
    from services.similar_articles_finder import SimilarArticlesFinder; return SimilarArticlesFinder(email_openalex=email_openalex)


def get_article_evaluator(df_local, ollama_model="llama3"):
    from services.article_evaluator import ArticleEvaluator; return ArticleEvaluator(df_local=df_local, ollama_model=ollama_model)


def get_cache_manager():
    try:
        from services.cache_manager import CacheManager
        return CacheManager()
    except Exception:
        return None
    from services.cache_manager import CacheManager


class RecommendationCache:
    """Cache simples em memória com TTL para recomendações Discovery-First."""

    def __init__(self, ttl_seconds: int = 86400):
        self._store: dict = {}
        self._ttl = ttl_seconds

    def _key(self, title: str, abstract: str, top_n: int, idioma: str) -> str:
        return f"discovery:{hash(title + abstract + str(top_n) + idioma)}"

    def get(self, title: str, abstract: str, top_n: int, idioma: str):
        k = self._key(title, abstract, top_n, idioma)
        entry = self._store.get(k)
        if not entry:
            return None
        timestamp, value = entry
        if time.time() - timestamp > self._ttl:
            self._store.pop(k, None)
            return None
        return value

    def set(self, title: str, abstract: str, top_n: int, idioma: str, value):
        k = self._key(title, abstract, top_n, idioma)
        self._store[k] = (time.time(), value)

    def clear(self):
        self._store.clear()


recommendation_cache = RecommendationCache(ttl_seconds=86400)

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

# --- 1. CONFIGURAÇÃO ÚNICA DA P GINA (Executada antes de qualquer comando Streamlit) ---
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
    page_title="O Portal do Pesquisador",
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

# --- 2. SISTEMA DE TRADUÇÃO MULTIL NGUE ---
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Português"

# Seletor de idioma fixado na barra lateral
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.session_state.idioma = st.sidebar.selectbox(
    "  Language / Idioma:",
    ["English", "Español", "Português"], index=0
)

# --- BOTÃO DE CONTATO (GLOBAL) ---
_lang = st.session_state.get('idioma', 'Português')
_btn_contato_text = "✉️ Fale conosco"
if _lang == 'English':
    _btn_contato_text = "✉️ Contact Us"
elif _lang == 'Español':
    _btn_contato_text = "✉️ Contáctenos"

st.sidebar.markdown(
    f"""
    <a href="mailto:support@scipubs.com" style="text-decoration: none;">
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
            margin-top: 15px;
        " onmouseover="this.style.backgroundColor='#cc2222'" onmouseout="this.style.backgroundColor='#FF2B2B'">
            {_btn_contato_text}
        </button>
    </a>
    """,
    unsafe_allow_html=True
)


dic = {
    "Português": {
        "titulo": "O Portal do Pesquisador",
        "subtitulo": "A ciência aberta importa. Sem perguntas. Sem taxas. Sem anúncios. Apenas use.",
        "filtros_tit": "####   Buscador de Periódicos",
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
        "m_sjr": "SJR Score  pice",
        "cat_tit": "#### 📋 Catálogo de Periódicos",
        "exibir_pag": "Exibir por página:",
        "pag_lbl": "Página",
        "exportar_btn": "📥 Exportar apenas esta página",
        "aviso_nada": "Nenhum periódico atende aos critérios aplicados.",
        "nav_tit": "Painel de Navegação",
        "todas": "Todas",
        "col_h5": " Índice h5 (Scholar)",
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
        "busca_cat": "  Catálogo de Periódicos",
        "busca_ia": "   Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendação Temática com Inteligência Artificial",
        "ia_subtitulo": "Cole o título e o resumo (abstract) do seu artigo. A IA analisa o conteúdo e indica os periódicos mais adequados, com métricas enriquecidas.",
        "ia_campo_titulo": "Título do Artigo",
        "ia_campo_resumo": "Resumo / Abstract (Suporta Português, Inglês ou Espanhol)",
        "ia_motor_tit": "Motor de IA",
        "ia_motor_desc": "Recomendações via IA generativa — Gemini (nuvem) ou Ollama (local, 100% gratuito).",
        "ia_ollama_ok": "Ollama detectado e pronto para uso.",
        "ia_ollama_off": "Ollama não detectado. Será usado o algoritmo local de relevância temática.",
        "ia_num_rec": "Quantidade de recomendações desejadas (máx. 20)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "Analisando seu artigo e cruzando com catálogo e bases acadêmicas...",
        "ia_sucesso": "Recomendações geradas com sucesso!",
        "ia_erro": "Erro ao processar a recomendação. Tente novamente em instantes.",
        "ia_fallback_local": "Resultado gerado pelo algoritmo local de relevância temática (Ollama indisponível).",
        "ia_artigos_similares": "Artigos semanticamente similares",
        "ia_artigos_similares_hint": "Referências publicadas com temática próxima ao seu resumo (OpenAlex).",
        "ia_aderencia_escopo": "Aderência ao Escopo",
        "ia_probabilidade": "Probabilidade Estimada de Aceitação",
        "ia_probabilidade_nota": "Estimativa baseada em aderência temática, prestígio da revista e artigos similares publicados.",
        "ia_justificativa_tit": "Por que esta revista foi recomendada",
        "ia_classificacao_area": "Classificação CAPES do artigo",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_aderencia": "Grau de Aderência:",
        "ia_card_site": "  Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponível na base",
        "filtro_area": "Grande Área",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "🔑 IA Motor",
        "ia_como_obter_titulo": "ℹ  Sobre os modos de IA",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
1. A IA analisa semanticamente seu título e resumo<br>
2. Cruza com o catálogo local e bases acadêmicas (OpenAlex)<br>
3. Retorna recomendações com métricas enriquecidas<br>
4. Para obter resultados mais ágeis, você pode inserir uma chave API do Gemini AI; o passo a passo para a obtenção gratuita é explicado abaixo.<br>
5. Caso não tenha ou não queira usar essa opção, você poderá realizar a busca deixando em branco essa janela e usando o Ollama (Llama 3) como IA.
</div>
        """,
        "ia_refinar_pesquisa": "🎯 Refinar Pesquisa",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### Bem-vindo(a) ao SciPubs!",
        "reg_apresentacao": "Esta é uma plataforma científica de alta tecnologia projetada para simplificar a busca e a seleção de periódicos de impacto para sua publicação. Una forças com ciência de dados e IA.",
        "reg_beneficios_tit": "✨ Por que usar o SciPubs?",
        "reg_beneficio_1_tit": "  Busca Tradicional",
        "reg_beneficio_1_desc": "Filtros por CNPq, Indexadores (Scopus, Web of Science, SciELO, Educ@) e métricas consolidadas.",
        "reg_beneficio_2_tit": "📊 Métricas Unificadas",
        "reg_beneficio_2_desc": "Quartis JCR/SJR, H-Index e atalhos de impacto no Scholar ao seu alcance.",
        "reg_beneficio_3_tit": "   Recomendador IA",
        "reg_beneficio_3_desc": "Recomendador generativo via Ollama (Llama 3) cruzado com catálogo local e OpenAlex.",
        "reg_formulario_tit": "  Registro de Acesso Acadêmico",
        "reg_formulario_desc": "O acesso ao portal é gratuito e aberto a toda a comunidade científica (de estudantes de graduação a pós-doutores). Preencha o cadastro abaixo para liberar o acesso.",
        "reg_nome": "Nome Completo:",
        "reg_email": "E-mail Acadêmico ou Pessoal:",
        "reg_escolaridade": "Titulação:",
        "reg_instituicao": "Instituição de Vínculo:",
        "reg_inst_outra": "Especifique sua Instituição:",
        "reg_area_interesse": "Grande Área de Interesse (Predominante):",
        "reg_btn_enviar": "Registrar e Acessar o Buscador ➔",
        "reg_sucesso": "🎉 Registro concluído com sucesso! Bem-vindo(a) ao SciPubs: O Portal do Pesquisador.",
        "reg_erro_campos": "    Por favor, preencha todos os campos obrigatórios.",
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
        "rec_btn_verificar": "Verificar Informações ➔",
        "rec_btn_redefinir": "Redefinir Senha",
        "rec_nova_senha": "Nova Senha:",
        "rec_conf_senha": "Confirmar Nova Senha:",
        "rec_sucesso": "🎉 Senha redefinida com sucesso! Faça login.",
        "rec_erro_nao_encontrado": "    E-mail não encontrado em nossos registros.",
        "rec_btn_voltar": "Voltar para o Login",
        "log_btn_google": "Conectar com o Google",
        "log_cadastrar_link": "Não tem uma conta? Cadastre-se aqui!",
        "log_entrar_link": "Já tem uma conta? Faça login aqui!",
        "log_titulo": "🔒 Entrar no SciPubs",
        "reg_titulo_form": "  Criar Conta Acadêmica",
        "reg_nome_sobrenome": "Nome e Sobrenome:",
        "reg_pais": "País:",
        "reg_telefone": "Telefone:",
        "reg_senha": "Senha:",
        "reg_confirmar_senha": "Confirmar Senha:",
        "reg_btn_cadastrar": "Criar Conta e Acessar ➔",
        "reg_erro_senha_diferente": "    As senhas digitadas não coincidem.",
        "reg_erro_ja_existe": "    Este e-mail já está cadastrado. Faça login.",
        "log_erro_invalido": "    E-mail ou senha incorretos.",
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
        "subtitulo": "Open science matters. No asks. No fees. No ads. Just use.",
        "filtros_tit": "####   Journal Finder",
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
        "gov_tit": "GOVERNMENT WEBSITES",
        "inst_tit": "INSTITUTIONAL INFORMATION",
        "pessoal_lbl": "👤 Personal website",
        "indexadores_tit": "INDEXERS",
        "repositorios_tit": "DIRECTORIES",
        "ia_tit": "ACADEMIC AI",
        "btn_desktop": "💻 Download Windows Version",
        "busca_cat": "  Journal Catalog",
        "busca_ia": "   Smart Recommender (AI)",
        "ia_titulo": "Thematic Recommendation with Artificial Intelligence",
        "ia_subtitulo": "Paste your article title and abstract. The AI analyzes your content and suggests the best-matching journals with enriched metrics.",
        "ia_campo_titulo": "Article Title",
        "ia_campo_resumo": "Abstract (Supports Portuguese, English, or Spanish)",
        "ia_motor_tit": "AI Engine",
        "ia_motor_desc": "Recommendations via generative AI — Gemini (cloud) or Ollama (local, 100% free).",
        "ia_ollama_ok": "Ollama detected and ready.",
        "ia_ollama_off": "Ollama not detected. The local thematic relevance algorithm will be used.",
        "ia_num_rec": "Number of desired recommendations (max. 20)",
        "ia_btn_buscar": "Analyze and Recommend",
        "ia_analisando": "Analyzing your article and cross-referencing catalog and academic databases...",
        "ia_sucesso": "Recommendations generated successfully!",
        "ia_erro": "Error processing the recommendation. Please try again shortly.",
        "ia_fallback_local": "Result generated by the local thematic relevance algorithm (Ollama unavailable).",
        "ia_artigos_similares": "Semantically similar articles",
        "ia_artigos_similares_hint": "Published references with themes close to your abstract (OpenAlex).",
        "ia_aderencia_escopo": "Scope Adherence",
        "ia_probabilidade": "Estimated Acceptance Probability",
        "ia_probabilidade_nota": "Estimate based on thematic fit, journal prestige, and similar published articles.",
        "ia_justificativa_tit": "Why this journal was recommended",
        "ia_classificacao_area": "CAPES classification of the article",
        "ia_card_motivo": "Why publish here:",
        "ia_card_aderencia": "Adherence Score:",
        "ia_card_site": "  Visit Official Homepage",
        "ia_card_sem_site": "Website not available in database",
        "filtro_area": "Broad Area",
        "filtro_indexador": "Indexer",
        "ia_credencial_tit": "🔑 AI Engine",
        "ia_como_obter_titulo": "ℹ  About AI modes",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
1. AI semantically analyzes your title and abstract<br>
2. Cross-references with local catalog and academic databases (OpenAlex)<br>
3. Returns enriched recommendations with metrics<br>
4. For faster results, you can insert a Gemini AI API key; the step-by-step guide to obtain it for free is explained below.<br>
5. If you don't have or don't want to use this option, you can run the search leaving this field blank and using Ollama (Llama 3) as the AI.
</div>
        """,
        "ia_refinar_pesquisa": "🎯 Refine Targets",
        "ia_todos": "All",
        "reg_boas_vindas": "### Welcome to the SciPubs: The Researcher's Portal!",
        "reg_apresentacao": "This is a high-tech scientific platform designed to simplify the search and selection of high-impact journals for your publication. Join forces with data science and AI.",
        "reg_beneficios_tit": "✨ Why use SciPubs?",
        "reg_beneficio_1_tit": "  Traditional Search",
        "reg_beneficio_1_desc": "Filters by CNPq subareas, indexers (Scopus, Web of Science, SciELO, Educ@), and consolidated metrics.",
        "reg_beneficio_2_tit": "📊 Unified Metrics",
        "reg_beneficio_2_desc": "JCR/SJR quartiles, H-Index, and impact shortcuts on Google Scholar at your fingertips.",
        "reg_beneficio_3_tit": "   AI Recommender",
        "reg_beneficio_3_desc": "Generative recommendations via Ollama (Llama 3) crossed with local catalog and OpenAlex.",
        "reg_formulario_tit": "  Academic Access Registration",
        "reg_formulario_desc": "Access to the portal is free and open to the entire scientific community (from undergraduate students to postdocs). Fill out the form below to unlock access.",
        "reg_nome": "Full Name:",
        "reg_email": "Academic or Personal Email:",
        "reg_escolaridade": "Degree:",
        "reg_instituicao": "Affiliated Institution:",
        "reg_inst_outra": "Specify your Institution:",
        "reg_area_interesse": "Major Research Area of Interest:",
        "reg_btn_enviar": "Register and Access the Finder ➔",
        "reg_sucesso": "🎉 Registration completed successfully! Welcome to the SciPubs: The Researcher's Portal.",
        "reg_erro_campos": "    Please fill in all required fields.",
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
        "rec_btn_verificar": "Verify Information ➔",
        "rec_btn_redefinir": "Reset Password",
        "rec_nova_senha": "New Password:",
        "rec_conf_senha": "Confirm New Password:",
        "rec_sucesso": "🎉 Password reset successfully! Please log in.",
        "rec_erro_nao_encontrado": "    E-mail not found in our records.",
        "rec_btn_voltar": "Back to Login",
        "log_btn_google": "Sign in with Google",
        "log_cadastrar_link": "Don't have an account? Sign up here!",
        "log_entrar_link": "Already have an account? Log in here!",
        "log_titulo": "🔒 Log in to SciPubs",
        "reg_titulo_form": "  Create Academic Account",
        "reg_nome_sobrenome": "First and Last Name:",
        "reg_pais": "Country:",
	"reg_idade": "Date of Birth",
	"reg_sexo": "Sex",
        "reg_raca": "Race/Ethnicity",
        "reg_telefone": "Phone:",
        "reg_senha": "Password:",
        "reg_confirmar_senha": "Confirm Password:",
        "reg_btn_cadastrar": "Create Account and Access ➔",
        "reg_erro_senha_diferente": "    Passwords do not match.",
        "reg_erro_ja_existe": "    This email is already registered. Please log in.",
        "log_erro_invalido": "    Incorrect email or password.",
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
        "titulo": "El Portal del Investigador",
        "subtitulo": "La ciencia abierta importa. Sin registros. Sin pagos. Sin anuncios. Solo úsala.",
        "filtros_tit": "####   Buscador de Revistas",
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
        "m_sjr": "SJR Score  pice",
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
        "gov_tit": "SITIOS DEL GOBIERNO",
        "inst_tit": "INFORMACIÓN INSTITUCIONAL",
        "pessoal_lbl": "👤 Sitio personal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "DIRECTORIOS",
        "ia_tit": "IA ACADÉMICA",
        "btn_desktop": "💻 Descargar Versión para Windows",
        "busca_cat": "  Catálogo de Revistas",
        "busca_ia": "   Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendación Temática con Inteligencia Artificial",
        "ia_subtitulo": "Pegue el título y el resumen (abstract) de su artículo. La IA analiza el contenido e indica las revistas más adecuadas, con métricas enriquecidas.",
        "ia_campo_titulo": "Título del Artículo",
        "ia_campo_resumo": "Resumen / Abstract (Soporta Portugués, Inglés o Español)",
        "ia_motor_tit": "Motor de IA",
        "ia_motor_desc": "Recomendaciones vía IA generativa — Gemini (nube) u Ollama (local, 100% gratuito).",
        "ia_ollama_ok": "Ollama detectado y listo para usar.",
        "ia_ollama_off": "Ollama no detectado. Se usará el algoritmo local de relevancia temática.",
        "ia_num_rec": "Cantidad de recomendaciones deseadas (máx. 20)",
        "ia_btn_buscar": "Analar y Recomendar",
        "ia_analisando": "Analizando su artículo y cruzando con catálogo y bases académicas...",
        "ia_sucesso": "¡Recomendaciones generadas con éxito!",
        "ia_erro": "Error al procesar la recomendación. Inténtelo de nuevo en unos instantes.",
        "ia_fallback_local": "Resultado generado por el algoritmo local de relevancia temática (Ollama no disponible).",
        "ia_artigos_similares": "Artículos semánticamente similares",
        "ia_artigos_similares_hint": "Referencias publicadas con temática próxima a su resumen (OpenAlex).",
        "ia_aderencia_escopo": "Adherencia al Alcance",
        "ia_probabilidade": "Probabilidad Estimada de Aceptación",
        "ia_probabilidade_nota": "Estimación basada en adherencia temática, prestigio de la revista y artículos similares publicados.",
        "ia_justificativa_tit": "Por qué se recomendó esta revista",
        "ia_classificacao_area": "Clasificación CAPES del artículo",
        "ia_card_motivo": "Por qué publicar aqui:",
        "ia_card_aderencia": "Grado de Adherencia:",
        "ia_card_site": "  Visitar Homepage Oficial",
        "ia_card_sem_site": "Sitio no disponible en la base",
        "filtro_area": "Gran  rea",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "🔑 Motor IA",
        "ia_como_obter_titulo": "ℹ  Sobre los modos de IA",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
1. La IA analiza semánticamente su título y resumen<br>
2. Cruza con el catálogo local y bases académicas (OpenAlex)<br>
3. Retorna recomendaciones con métricas enriquecidas<br>
4. Para obtener resultados más ágiles, puede insertar una clave API de Gemini AI; el paso a paso para obtenerla gratuitamente se explica a continuación.<br>
5. Si no tiene o no desea usar esta opción, puede realizar la búsqueda dejando en blanco esta ventana y usando Ollama (Llama 3) como IA.
</div>
        """,
        "ia_refinar_pesquisa": "🎯 Refinar Búsqueda",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### ¡Bienvenido a SciPubs: El Portal del Investigador!",
        "reg_apresentacao": "Esta es una plataforma científica de alta tecnología diseñada para simplificar la búsqueda y selección de revistas de impacto para su publicación. Una fuerzas con ciencia de datos e IA.",
        "reg_beneficios_tit": "✨ ¿Por qué usar SciPubs?",
        "reg_beneficio_1_tit": "  Búsqueda Tradicional",
        "reg_beneficio_1_desc": "Filtros por subáreas del CNPq, indexadores (Scopus, Web of Science, SciELO, Educ@) y métricas consolidadas.",
        "reg_beneficio_2_tit": "📊 Métricas Unificadas",
        "reg_beneficio_2_desc": "Cuartiles JCR/SJR, H-Index y accesos directos de impacto en Scholar a su alcance.",
        "reg_beneficio_3_tit": "   Recomendador IA",
        "reg_beneficio_3_desc": "Recomendaciones generativas vía Ollama (Llama 3) cruzadas con catálogo local y OpenAlex.",
        "reg_formulario_tit": "  Registro de Acceso Académico",
        "reg_formulario_desc": "El acceso al portal es gratuito y abierto a toda la comunidad científica (desde estudiantes hasta posdoctores). Complete el formulario a continuación para liberar el acceso.",
        "reg_nome": "Nombre Completo:",
        "reg_email": "Correo Electrónico Académico o Personal:",
        "reg_escolaridade": "Titulación:",
        "reg_instituicao": "Institución de Vínculo:",
        "reg_inst_outra": "Especifique su Institución:",
	"reg_idade": "Fecha de Nacimiento",
	"reg_sexo": "Sexo",
        "reg_raca": "Raza/Etnía",
        "reg_area_interesse": "Gran Area de Interés Predominante:",
        "reg_btn_enviar": "Registrarse y Acceder al Buscador ➔",
        "reg_sucesso": "🎉 ¡Registro completado con éxito! Bienvenido a SciPubs: El Portal del Investigador.",
        "reg_erro_campos": "    Por favor, complete todos los campos obligatorios.",
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
        "rec_btn_verificar": "Verificar Información ➔",
        "rec_btn_redefinir": "Restablecer Contraseña",
        "rec_nova_senha": "Nueva Contraseña:",
        "rec_conf_senha": "Confirmar Nueva Contraseña:",
        "rec_sucesso": "🎉 ¡Contraseña restablecida con éxito! Inicie sesión.",
        "rec_erro_nao_encontrado": "    Correo electrónico no encontrado en nuestros registros.",
        "rec_btn_voltar": "Volver al Inicio",
        "log_btn_google": "Conectar con Google",
        "log_cadastrar_link": "¿No tienes una cuenta? ¡Regístrate aquí!",
        "log_entrar_link": "¿Ya tienes una cuenta? ¡Inicia sesión aquí!",
        "log_titulo": "🔒 Iniciar Sesión en SciPubs",
        "reg_titulo_form": "  Crear Cuenta Académica",
        "reg_nome_sobrenome": "Nombre y Apellido:",
        "reg_pais": "País:",
        "reg_telefone": "Teléfono:",
        "reg_senha": "Contraseña:",
        "reg_confirmar_senha": "Confirmar Contraseña:",
        "reg_btn_cadastrar": "Crear Cuenta y Acceder ➔",
        "reg_erro_senha_diferente": "    Las contraseñas no coinciden.",
        "reg_erro_ja_existe": "    Este correo ya está registrado. Inicie sesión.",
        "log_erro_invalido": "    Correo o contraseña incorrectos.",
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

    /* =========================================
       📱 DESIGN MOBILE (UX/UI PREMIUM RESPONSIVO)
       ========================================= */
    @media (max-width: 768px) {
        /* 1. Header (Hero) Redesenhado para Celular */
        .premium-hero {
            text-align: center !important;
            padding: 12px 10px !important;
            margin-bottom: 15px !important;
            border-left: none !important;
            border-top: 5px solid #FF2B2B !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 15px !important;
        }
        
        .premium-hero img {
            display: block !important;
            max-width: 240px !important; /* Logo em tamanho harmônico */
            margin: 0 auto !important;
            margin-bottom: 10px !important;
        }
        
        .premium-title {
            font-size: 1.5rem !important; /* Texto cabendo em telas finas */
            line-height: 1.1 !important;
            margin-bottom: 8px !important;
            text-align: center !important;
        }
        
            .premium-subtitle {
        color: #FFD700 !important; /* Amarelo Dourado */
        font-size: 0.8rem !important; /* Fonte pequena */
        text-shadow: 1px 1px 0px #b39700, 2px 2px 0px #806b00, 3px 3px 4px rgba(0,0,0,0.6) !important; /* Efeito 3D */
        max-width: 280px; /* Força quebra em duas linhas */
        margin: 0 auto !important; /* Centraliza */
        line-height: 1.4;
        margin-top: 5px !important;
    }
        
        .premium-text-block {
            align-items: center !important;
        }

        /* 2. Redução de Espaços e Margens Brancas do Streamlit */
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* 3. Cards de Métricas em Coluna */
        div[data-testid="stMetric"] {
            padding: 18px 15px !important;
            margin-bottom: 5px !important;
            text-align: center !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
        }

        /* 4. Tabelas Inteligentes (Rolagem horizontal confinada) */
        div[data-testid="stDataFrame"] {
            overflow-x: auto !important;
            width: 100% !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        }
        
        /* 5. Inputs Touch-Friendly (Gordos) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            height: 50px !important;
            font-size: 16px !important; /* 16px evita o zoom automático no iOS */
        }
        
        /* 6. Botões Arredondados e Full Width no Sidebar e Menu */
        .btn-custom-menu {
            justify-content: center !important;
            padding: 14px !important;
            border-radius: 25px !important; /* Estilo pílula */
            font-size: 1.05rem !important;
        }
        
        button[data-baseweb="tab"] {
            padding: 10px 12px !important;
            font-size: 0.85rem !important;
        }
    }
    
    /* Telas Muito Pequenas (iPhone SE) */
    @media (max-width: 480px) {
        .premium-title { font-size: 1.8rem !important; }
        .premium-subtitle { font-size: 1rem !important; }
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
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        border-left: 6px solid #FF2B2B;
    }
    .premium-title {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin-bottom: 10px !important;
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
            
            # Renomeia as colunas do CSV para garantir a acentuação correta utilizada no código
            df = df.rename(columns={
                "Grande Area": "Grande Área",
                "Grande Area": "Grande Área",
                "Area do Conhecimento": "Área do Conhecimento",
                "Area do Conhecimento": "Área do Conhecimento",
                "Subarea do Conhecimento": "Subárea do Conhecimento",
                "Subarea do Conhecimento": "Subárea do Conhecimento",
                "Título da Revista": "Título da Revista",
                "Título da Revista": "Título da Revista",
                "Índice h5": "Índice h5"
            })

            
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
            st.error(f"    Erro ao processar a base de dados '{nome_arquivo}'. Detalhes: {e}")
            st.stop()
    else:
        st.error("    Base de dados não encontrada. O arquivo 'dados.csv' não foi localizado na raiz do projeto. Por favor, certifique-se de fazer o download do arquivo no repositório GitHub correspondente.")
        st.stop()

df_original, arquivo_usado = carregar_dados()

cache_manager = get_cache_manager()
try:
    anonymous_logger = get_anonymous_logger()
except Exception:
    anonymous_logger = None

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

# Botão de Configurações
btn_conf_text = "⚙ Configs"
btn_conf_help = "Configurações"
if st.session_state.get("idioma", "English") == "English":
    btn_conf_text = "⚙ Settings"
    btn_conf_help = "Settings"
elif st.session_state.get("idioma", "English") == "Español":
    btn_conf_text = "⚙ Config."
    btn_conf_help = "Configuración"

# if st.sidebar.button(btn_conf_text, key="btn_config_gear_sidebar", help=btn_conf_help, use_container_width=True):
#     st.session_state.abrir_configuracoes = not st.session_state.get("abrir_configuracoes", False)
#     st.rerun()

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
        <span style='color: #A91D22;'> </span> <b>{t['meta_sistema']}:</b> {t['meta_status']}<br>
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
if imagem_base64:
    tag_imagem = f'<img src="data:image/png;base64,{imagem_base64}" style="height: 220px; width: auto; object-fit: contain;">'
else:
    tag_imagem = '<span class="emoji-logo" style="font-size: 6.5rem; line-height: 1; margin-right: 15px;">📚</span>'

st.markdown(f'''<div class="premium-hero" style="display: flex; align-items: center; flex-wrap: nowrap; gap: 30px; padding: 25px 35px;">
{tag_imagem}
<div class="divider-line" style="width: 2px; height: 140px; background-color: rgba(255,255,255,0.15);"></div>
<div class="premium-text-block">
<h1 class="premium-title" style="margin: 0 !important; padding: 0 !important; font-size: 2.3rem !important; font-weight: 800 !important; letter-spacing: -0.5px;">{t['titulo']}</h1>
<p class="premium-subtitle" style="margin: 5px 0 0 0 !important; padding: 0 !important; font-size: 1.1rem !important; opacity: 0.85;">{t['subtitulo']}</p>
</div>
</div>''', unsafe_allow_html=True)



# Textos informativos traduzidos

# --- TELA DE CONFIGURAÇÕES & AJUSTES ---
if st.session_state.get("abrir_configuracoes", False):
    lang = st.session_state.get('idioma', 'Português')

    # Dicionário de traduções da página
    ts = {
        'titulo': "## ⚙ Configurações & Ajustes do SciPubs",
        'btn_voltar': "⬅ Voltar para o Buscador",
        'lbl_opcoes': "Selecione uma opção de ajuste:",
        'opc_cad': "👤 Atualização de Cadastro",
        'opc_senha': "🔑 Atualização de Senha",
        'opc_tema': "🎨 Tema da Plataforma (Claro/Escuro)",
        'opc_comp': "📢 Compartilhar o SciPubs",
        
        # Cadastro
        'sub_cad': "👤 Atualizar Meus Dados de Cadastro",
        'lbl_nome': "Nome Completo:",
        'lbl_tel': "Telefone:",
        'lbl_esc': "Escolaridade:",
        'lbl_inst': "Instituição de Vínculo:",
        'btn_salvar_cad': "Salvar Alterações do Cadastro",
        'err_campos': "Preencha todos os campos obrigatórios.",
        'suc_cad': "🎉 Dados do cadastro atualizados com sucesso!",
        'esc_opts': ["Estudante de Graduação", "Especialista / Pós-Graduado", "Mestrando", "Mestre", "Doutorando", "Doutor", "Pós-Doutor", "Outro"],
        
        # Senha
        'sub_senha': "🔑 Alterar Minha Senha de Acesso",
        'lbl_nova': "Nova Senha:",
        'lbl_conf': "Confirmar Nova Senha:",
        'btn_salvar_senha': "Atualizar Senha",
        'err_senha_branca': "A senha não pode estar em branco.",
        'err_senha_diff': "As senhas digitadas são diferentes.",
        'suc_senha': "🎉 Senha alterada com sucesso!",
        
        # Tema
        'sub_tema': "🎨 Estilo e Aparência da Plataforma",
        'tema_escuro': "Modo Noturno (Escuro)",
        'tema_claro': "Modo Diurno (Claro)",
        'lbl_tema_ativo': "O tema ativo atualmente é: **{tema}**",
        'btn_claro': "Ativar Modo Diurno (Claro)",
        'btn_escuro': "Ativar Modo Noturno (Escuro)",
        
        # Compartilhar
        'sub_comp': "📢 Compartilhar o SciPubs",
        'txt_comp': "Confira o Buscador de Periódicos Científicos do PPGE UFOP: ",
        'lbl_forma': "Escolha uma das formas abaixo para divulgar o portal:",
        'btn_copiar': "📋 Copiar Link",
        'suc_copiar': "Link copiado para exibição!"
    }

    if st.session_state.get("idioma", "English") == "English":
        ts['titulo'] = "## ⚙ SciPubs Settings & Adjustments"
        ts['btn_voltar'] = "⬅ Back to Search Engine"
        ts['lbl_opcoes'] = "Select an adjustment option:"
        ts['opc_cad'] = "👤 Update Profile"
        ts['opc_senha'] = "🔑 Update Password"
        ts['opc_tema'] = "🎨 Platform Theme (Light/Dark)"
        ts['opc_comp'] = "📢 Share SciPubs"
        ts['sub_cad'] = "👤 Update My Profile Data"
        ts['lbl_nome'] = "Full Name:"
        ts['lbl_tel'] = "Phone:"
        ts['lbl_esc'] = "Education Level:"
        ts['lbl_inst'] = "Institution:"
        ts['btn_salvar_cad'] = "Save Profile Changes"
        ts['err_campos'] = "Please fill in all required fields."
        ts['suc_cad'] = "🎉 Profile updated successfully!"
        ts['esc_opts'] = ["Undergraduate Student", "Specialist / Post-Graduate", "Master's Student", "Master", "PhD Student", "PhD", "Post-Doc", "Other"]
        ts['sub_senha'] = "🔑 Change My Password"
        ts['lbl_nova'] = "New Password:"
        ts['lbl_conf'] = "Confirm New Password:"
        ts['btn_salvar_senha'] = "Update Password"
        ts['err_senha_branca'] = "Password cannot be blank."
        ts['err_senha_diff'] = "Passwords do not match."
        ts['suc_senha'] = "🎉 Password changed successfully!"
        ts['sub_tema'] = "🎨 Platform Style and Appearance"
        ts['tema_escuro'] = "Dark Mode"
        ts['tema_claro'] = "Light Mode"
        ts['lbl_tema_ativo'] = "Current active theme: **{tema}**"
        ts['btn_claro'] = "Activate Light Mode"
        ts['btn_escuro'] = "Activate Dark Mode"
        ts['sub_comp'] = "📢 Share SciPubs"
        ts['txt_comp'] = "Check out the Scientific Journals Search Engine of PPGE UFOP: "
        ts['lbl_forma'] = "Choose one of the ways below to share the portal:"
        ts['btn_copiar'] = "📋 Copy Link"
        ts['suc_copiar'] = "Link copied to clipboard!"
    elif st.session_state.get("idioma", "English") == "Español":
        ts['titulo'] = "## ⚙ Configuración y Ajustes de SciPubs"
        ts['btn_voltar'] = "⬅ Volver al Buscador"
        ts['lbl_opcoes'] = "Seleccione una opción de ajuste:"
        ts['opc_cad'] = "👤 Actualizar Perfil"
        ts['opc_senha'] = "🔑 Actualizar Contraseña"
        ts['opc_tema'] = "🎨 Tema de la Plataforma (Claro/Oscuro)"
        ts['opc_comp'] = "📢 Compartir SciPubs"
        ts['sub_cad'] = "👤 Actualizar Mis Datos de Perfil"
        ts['lbl_nome'] = "Nombre Completo:"
        ts['lbl_tel'] = "Teléfono:"
        ts['lbl_esc'] = "Nivel de Educación:"
        ts['lbl_inst'] = "Institución:"
        ts['btn_salvar_cad'] = "Guardar Cambios del Perfil"
        ts['err_campos'] = "Complete todos los campos obligatorios."
        ts['suc_cad'] = "🎉 ¡Datos del perfil actualizados con éxito!"
        ts['esc_opts'] = ["Estudiante de Grado", "Especialista / Postgrado", "Estudiante de Maestría", "Magíster", "Estudiante de Doctorado", "Doctor", "Post-Doctor", "Otro"]
        ts['sub_senha'] = "🔑 Cambiar Mi Contraseña"
        ts['lbl_nova'] = "Nueva Contraseña:"
        ts['lbl_conf'] = "Confirmar Nueva Contraseña:"
        ts['btn_salvar_senha'] = "Actualizar Contraseña"
        ts['err_senha_branca'] = "La contraseña no puede estar en blanco."
        ts['err_senha_diff'] = "Las contraseñas no coinciden."
        ts['suc_senha'] = "🎉 ¡Contraseña cambiada con éxito!"
        ts['sub_tema'] = "🎨 Estilo y Apariencia de la Plataforma"
        ts['tema_escuro'] = "Modo Oscuro"
        ts['tema_claro'] = "Modo Claro"
        ts['lbl_tema_ativo'] = "El tema activo actualmente es: **{tema}**"
        ts['btn_claro'] = "Activar Modo Claro"
        ts['btn_escuro'] = "Activar Modo Oscuro"
        ts['sub_comp'] = "📢 Compartir SciPubs"
        ts['txt_comp'] = "Conoce el Buscador de Revistas Científicas de PPGE UFOP: "
        ts['lbl_forma'] = "Elija una de las siguientes formas para compartir el portal:"
        ts['btn_copiar'] = "📋 Copiar Enlace"
        ts['suc_copiar'] = "¡Enlace copiado al portapapeles!"

    st.markdown(ts['titulo'])

    if st.button(ts['btn_voltar'], key="btn_fechar_config"):
        st.session_state.abrir_configuracoes = False
        st.rerun()

    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    opc_config = st.radio(
        ts['lbl_opcoes'],
        [ts['opc_cad'], ts['opc_senha'], ts['opc_tema'], ts['opc_comp']],
        key="radio_opc_config"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if ts['opc_cad'] in opc_config:
        st.subheader(ts['sub_cad'])
        email_atual = st.session_state.email_usuario
        nome_atual = st.session_state.get("nome_usuario", "")

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

        nome_edit = st.text_input(ts['lbl_nome'], value=nome_atual)
        tel_edit = st.text_input(ts['lbl_tel'], value=telefone_atual)

        opcoes_esc_edit = ts['esc_opts']
        if escolaridade_atual not in opcoes_esc_edit:
            opcoes_esc_edit.append(escolaridade_atual)
        esc_edit = st.selectbox(ts['lbl_esc'], opcoes_esc_edit, index=opcoes_esc_edit.index(escolaridade_atual))

        inst_edit = st.text_input(ts['lbl_inst'], value=inst_atual)

        if st.button(ts['btn_salvar_cad'], type="primary"):
            if not nome_edit.strip() or not tel_edit.strip() or not inst_edit.strip():
                st.error("    " + ts['err_campos'])
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
                st.success(ts['suc_cad'])
                time.sleep(1.2)
                st.rerun()

    elif ts['opc_senha'] in opc_config:
        st.subheader(ts['sub_senha'])
        nova_s = st.text_input(ts['lbl_nova'], type="password", key="settings_nova_senha")
        conf_s = st.text_input(ts['lbl_conf'], type="password", key="settings_conf_senha")
        if st.button(ts['btn_salvar_senha'], type="primary"):
            if not nova_s.strip():
                st.error("    " + ts['err_senha_branca'])
            elif nova_s != conf_s:
                st.error("    " + ts['err_senha_diff'])
            else:
                redefinir_senha_usuario(st.session_state.email_usuario, nova_s)
                st.success(ts['suc_senha'])
                time.sleep(1.2)
                st.rerun()

    elif ts['opc_tema'] in opc_config:
        st.subheader(ts['sub_tema'])
        tema_atual = ts['tema_escuro'] if st.session_state.get("dark_mode", False) else ts['tema_claro']
        st.info(ts['lbl_tema_ativo'].format(tema=tema_atual))

        if st.session_state.get("dark_mode", False):
            if st.button(ts['btn_claro'], type="primary"):
                st.session_state.dark_mode = False
                st.rerun()
        else:
            if st.button(ts['btn_escuro'], type="primary"):
                st.session_state.dark_mode = True
                st.rerun()

    elif ts['opc_comp'] in opc_config:
        st.subheader(ts['sub_comp'])
        url_portal = "https://www.scipubs.com/"
        texto_compartilhar = f"{ts['txt_comp']}{url_portal}"

        msg_encoded = urllib.parse.quote(texto_compartilhar)
        link_wa = f"https://api.whatsapp.com/send?text={msg_encoded}"
        link_mail = f"mailto:?subject=SciPubs&body={msg_encoded}"

        st.write(ts['lbl_forma'])
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(f"[💬 WhatsApp]({link_wa})", unsafe_allow_html=True)
        with col_c2:
            st.markdown(f"[✉ E-mail]({link_mail})", unsafe_allow_html=True)
        with col_c3:
            if st.button(ts['btn_copiar']):
                st.info(f"Link: `{url_portal}`")
                st.success(ts['suc_copiar'])

    st.stop()

# Textos informativos traduzidos
if st.session_state.idioma == "Português":
    expander_titulo = "💡 Sobre o SciPubs & Como Utilizar"
    sobre_texto = """
### Bem-vindo(a) ao SciPubs: O Portal do Pesquisador!
Esta é uma ferramenta desenvolvida para otimizar a busca por periódicos científicos de alto impacto.
  
####     O que você pode fazer aqui?
1. **Busca Avançada & Booleana:** Pesquise por termos exatos utilizando aspas (ex: `"educação musical"`) ou combine múltiplos critérios usando os operadores lógicos `AND`, `OR` e `NOT` (ex: `music AND education NOT medicine`).
2. **Filtros por Subárea (CNPq):** Encontre periódicos perfeitamente alinhados    sua subárea específica de atuação e conhecimento.
3. **Métricas de Impacto:** Analise o prestígio internacional através de quartis e indicadores consolidados das bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** e o link direto para o **Índice h5 (Google Scholar)**.
4. **Recomendação Inteligente (IA):** Use a inteligência artificial do Google Gemini para colar o título e resumo do seu artigo e obter as recomendações de periódicos ideais com justificativa e link direto.
5. **Exportação de Dados:** Filtre os resultados de acordo com sua necessidade e faça o download da tabela customizada imediatamente.
"""
elif st.session_state.idioma == "English":
    expander_titulo = "💡 About SciPubs & How to Use"
    sobre_texto = """
### Welcome to SciPubs: the Researcher's Portal!
This is a tool developed to optimize the search for high-impact scientific journals.
 
####     What can you do here?
1. **Advanced & Boolean Search:** Search for exact phrases using quotation marks (e.g., `"music education"`) or combine multiple criteria using the logical operators `AND`, `OR`, and `NOT` (e.g., `music AND education NOT medicine`).
2. **Filters by Subarea (CNPq):** Find journals perfectly aligned with your specific subarea of expertise.
3. **Impact Metrics:** Analyze international prestige through consolidated quartiles and indicators from **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index**, and direct links to the **h5-Index (Google Scholar)**.
4. **Smart Recommender (AI):** Paste your title and abstract, and let the Google Gemini AI recommend the best matches with specific rationale and homepage links.
5. **Data Export:** Filter results according to your needs and download the customized table immediately.
"""
else: # Español
    expander_titulo = "📖 Sobre el SciPubs y Cómo Utilizar"
    sobre_texto = """
### ¡Bienvenido al SciPubs: El Portal del Investigador!
Esta es una herramienta desarrollada con el objetivo de optimizar la búsqueda de revistas científicas de alto impacto.
 
####     ¿Qué puedes fazer aquí?
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

# --- HEADER BUTTONS ---
_lang = st.session_state.get('idioma', 'English')

_btn_donate = "☕ Donate"
_btn_sub = "✉️ Subscribe"
if _lang == 'Português':
    _btn_donate = "☕ Doações"
    _btn_sub = "✉️ Inscrever-se"
elif _lang == 'Español':
    _btn_donate = "☕ Doacciones"
    _btn_sub = "✉️ Suscribirse"

col_title, col_btns = st.columns([1, 1])
with col_title:
    st.markdown(t['filtros_tit'])
with col_btns:
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        st.markdown(
            f"""<a href="https://buymeacoffee.com/scipubs" target="_blank" style="text-decoration: none;">
                <button style="width: 100%; background-color: #FFDD00; color: #000000; border: none; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 0.95rem; cursor: pointer; transition: 0.3s;" onmouseover="this.style.backgroundColor='#e6c700'" onmouseout="this.style.backgroundColor='#FFDD00'">
                    {_btn_donate}
                </button>
            </a>""", unsafe_allow_html=True
        )
    with bcol2:
        if st.button(_btn_sub, use_container_width=True, type="primary"):
            st.session_state.show_sub = True
            st.rerun()


# Define as abas com base na presença do parâmetro ?admin=true ou ?visitas=true na URL ou se o usuário logado for Admin
params_url = st.query_params
if "admin" in params_url or "visitas" in params_url or st.session_state.get("is_admin", False):
    tab_busca, tab_ia, tab_admin = st.tabs([t['busca_cat'], t['busca_ia'], "📊 Estatísticas (Admin)"])
else:
    tab_busca, tab_ia = st.tabs([t['busca_cat'], t['busca_ia']])

# ==================== ABA 1: CAT LOGO TRADICIONAL ====================
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
        df_exibir = df_da_pagina.drop(columns=["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento"], errors="ignore")
        
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
                    return val_str + "#🎯 Acessar h5"
                return "-"
            df_exibir["Índice h5"] = df_exibir["Índice h5"].apply(format_h5)
        
        # Reconstrução ultra-defensiva para descartar qualquer metadado do pandas que confunda o PyArrow
        df_exibir = pd.DataFrame({col: df_exibir[col].tolist() for col in df_exibir.columns})
        
        # EXIBIÇÃO DA HOMEPAGE NA TABELA COM LINK CLIC VEL
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

# ==================== ABA 2: RECOMENDADOR INTELIGENTE (DISCOVERY-FIRST) ====================

def _check_ollama_available():
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def _filtrar_journals_ia(journals, area_ia, indexador_ia, t_dict):
    filtrados = journals
    if area_ia not in ("Todas", t_dict.get("ia_todas", "Todas"), t_dict.get("todas", "Todas")):
        filtrados = [
            j for j in filtrados
            if str(j.get("grande_area", "")).strip() == str(area_ia).strip()
        ]
    if indexador_ia not in ("Todos", t_dict.get("ia_todos", "Todos")):
        filtrados = [
            j for j in filtrados
            if indexador_ia.lower() in str(j.get("indexador", "")).lower()
        ]
    return filtrados


def _contar_artigos_similares_por_revista(similar_articles, journal_name):
    if not similar_articles or not journal_name:
        return 0
    from utils.fuzzy_matcher import calculate_similarity
    count = 0
    for artigo in similar_articles:
        revista = str(artigo.get("revista_nome", ""))
        if calculate_similarity(journal_name, revista) >= 0.75:
            count += 1
    return count


def _preparar_candidatos_locais(df_base, titulo, resumo, area_ia, indexador_ia, t_dict):
    df_candidatos = df_base.copy()
    if area_ia not in ("Todas", t_dict.get("ia_todas", "Todas"), t_dict.get("todas", "Todas")):
        df_candidatos = df_candidatos[df_candidatos["Grande Área"] == area_ia]
    if indexador_ia not in ("Todos", t_dict.get("ia_todos", "Todos")):
        df_candidatos = df_candidatos[
            df_candidatos["Indexador"].astype(str).str.contains(re.escape(indexador_ia), case=False, na=False)
        ]

    texto_busca = f"{titulo} {resumo}".lower()
    palavras = set(re.findall(r'\b[a-zA-Zà-ü]{4,}\b', texto_busca))
    stopwords = {
        "para", "como", "uma", "este", "esta", "com", "dos", "das", "pelo", "pela",
        "artigo", "pesquisa", "estudo", "sobre", "with", "this", "from", "that",
        "article", "research", "study", "about"
    }
    palavras_filtradas = palavras - stopwords

    sinonimos_academicos = [
        {"educação", "education", "educación", "ensino", "teaching", "aprendizado", "learning", "aprendizaje"},
        {"computação", "computing", "computador", "computer", "tecnologia", "technology", "tecnología"},
        {"saúde", "health", "salud", "medicina", "medicine", "médico", "medical", "médica"},
        {"ciência", "science", "ciencia", "científico", "scientific", "pesquisa", "research", "investigación"},
    ]

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
            grande_area = str(row.get("Grande Área", "")).lower()
            area = str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", ""))).lower()
            subarea = str(row.get("Subárea do Conhecimento", "")).lower()
            for pal in palavras_filtradas:
                if pal in nome:
                    score += 5
                if pal in grande_area:
                    score += 3
                if pal in area:
                    score += 3
                if pal in subarea:
                    score += 3
            return score

        df_candidatos["relevancia"] = df_candidatos.apply(calcular_relevancia, axis=1)
        df_candidatos = df_candidatos.sort_values(by=["relevancia", "SJR"], ascending=[False, False])
    else:
        df_candidatos["relevancia"] = 0
        df_candidatos = df_candidatos.sort_values(by="SJR", ascending=False)

    if len(df_candidatos) > 40:
        df_candidatos = df_candidatos.head(40)

    return df_candidatos, palavras_filtradas


def _gerar_recomendacoes_locais_fallback(df_base, titulo, resumo, num_recomendacoes, area_ia, indexador_ia, t_dict):
    df_candidatos, palavras_filtradas = _preparar_candidatos_locais(
        df_base, titulo, resumo, area_ia, indexador_ia, t_dict
    )
    if df_candidatos.empty:
        return []

    texto_detect = f"{titulo} {resumo}".lower()
    pt_stops = {"o", "a", "e", "de", "do", "da", "em", "para", "um", "uma", "com", "por", "os", "as"}
    en_stops = {"the", "and", "of", "in", "to", "a", "is", "that", "for", "it", "with", "on", "as"}
    pt_count = sum(1 for w in re.findall(r'\b\w+\b', texto_detect) if w in pt_stops)
    en_count = sum(1 for w in re.findall(r'\b\w+\b', texto_detect) if w in en_stops)
    is_english = en_count > pt_count

    col_titulo = df_base.columns[0]
    top_n = df_candidatos.head(num_recomendacoes)
    max_rel = float(df_candidatos["relevancia"].max()) if "relevancia" in df_candidatos.columns else 0.0
    journals = []

    for idx, (_, row) in enumerate(top_n.iterrows()):
        nome_rev = str(row[col_titulo])
        area_rev = str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", row.get("Grande Área", "-"))))
        rel_score = float(row.get("relevancia", 0.0))

        if max_rel > 0:
            pct = min(96, max(82 + int((rel_score / max_rel) * 14), 96 - (idx * 3)))
        else:
            pct = max(60, 78 - (idx * 4))

        matched_keywords = []
        for p in palavras_filtradas:
            campos = " ".join([
                str(row.get(col_titulo, "")),
                str(row.get("Grande Área", "")),
                str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", ""))),
                str(row.get("Subárea do Conhecimento", "")),
            ]).lower()
            if p in campos:
                matched_keywords.append(p.capitalize())

        if is_english:
            if matched_keywords:
                kw_str = ", ".join(f"'{k}'" for k in list(matched_keywords)[:3])
                justificativa = f"Strong thematic alignment with key concepts: {kw_str}."
            else:
                justificativa = f"Recommended based on the journal's editorial scope in {area_rev}."
        else:
            if matched_keywords:
                kw_str = ", ".join(f"'{k}'" for k in list(matched_keywords)[:3])
                justificativa = f"Forte alinhamento temático com conceitos-chave: {kw_str}."
            else:
                justificativa = f"Recomendado com base no escopo editorial na área de {area_rev}."

        journals.append({
            "nome": nome_rev,
            "issn": row.get("ISSN", "-"),
            "homepage": row.get("Homepage", "-"),
            "grande_area": row.get("Grande Área", "-"),
            "area": area_rev,
            "subarea": row.get("Subárea do Conhecimento", "-"),
            "indexador": row.get("Indexador", "-"),
            "jif": row.get("JIF", "-"),
            "quartil_jcr": row.get("Quartil JCR", "-"),
            "sjr": row.get("SJR", "-"),
            "sjr_quartile": row.get("SJR Best Quartile", "-"),
            "h_index": row.get("H index", row.get("h-index", "-")),
            "h5_link": row.get("Índice h5", "-"),
            "aderencia": pct,
            "justificativa": justificativa,
            "idioma": "EN" if is_english else "PT",
            "fonte_dados": "local",
        })

    return journals


with tab_ia:
    # Função auxiliar local para traduzir as Grandes Áreas
    def traduzir_grande_area(area_original, t_dict):
        if not area_original or str(area_original).strip() in ["-", "None", "nan"]:
            return "-"
        import unicodedata
        def clean_str(s):
            s = str(s).lower().strip()
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            s = ''.join(c for c in s if c.isalnum() or c.isspace())
            return ' '.join(s.split())
        area_clean = clean_str(area_original)
        mapeamento = t_dict.get("areas_trad", {})
        for chave_original, valor_traduzido in mapeamento.items():
            if clean_str(chave_original) == area_clean:
                return valor_traduzido
        return str(area_original).strip()

    from services import check_ollama_available as check_ollama

    # Inicialização segura dos estados na Session State
    if "recomendacoes" not in st.session_state:
        st.session_state.recomendacoes = None
    if "erro_ia" not in st.session_state:
        st.session_state.erro_ia = None
    if "aviso_filtro" not in st.session_state:
        st.session_state.aviso_filtro = False
    if "ia_cache" not in st.session_state:
        st.session_state.ia_cache = {}
    if "artigos_similares" not in st.session_state:
        st.session_state.artigos_similares = None
    if "avaliacao_artigo" not in st.session_state:
        st.session_state.avaliacao_artigo = None
    if "backend_usado" not in st.session_state:
        st.session_state.backend_usado = None
    if "gemini_key_validada" not in st.session_state:
        st.session_state.gemini_key_validada = False
    
    col_input, col_meta = st.columns([2, 1])
    
    with col_input:
        st.markdown(f"### {t['ia_titulo']}")
        st.markdown(f"*{t['ia_subtitulo']}*")
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        
        titulo_artigo = st.text_input(t['ia_campo_titulo'], placeholder="Ex: Análise Epidemiológica de Saúde Coletiva...", key="ia_tit_input")
        resumo_artigo = st.text_area(t['ia_campo_resumo'], placeholder="Paste or type abstract here...", height=250, key="ia_res_input")
        
        disparar_busca = st.button(t['ia_btn_buscar'], type="primary", key="btn_ia_disparar")
        
    with col_meta:
        st.markdown(f"#### {t['ia_credencial_tit']}")
        st.markdown(f"*{t['ia_motor_desc']}*")
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        
        # Lê chave global do Streamlit Secrets (se existir)
        chave_global_gemini = ""
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                chave_global_gemini = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
        
        # Campo para chave Gemini do usuário (opcional)
        user_gemini_key = st.text_input(
            "🔑 Chave Gemini (opcional)",
            type="password",
            placeholder="Deixe em branco para usar Ollama local ou algoritmo local",
            help="Se você tiver uma chave gratuita do Google Gemini, cole aqui para recomendações mais precisas. Sem chave, o app tenta usar o Ollama (Llama 3) instalado localmente; caso contrário, usa o algoritmo local de relevância."
        )
        
                # Define chave ativa
        api_key_ativa = user_gemini_key.strip() if user_gemini_key else (str(chave_global_gemini).strip() if chave_global_gemini else "")
        
        # Status do sistema
        if api_key_ativa:
            st.success("🔑 Chave Gemini configurada")
            # Instrução para obter chave (recolhida)
            with st.expander("ℹ️ Como obter chave gratuita?", expanded=False):
                st.markdown("""
                1. Acesse [aistudio.google.com](https://aistudio.google.com)
                2. Faça login com sua conta Google
                3. Clique em "Get API Key" → "Create API Key"
                4. Copie a chave e cole acima
                """)
        else:
            ollama_ok, _ = check_ollama()
            if ollama_ok:
                st.success(f"✅ Ollama local detectado")
            else:
                st.info("⚙️ Modo local (algoritmo de relevância)")
            with st.expander("ℹ️ Sobre os modos de IA", expanded=False):
                st.markdown(t['ia_como_obter_texto'], unsafe_allow_html=True)
            with st.expander("🔑 Como obter chave Gemini gratuita?", expanded=False):
                st.markdown("""
                1. Acesse [aistudio.google.com](https://aistudio.google.com)
                2. Faça login com sua conta Google
                3. Clique em "Get API Key" → "Create API Key"
                4. Copie a chave e cole no campo acima
                """)
        
        st.markdown(f"#### {t['ia_refinar_pesquisa']}")
        
        grandes_areas_originais = sorted(list(df_original["Grande Área"].dropna().unique()))
        area_ia_opcoes = {t['todas']: "Todas"}
        for area in grandes_areas_originais:
            area_traduzida = traduzir_grande_area(area, t)
            area_ia_opcoes[area_traduzida] = area
            
        area_ia_exibicao = st.selectbox(f"{t['filtro_area']} (IA)", list(area_ia_opcoes.keys()))
        area_ia = area_ia_opcoes[area_ia_exibicao]
        
        indexador_ia = st.selectbox(f"{t['filtro_indexador']} (IA)", [t['ia_todos']] + list(df_original["Indexador"].dropna().unique()))
        
        num_recomendacoes = st.slider(
            t['ia_num_rec'], 
            min_value=3, 
            max_value=20, 
            value=5, 
            step=1
        )
        
    if disparar_busca:
        if not titulo_artigo or not resumo_artigo:
            st.warning("    Preencha o Título e o Resumo do seu artigo científico para rodar a recomendação.")
        else:
            cache_key = hashlib.md5(
                f"{titulo_artigo.strip().lower()}|{resumo_artigo.strip().lower()}|{num_recomendacoes}|{area_ia}|{indexador_ia}".encode("utf-8")
            ).hexdigest()
            
            if cache_key in st.session_state.ia_cache:
                st.session_state.recomendacoes = st.session_state.ia_cache[cache_key]
                st.session_state.erro_ia = None
                st.session_state.aviso_filtro = False
                st.rerun()
            else:
                st.session_state.recomendacoes = None
                st.session_state.erro_ia = None
                st.session_state.aviso_filtro = False
                st.session_state.artigos_similares = None
                st.session_state.avaliacao_artigo = None
                st.session_state.backend_usado = None
                
                status_container = st.empty()
                status_container.info(f"  {t['ia_analisando']}")
                
                tempo_inicio = time.time()
                
                # 1. Usa MatchJournalV2 (Semantic Kernel Style)
                journals = None
                error = None
                backend = "match_journal_v2"
                
                match = get_match_journal_v2(df_original)
                
                journals = match.recommend(
                    titulo=titulo_artigo,
                    resumo=resumo_artigo,
                    order_by="probability",  # Default: Estimated Acceptance Probability
                    top_n=num_recomendacoes,
                    only_with_aims=True  # Só revistas com Aims & Scope preenchidos
                )
                
                st.session_state.backend_usado = "match_journal_v2"
                st.session_state.order_by = "probability"
                
                # Busca artigos similares via OpenAlex (desativada por padrão para agilidade)
                similar_articles = []
                st.session_state.artigos_similares = []
                
                # Avaliação do artigo desativada para agilidade; usa métricas do próprio recommender
                avaliacoes = {}
                st.session_state.avaliacao_artigo = avaliacoes
                
                # Aplica filtros de área/indexador
                if area_ia != "Todas" or indexador_ia != t.get("ia_todos", "Todos"):
                    journals = _filtrar_journals_ia(journals, area_ia, indexador_ia, t)
                
                st.session_state.recomendacoes = journals
                st.session_state.ia_cache[cache_key] = journals
                
                tempo_total = time.time() - tempo_inicio
                
                # Log anônimo
                try:
                    anonymous_logger.log_recommendation(
                        area_conhecimento=area_ia,
                        tempo_resposta_segundos=round(tempo_total, 2),
                        num_resultados=len(journals) if journals else 0,
                        sucesso=(journals is not None and len(journals) > 0),
                        idioma=st.session_state.idioma
                    )
                except Exception:
                    pass
                
                status_container.empty()
                st.rerun()

    # RENDERIZAÇÃO DOS RESULTADOS
    if st.session_state.get("aviso_filtro"):
        st.warning("    Nenhum periódico no catálogo atende aos filtros de Grande Área e Indexador selecionados. Por favor, ajuste os filtros.")
    elif st.session_state.get("erro_ia"):
        st.error(t['ia_erro'])
        st.caption(f"Detalhes: {st.session_state.erro_ia}")
    elif st.session_state.get("recomendacoes") is not None:
        backend = st.session_state.get("backend_usado", "local")
        if backend == "gemini":
            st.success(f"✅ Recomendações via Gemini API")
        elif backend == "ollama":
            st.info(f"🦙 Recomendações via Ollama local")
        else:
            st.info(f"ℹ️ {t['ia_fallback_local']}")
        
        st.success(t['ia_sucesso'])
        
        # Exibe classificação da área do artigo
        avaliacoes = st.session_state.get("avaliacao_artigo", {})
        if avaliacoes:
            primeira_avaliacao = next(iter(avaliacoes.values()), None)
            if primeira_avaliacao and primeira_avaliacao.get("grande_area"):
                st.markdown(f"**{t['ia_classificacao_area']}:** {primeira_avaliacao['grande_area']} > {primeira_avaliacao.get('area', '-')}")
        
        # Exibe artigos similares
        similar_articles = st.session_state.get("artigos_similares", [])
        if similar_articles:
            with st.expander(f"📄 {t['ia_artigos_similares']} ({len(similar_articles)})", expanded=False):
                st.caption(t['ia_artigos_similares_hint'])
                for art in similar_articles[:5]:
                    st.markdown(f"- **{art.get('titulo', '')}**")
                    st.caption(f"  {art.get('revista_nome', '')} ({art.get('ano', '')}) — {art.get('citacao_count', 0)} citações")
        
        # Renderiza cards de cada revista recomendada
        for rec in st.session_state.recomendacoes:
            nome_rev = rec.get("nome", rec.get("revista_nome", ""))
            registro_revista = df_original[df_original[df_original.columns[0]] == nome_rev]
            
            homepage = rec.get("homepage", "")
            issn = rec.get("issn", "N/A")
            indexador = rec.get("indexador", "N/A")
            quartil = rec.get("quartil_jcr", "N/A")
            sjr = rec.get("sjr", "N/A")
            h_index = rec.get("h_index", "-")
            h5_link = rec.get("h5_link", "-")
            aderencia = rec.get("aderencia", rec.get("revista_aderencia", 0))
            probabilidade = rec.get("probabilidade_aceitacao", max(10, aderencia - 5))
            justificativa = rec.get("justificativa", "")
            
            # Se encontrou no df original, enriquece com dados locais
            if not registro_revista.empty:
                try:
                    row = registro_revista.iloc[0]
                    if not homepage or homepage in ["-", "", "nan", "None"]:
                        homepage = str(row.get("Homepage", ""))
                    if issn in ["N/A", "-"]:
                        issn = str(row.get("ISSN", "N/A"))
                    if indexador in ["N/A", "-"]:
                        indexador = str(row.get("Indexador", "N/A"))
                    if quartil in ["N/A", "-"]:
                        quartil = str(row.get("Quartil JCR", "N/A"))
                    if sjr in ["N/A", "-"]:
                        sjr = str(row.get("SJR", "N/A"))
                    if h_index in ["-"]:
                        h_index = str(row.get("H index", row.get("h-index", "-")))
                    if h5_link in ["-"]:
                        h5_link = str(row.get("Índice h5", "-"))
                except Exception:
                    pass
            
            # Obtém avaliação do artigo para esta revista
            aderencia_escopo = aderencia
            justificativa_metricas = justificativa
            
            if nome_rev in avaliacoes:
                ev = avaliacoes[nome_rev]
                aderencia_escopo = ev.get("aderencia_escopo", aderencia)
                probabilidade = ev.get("probabilidade_aceitacao", probabilidade)
                justificativa_metricas = ev.get("justificativa_metricas", justificativa)
            
            with st.container(border=True):
                # Título da revista + botões Homepage e h5 ao lado
                col_titulo, col_btn_home, col_btn_h5 = st.columns([3, 1, 1])
                with col_titulo:
                    st.markdown(f"### {nome_rev}")
                with col_btn_home:
                    if homepage and homepage not in ["nan", "-", "None", ""]:
                        st.link_button(t['ia_card_site'] + " 🔗", homepage, type="primary", use_container_width=True)
                    else:
                        st.info(t['ia_card_sem_site'])
                with col_btn_h5:
                    if h5_link and h5_link not in ["nan", "-", "None", ""]:
                        st.link_button("🎯 Índice h5", h5_link, type="secondary", use_container_width=True)
                
                st.caption(f"**ISSN:** {issn} | **Indexador:** {indexador} | **Quartil:** {quartil} | **SJR:** {sjr} | **H-index:** {h_index}")
                
                # Barras de progresso para métricas
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f"**{t['ia_aderencia_escopo']}**")
                    st.progress(min(aderencia_escopo / 100, 1.0))
                    st.markdown(f"<p style='text-align: center; font-size: 1.2rem; font-weight: bold;'>{aderencia_escopo}%</p>", unsafe_allow_html=True)
                with col_m2:
                    st.markdown(f"**{t['ia_probabilidade']}**")
                    st.progress(min(probabilidade / 100, 1.0))
                    st.markdown(f"<p style='text-align: center; font-size: 1.2rem; font-weight: bold;'>{probabilidade}%</p>", unsafe_allow_html=True)
                
                st.caption(f"*{t['ia_probabilidade_nota']}*")
                
                # Justificativa dissertativa das métricas
                with st.expander(f"📖 {t['ia_justificativa_tit']}", expanded=True):
                    st.markdown(justificativa_metricas)

# ==================== ABA 3: ESTAT STICAS DE ACESSOS (SÓ PARA ADMIN) ====================
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


# --- MODALS & BUTTONS ACTIONS ---
@st.dialog("Subscribe / Inscrever-se")
def show_subscribe_modal():
    st.markdown("### Join our VIP Community! 🚀")
    st.markdown("Leave your email to receive publication tips and platform updates. No spam, we promise.")
    with st.form("subscribe_form"):
        nome = st.text_input("Name:")
        email = st.text_input("Email:")
        if st.form_submit_button("Subscribe", type="primary", use_container_width=True):
            if nome and email:
                import pandas as pd
                import os
                import datetime
                
                caminho = "usuarios.csv"
                novo_usuario = pd.DataFrame([{
                    "Data/Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Nome": nome,
                    "Email": email.lower().strip(),
                    "Assinante": True
                }])
                if os.path.exists(caminho):
                    try:
                        df_existente = pd.read_csv(caminho, sep=";")
                        df_novo = pd.concat([df_existente, novo_usuario], ignore_index=True)
                        df_novo.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
                    except:
                        novo_usuario.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
                else:
                    novo_usuario.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
                    
                st.success("Thank you for subscribing!")
            else:
                st.error("Please fill in both Name and Email.")

if 'show_sub' in st.session_state and st.session_state.show_sub:
    show_subscribe_modal()
    st.session_state.show_sub = False
