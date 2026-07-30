import requests
import json
import logging
from utils.formatting import clean_markdown_codeblocks

logger = logging.getLogger(__name__)

class GeminiMarketClient:
    """Cliente para integrações estratégicas de análise de mercado via Gemini 2.5."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def generate_content(self, prompt: str, timeout: int = 40) -> str:
        """Envia um prompt para o modelo Gemini e retorna a resposta textual."""
        if not self.api_key:
            raise ValueError("Chave API do Gemini não configurada.")
            
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.base_url, json=payload, headers=headers, timeout=timeout)
        
        if response.ok:
            data = response.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return clean_markdown_codeblocks(text)
            except (KeyError, IndexError) as e:
                raise ValueError(f"Formato inesperado na resposta do Gemini: {e}")
        else:
            raise RuntimeError(f"Erro na API Gemini (Status {response.status_code}): {response.text}")

    def run_market_study(self, project_info: dict) -> dict:
        """
        Gera um estudo de mercado completo em JSON estruturado incluindo:
        - Resumo Executivo
        - Matriz SWOT (Forças, Oportunidades, Fraquezas, Ameaças)
        - Análise Competitiva (3-5 Concorrentes Principais)
        - Recomendações Estratégicas e Indicadores de Risco/Oportunidade
        """
        prompt = f"""
        Você é um consultor sênior de inteligência de mercado e estratégia de negócios da McKinsey / BCG.
        Realize um Estudo de Mercado Aprofundado para o projeto abaixo:

        INFORMAÇÕES DO PROJETO:
        - Nome do Projeto: {project_info.get('nome_projeto')}
        - Segmento / Nicho: {project_info.get('segmento')}
        - Descrição do Produto/Serviço: {project_info.get('descricao')}
        - Público-Alvo: {project_info.get('publico_alvo')}
        - Foco do Estudo: {project_info.get('objetivo_estudo')}
        - Abrangência Geográfica: {project_info.get('abrangencia')}
        - URLs / Concorrentes Mencionados: {project_info.get('urls', 'Nenhum informado')}

        EXIGÊNCIA DE RESPOSTA:
        Responda estritamente com um objeto JSON válido, sem tags markdown adicionais (como ```json ou ```). Use exatamente a seguinte estrutura:

        {{
          "resumo_executivo": "Visão geral estratégica concisa em 2 parágrafos...",
          "score_oportunidade": 85,
          "nivel_concorrencia": "Médio / Alto",
          "tamanho_mercado_estimado": "Ex: R$ 1,2 Bilhão (Brasil)",
          "matriz_swot": {{
            "forcas": ["Ponto forte 1", "Ponto forte 2", "Ponto forte 3"],
            "oportunidades": ["Oportunidade 1", "Oportunidade 2", "Oportunidade 3"],
            "fraquezas": ["Ponto fraco 1", "Ponto fraco 2"],
            "ameacas": ["Ameaça 1", "Ameaça 2"]
          }},
          "concorrentes": [
            {{
              "nome": "Concorrente A",
              "posicionamento": "Líder de mercado tradicional",
              "pontos_fortes": "Marca consolidada e grande base de clientes",
              "pontos_fracos": "Tecnologia legada e preços elevados",
              "diferencial_proposto": "Como se diferenciar deste player"
            }},
            {{
              "nome": "Concorrente B",
              "posicionamento": "Startup de crescimento rápido",
              "pontos_fortes": "Interface moderna e preços acessíveis",
              "pontos_fracos": "Pouca abrangência de recursos avançados",
              "diferencial_proposto": "Recursos exclusivos e suporte especializado"
            }}
          ],
          "recomendacoes_estrategicas": [
            "Recomendação 1 de go-to-market",
            "Recomendação 2 de precificação",
            "Recomendação 3 de diferenciação de produto"
          ],
          "principais_riscos": [
            "Risco regulatório ou de adoção 1",
            "Risco de concorrência 2"
          ]
        }}
        """

        raw_text = self.generate_content(prompt, timeout=60)
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback se a IA retornar caracteres extras
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError("Não foi possível decodificar a resposta da IA em formato JSON válido.")
