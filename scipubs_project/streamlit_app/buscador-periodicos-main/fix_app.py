with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the corrupted first line
content = content.replace('import streamlit as st import sys import os  sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # Safe lazy imports for services def _safe_import(name):     try:         __import__(name)         return True     except Exception:         return False  _discovery_ok = _safe_import("services.discovery_recommender") _similar_ok = _safe_import("services.similar_articles_finder") _evaluator_ok = _safe_import("services.article_evaluator") _cache_ok = _safe_import("services.cache_manager") _logger_ok = _safe_import("utils.logger")        def get_texto_termos(lang):     if st.session_state.get("idioma", "English") == "English":         return', 'import streamlit as st\nimport sys\nimport os\n\n# Adiciona diretório atual ao path para imports locais\nsys.path.append(os.path.dirname(os.path.abspath(__file__)))\n\n\ndef get_texto_termos(lang):\n    if st.session_state.get("idioma", "English") == "English":\n        return')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')