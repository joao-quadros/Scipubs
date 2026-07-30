import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import urllib3
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de sys.stdout para UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MAX_WORKERS = 25
BATCH_SIZE = 100

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def build_known_catalog_map():
    """Cria um mapa de revistas já catalogadas em dados_2.csv / dados_complemento.csv."""
    known_map = {}
    for filename in ['dados_complemento.csv', 'dados_2.csv']:
        if os.path.exists(filename):
            try:
                df_cat = pd.read_csv(filename, sep=';', encoding='utf-8-sig', low_memory=False)
                col_title = df_cat.columns[0]
                col_scope = "Aims and Scope" if "Aims and Scope" in df_cat.columns else None
                col_issn = "ISSN" if "ISSN" in df_cat.columns else None

                if col_scope:
                    for _, row in df_cat.iterrows():
                        scope_val = clean_text(str(row.get(col_scope, "")))
                        if scope_val and scope_val not in ["-", "", "nan", "None", "Informação não encontrada"]:
                            t_norm = clean_text(str(row.get(col_title, ""))).lower()
                            if t_norm and t_norm not in known_map:
                                known_map[t_norm] = scope_val

                            if col_issn:
                                issn_val = clean_text(str(row.get(col_issn, ""))).replace("-", "").lower()
                                if issn_val and issn_val not in known_map:
                                    known_map[issn_val] = scope_val
            except Exception as e:
                print(f"Aviso ao carregar {filename}: {e}")
    print(f"[CATÁLOGO EXISTENTE] {len(known_map)} registros mapeados para reutilização inteligente.")
    return known_map

def fetch_openalex_details(issn, title):
    """Consulta OpenAlex para obter informações de escopo, tópicos e conceitos."""
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        issn_clean = str(issn).replace("-", "").strip()
        url = f"https://api.openalex.org/sources/issn:{issn_clean}"
        try:
            r = requests.get(url, timeout=4, verify=False)
            if r.status_code == 200:
                data = r.json()
                desc = data.get("description")
                topics = [t.get("display_name") for t in data.get("topics", [])[:6] if t.get("display_name")]
                concepts = [c.get("display_name") for c in data.get("concepts", [])[:6] if c.get("display_name")]
                
                parts = []
                if desc and len(clean_text(desc)) > 20:
                    parts.append(clean_text(desc))
                elif topics:
                    parts.append("Tópicos Principais: " + ", ".join(topics))
                elif concepts:
                    parts.append("Conceitos Chave: " + ", ".join(concepts))
                    
                if parts:
                    return ". ".join(parts)
        except Exception:
            pass
    return ""

def fetch_doaj_details(issn, title):
    """Consulta DOAJ API para obter escopo e palavras-chave."""
    if issn and str(issn).strip() not in ["-", "", "nan", "None"]:
        issn_clean = str(issn).replace("-", "").strip()
        if len(issn_clean) == 8:
            issn_fmt = f"{issn_clean[:4]}-{issn_clean[4:]}"
        else:
            issn_fmt = issn_clean
        url = f"https://doaj.org/api/v4/search/journals/issn:{issn_fmt}"
        try:
            r = requests.get(url, timeout=4, verify=False)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if results:
                    bib = results[0].get("bibjson", {})
                    subjects = [s.get("term") for s in bib.get("subject", []) if s.get("term")]
                    keywords = bib.get("keywords", [])
                    parts = []
                    if subjects:
                        parts.append("Áreas de Conhecimento: " + ", ".join(subjects))
                    if keywords:
                        parts.append("Palavras-Chave: " + ", ".join(keywords))
                    if parts:
                        return ". ".join(parts)
        except Exception:
            pass
    return ""

