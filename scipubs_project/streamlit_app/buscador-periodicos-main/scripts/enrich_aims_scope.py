import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

# Configurações do Scraper
MAX_WORKERS = 15  # Número de threads paralelas (moderado para evitar bans de IP)
TIMEOUT = 6      # Timeout curto para requisições em segundos

def clean_html_text(text):
    """Limpa espaços em branco e quebras de linha."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_aims_scope_from_html(html_content, url):
    """
    Usa heurísticas baseadas em marcas de editoras e NLP simples
    para extrair o escopo real de uma revista a partir do HTML.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    url_lower = url.lower()
    
    # 1. Caso SAGE (journals.sagepub.com)
    if "sagepub.com" in url_lower:
        # Tenta blocos comuns de descrição na SAGE
        desc_div = soup.find('div', class_=re.compile(r'journal-description|overview|aims-and-scopes|about'))
        if desc_div:
            p_tags = desc_div.find_all('p')
            if p_tags:
                return "\n\n".join([clean_html_text(p.text) for p in p_tags if len(p.text.strip()) > 30])
        # Fallback para tags de meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return clean_html_text(meta_desc.get('content'))

    # 2. Caso SciELO (scielo.br / scielo.org)
    if "scielo" in url_lower:
        # Procura por seções de escopo ou "sobre"
        about_div = soup.find('div', id='about') or soup.find('div', class_='about')
        if about_div:
            return clean_html_text(about_div.text)
        # Busca por parágrafos longos que descrevam o periódico
        p_tags = soup.find_all('p')
        for p in p_tags:
            txt = p.text.lower()
            if "publica" in txt or "escopo" in txt or "objetivo" in txt or "editorial" in txt:
                if len(p.text.strip()) > 80:
                    return clean_html_text(p.text)

    # 3. Caso Elsevier / ScienceDirect
    if "elsevier.com" in url_lower or "sciencedirect.com" in url_lower:
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', property='og:description')
        if meta_desc and meta_desc.get('content'):
            return clean_html_text(meta_desc.get('content'))

    # 4. Caso Wiley / Springer
    if "wiley.com" in url_lower or "springer.com" in url_lower:
        aims_section = soup.find('section', id=re.compile(r'aims|scope|about')) or soup.find('div', class_=re.compile(r'aims|scope|about'))
        if aims_section:
            return clean_html_text(aims_section.text)

    # Heurística Geral para qualquer site acadêmico:
    # Procura por parágrafos longos que contenham marcadores semânticos de escopo
    p_tags = soup.find_all('p')
    candidates = []
    
    for p in p_tags:
        txt = p.text.strip()
        txt_lower = txt.lower()
        if len(txt) < 60:
            continue
            
        # Padrões comuns em inglês, português e espanhol
        patterns = [
            r"\bpublishes\b", r"\bpeer-reviewed\b", r"\bscope of the journal\b", 
            r"\baims to\b", r"\bwelcomes submissions\b", r"\bdedicated to\b",
            r"\bpublica\b", r"\brevista científica\b", r"\blinha editorial\b",
            r"\bseções\b", r"\bárea de\b", r"\bconhecimento\b",
            r"\bpublicación\b", r"\bdirigida a\b", r"\bse enfoca en\b"
        ]
        
        if any(re.search(pat, txt_lower) for pat in patterns):
            candidates.append(clean_html_text(txt))
            
    if candidates:
        # Retorna a junção dos 2 melhores parágrafos encontrados
        return "\n\n".join(candidates[:2])
        
    # Último recurso: meta description do site
    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', property='og:description')
    if meta_desc and meta_desc.get('content'):
        return clean_html_text(meta_desc.get('content'))
        
    return ""

