import requests
import json
import os

# Tenta carregar chave
api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    try:
        # Tenta ler do .env local
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "GEMINI_API_KEY" in line:
                        api_key = line.split("=")[1].strip().strip('"').strip("'")
    except:
        pass

if not api_key:
    try:
        # Tenta ler do Streamlit secrets
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except:
        pass

if not api_key:
    print("Erro: Chave API Gemini não configurada.")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = "Provide the official Aims and Scope description of the academic journal 'Musicae Scientiae' (ISSN 1029-8649). Return only the text description of aims and scope, without extra comments."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=20)
        if response.ok:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print("--- RETORNO DO GEMINI ---")
            print(text)
        else:
            print(f"Erro na API (Status {response.status_code}): {response.text}")
    except Exception as e:
        print(f"Erro de conexão: {e}")