def scrape_homepage_profile(url):
    """Extrai Escopo, Missão e Tipos de Trabalhos Aceitos via Web Scraping da Homepage."""
    if not url or str(url).strip() in ["-", "", "nan", "None"]:
        return "", "", ""
        
    url_str = str(url).strip()
    if not url_str.startswith("http"):
        url_str = "http://" + url_str
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    try:
        r = requests.get(url_str, headers=headers, timeout=5, verify=False, allow_redirects=True)
        if r.status_code != 200:
            return "", "", ""
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        escopo_text = ""
        missao_text = ""
        tipos_text = ""

        # 1. Missão Editorial
        for el in soup.find_all(['div', 'section', 'p', 'span']):
            txt_raw = clean_text(el.text)
            txt_low = txt_raw.lower()
            if any(w in txt_low for w in ['nossa missão', 'missão:', 'mission statement', 'misión:']) and len(txt_raw) > 20:
                m_match = re.search(r'(?:nossa missão|missão|mission statement|misión)[:\s]*(.*)', txt_raw, re.I)
                if m_match and len(m_match.group(1).strip()) > 15:
                    missao_text = clean_text(m_match.group(1))[:300]
                    break
                elif len(txt_raw) < 400:
                    missao_text = txt_raw[:300]
                    break

        # 2. Tipos de Trabalhos Aceitos
        for el in soup.find_all(['div', 'section', 'p', 'li', 'ul']):
            txt_raw = clean_text(el.text)
            txt_low = txt_raw.lower()
            if any(w in txt_low for w in ['article types', 'types of papers', 'tipos de artigos', 'tipos de trabalhos', 'manuscript types', 'submissões aceitas']) and len(txt_raw) > 15:
                t_match = re.search(r'(?:article types|types of papers|tipos de artigos|tipos de trabalhos|manuscript types)[:\s]*(.*)', txt_raw, re.I)
                if t_match and len(t_match.group(1).strip()) > 10:
                    tipos_text = clean_text(t_match.group(1))[:250]
                    break
                elif len(txt_raw) < 300:
                    tipos_text = txt_raw[:250]
                    break

        # 3. Meta Description / Escopo
        meta = soup.find('meta', attrs={'name': re.compile(r'description', re.I)}) or soup.find('meta', property=re.compile(r'description', re.I))
        if meta and meta.get('content'):
            m_text = clean_text(meta.get('content'))
            if len(m_text) > 30 and not any(ign in m_text.lower() for ign in ["human", "captcha", "access denied", "robot"]):
                escopo_text = m_text[:600]

        # OJS Summary / About Block
        if not escopo_text:
            ojs_div = soup.find('div', class_=re.compile(r'journal-summary|homepage-about|about|description', re.I))
            if ojs_div:
                txt = clean_text(ojs_div.text)
                if len(txt) > 40:
                    escopo_text = txt[:600]

        # Parágrafos gerais
        if not escopo_text:
            candidates = []
            for p in soup.find_all('p'):
                txt = clean_text(p.text)
                txt_low = txt.lower()
                if len(txt) < 50:
                    continue
                if any(w in txt_low for w in ["publishes", "peer-reviewed", "scope", "aims to", "focuses on", "publica", "escopo", "editorial", "revista"]):
                    candidates.append(txt)
            if candidates:
                escopo_text = "\n\n".join(candidates[:2])[:600]

        return escopo_text, missao_text, tipos_text

    except Exception:
        pass
    return "", "", ""

def process_journal_profile(title, issn, homepage, known_map):
    """Orquestra o mapeamento do perfil editorial da revista."""
    t_clean = clean_text(title)
    t_norm = t_clean.lower()
    issn_clean = clean_text(issn).replace("-", "").lower()

    # 1. Verifica no mapa do catálogo existente
    if t_norm in known_map:
        return known_map[t_norm]
    if issn_clean and issn_clean in known_map:
        return known_map[issn_clean]

    # 2. Web Scraping da Homepage Oficial
    escopo, missao, tipos = scrape_homepage_profile(homepage)

    # 3. Fallback para DOAJ API
    if not escopo or len(escopo) < 30:
        doaj_info = fetch_doaj_details(issn, title)
        if doaj_info:
            escopo = doaj_info

    # 4. Fallback para OpenAlex API
    if not escopo or len(escopo) < 20:
        oa_info = fetch_openalex_details(issn, title)
        if oa_info:
            escopo = oa_info

    # 5. Se nada foi encontrado em nenhuma fonte
    if not escopo and not missao and not tipos:
        return "Informação não encontrada"

    # Monta a síntese estruturada
    parts = []
    if escopo:
        parts.append(f"Objetivo e Escopo: {escopo}")
    if missao:
        parts.append(f"Missão: {missao}")
    if tipos:
        parts.append(f"Tipos de Trabalhos Aceitos: {tipos}")

    return ". ".join(parts)

