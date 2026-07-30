#!/usr/bin/env python3
"""Script para buscar Objetivo e Escopo de periódicos usando múltiplas fontes."""

import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
import re

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dados.csv")
EMAIL = "support@scipubs.com"
HEADERS = {"User-Agent": f"SciPubs/1.0 (mailto:{EMAIL})"}
MAX_TEXT_LENGTH = 1500

# APIs
OPENALEX_URL = "https://api.openalex.org/sources/issn:{}"
SCIELO_URL = "https://articlemeta.scielo.org/api/v1/journal/issn:{}"
CROSSREF_URL = "https://api.crossref.org/journals/{}"