def process_journal(row_data, col_title):
    """Executa a requisição e a extração para uma única revista."""
    nome = row_data[col_title]
    url = row_data.get("Homepage", "")
    
    if not url or str(url).strip() in ["-", "", "nan", "None"]:
        return nome, ""
        
    url = str(url).strip()
    if not url.startswith("http"):
        url = "http://" + url
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            escopo = extract_aims_scope_from_html(response.text, url)
            if escopo and len(escopo) > 40:
                return nome, escopo
    except Exception:
        pass
        
    return nome, ""

def enrich_csv(fn):
    """Processa o arquivo CSV de forma concorrente e atualiza progressivamente."""
    if not os.path.exists(fn):
        print(f"Arquivo {fn} não encontrado.")
        return
        
    print(f"\nIniciando enriquecimento de Aims & Scope para: {fn}...")
    try:
        df = pd.read_csv(fn, sep=';', encoding='utf-8-sig', low_memory=False)
    except Exception as e:
        print(f"Erro ao ler {fn}: {e}")
        return

    # Corrige nome das colunas
    col_title = df.columns[0]
    if 'Aims e Escopo' not in df.columns:
        df['Aims e Escopo'] = ""
        
    # Filtra linhas elegíveis (que têm homepage válida e ainda não têm escopo real)
    # Consideramos "não real" se o escopo for muito curto ou contiver o marcador de concatenação de áreas " - "
    def is_placeholder(val):
        val_str = str(val).strip()
        if val_str in ["", "-", "nan", "None"]:
            return True
        # Se contiver apenas a concatenação de áreas gerada anteriormente
        if " - " in val_str and len(val_str) < 150:
            return True
        return False
        
    mask_to_process = df['Homepage'].notna() & (df['Homepage'] != '-') & (df['Homepage'] != '') & df['Aims e Escopo'].apply(is_placeholder)
    indices_to_process = df[mask_to_process].index.tolist()
    
    total_total = len(df)
    total_elegivel = len(indices_to_process)
    print(f"Total de registros: {total_total} | Elegíveis para scraping: {total_elegivel}")
    
    if total_elegivel == 0:
        print("Tudo pronto! Nenhuma linha precisa de processamento.")
        return

    # Limita o processamento em lote para evitar gargalos (processa os top N com maior relevância/impacto primeiro)
    # Ordenamos de forma a processar os que têm SJR preenchido primeiro
    df_temp = df.loc[indices_to_process].copy()
    if 'SJR' in df_temp.columns:
        df_temp['SJR_num'] = pd.to_numeric(df_temp['SJR'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_temp = df_temp.sort_values(by='SJR_num', ascending=False)
        indices_to_process = df_temp.index.tolist()

    # Processamento em lotes de 100 para ir salvando o arquivo e não perder dados
    batch_size = 100
    processed_count = 0
    success_count = 0
    
    for i in range(0, len(indices_to_process), batch_size):
        batch_indices = indices_to_process[i:i+batch_size]
        print(f"\nProcessando lote de {i+1} a {i+len(batch_indices)} de {total_elegivel}...")
        
        results = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(process_journal, df.loc[idx], col_title): idx 
                for idx in batch_indices
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    nome, escopo = future.result()
                    if escopo:
                        results[idx] = escopo
                        success_count += 1
                except Exception as e:
                    pass
                processed_count += 1
                
        # Atualiza o DataFrame com os resultados do lote e salva no disco
        if results:
            for idx, escopo in results.items():
                df.at[idx, 'Aims e Escopo'] = escopo
            try:
                df.to_csv(fn, sep=';', index=False, encoding='utf-8-sig')
                print(f"Lote salvo! {len(results)} revistas enriquecidas com escopo real neste lote.")
            except Exception as save_err:
                print(f"Erro ao salvar lote no arquivo {fn}: {save_err}")
        else:
            print("Lote concluído (nenhum escopo novo encontrado).")
            
    print(f"\nFinalizado {fn}: {success_count} revistas atualizadas com sucesso de {processed_count} tentadas.")

if __name__ == "__main__":
    enrich_csv("dados.csv")
    enrich_csv("dados_revistas.csv")