def process_row(idx, row, known_map):
    col_title = row.index[0]
    col_issn = row.index[1]
    col_hp = row.index[2]

    title = str(row.get(col_title, ""))
    issn = str(row.get(col_issn, ""))
    hp = str(row.get(col_hp, ""))

    profile_text = process_journal_profile(title, issn, hp, known_map)
    return idx, profile_text

def run_enrichment(limit=None):
    src_file = "dados_new.csv"
    dst_file = "dados_new_atualizado.csv"

    if not os.path.exists(src_file):
        print(f"Arquivo {src_file} não encontrado.")
        return

    print(f"--- Iniciando Mapeamento Editorial Automatizado: {src_file} -> {dst_file} ---")

    # Lê arquivo de entrada
    try:
        df = pd.read_csv(src_file, sep=',', encoding='latin-1', low_memory=False)
    except Exception:
        df = pd.read_csv(src_file, sep=';', encoding='utf-8-sig', low_memory=False)

    col_title = df.columns[0]
    col_issn = df.columns[1]
    col_hp = df.columns[2]
    col_scope = "Aims and Scope"

    # Garante que Coluna D é 'Aims and Scope'
    if col_scope not in df.columns:
        df.insert(3, col_scope, "")

    # Prepara dataframe de destino se já existir para retomada pontual
    if os.path.exists(dst_file):
        try:
            df_dst = pd.read_csv(dst_file, sep=';', encoding='utf-8-sig', low_memory=False)
            if col_scope not in df_dst.columns:
                df_dst.insert(3, col_scope, "")
        except Exception:
            df_dst = df.copy()
    else:
        df_dst = df.copy()

    df_dst[col_scope] = df_dst[col_scope].astype(object).fillna("").astype(str)

    # Constrói o mapa de reutilização do catálogo existente
    known_map = build_known_catalog_map()

    # Identifica linhas pendentes de processamento
    mask_pending = df_dst[col_scope].isna() | (df_dst[col_scope].astype(str).str.strip() == "") | (df_dst[col_scope].astype(str).str.strip() == "-")
    pending_indices = df_dst[mask_pending].index.tolist()

    if limit:
        pending_indices = pending_indices[:limit]

    total = len(pending_indices)
    print(f"Total de periódicos a processar: {total}")

    if total == 0:
        print("Todos os periódicos já foram processados!")
        return

    success_count = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch_indices = pending_indices[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Lote {batch_num}/{total_batches}] Processando periódicos {i+1} a {i+len(batch_indices)} de {total}...")

        batch_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_row, idx, df_dst.iloc[idx], known_map): idx
                for idx in batch_indices
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    res_idx, profile_text = future.result()
                    if profile_text:
                        batch_results.append((res_idx, profile_text))
                except Exception:
                    pass

        # Grava resultados no arquivo de destino
        for res_idx, profile_text in batch_results:
            df_dst.at[res_idx, col_scope] = profile_text
            success_count += 1

        df_dst.to_csv(dst_file, sep=';', index=False, encoding='utf-8-sig')

        elapsed = time.time() - start_time
        rate = (i + len(batch_indices)) / max(1, elapsed)
        rem_sec = (total - (i + len(batch_indices))) / max(0.1, rate)
        print(f"[OK] Lote {batch_num} salvo em {dst_file}! +{len(batch_results)} processadas (Total: {success_count} | {elapsed/60:.1f} min decorridos | Est. restante: {rem_sec/60:.1f} min).")

    print(f"\n[FIM] Processamento concluído! Dados gravados com sucesso em {dst_file}.")

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_enrichment(limit=limit_val)
