import requests
from bs4 import BeautifulSoup
import json
import re

# Teste 1: SciELO Analytics API / page
url = "http://analytics.scielo.org/w/accesses?journal=0034-8910&collection=scl"
try:
    r = requests.get(url, timeout=5)
    print("SciELO Analytics status:", r.status_code)
except Exception as e:
    print("SciELO Analytics error:", e)

# Teste 2: SciELO REST API endpoint para métricas (h5_index e h5_median)
# SciELO disponibiliza a API de indicadores em api.scielo.org / analytics.scielo.org
url_api = "https://analytics.scielo.org/api/v1/journal/h5_index/?journal=0034-8910"
try:
    r = requests.get(url_api, timeout=5, verify=False)
    print("SciELO h5 API status:", r.status_code)
    if r.status_code == 200:
        print("Retorno h5 API:", r.text[:300])
except Exception as e:
    print("SciELO h5 API error:", e)
