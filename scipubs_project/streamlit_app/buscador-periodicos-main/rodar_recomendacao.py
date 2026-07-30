import sys
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
from recomendar_regras import recomendar_periodicos

titulo = "Humane: estudo piloto para validação de instrumento sobre Humanização na Educação Musical"
resumo = (
    "O processo de humanização na educação musical carece de métricas que legitimem sua dimensão formativa frente às pressões por resultados técnicos. "
    "Este estudo piloto objetivou desenvolver e validar o questionário Humane (Humanização em Música e Educação), fundamentado nas categorias de Paulo Freire "
    "(Diálogo, Conscientização, Práxis, Esperançar e Desumanização), e testar seu poder preditivo sobre a permanência de estudantes (N = 130) no Programa Música na Rede. "
    "A metodologia integreu Processamento de Linguagem Natural, Exploratory Graph Analysis, Teoria de Resposta ao Item e Modelagem de Equações Estruturais. "
    "Os resultados revelaram que, embora a teoria sugira os cinco eixos, a subjetividade discente processa a experiência em dois polos independentes: "
    "Engajamento Humanizador (ω = 0,90) e Consciência da Desumanização (ω = 0,69). O modelo estrutural apresentou ajuste de excelência "
    "(χ2/df = 1,14; CFI = 0,99; RMSEA = 0,03), demonstrando que a Humanização é um preditor robusto da retenção. Isoladamente, o construto humanizador "
    "explicou 13,4% da variância da permanência (β = 0,366; p < 0,001). A percepção de desumanização não impulsionou a evasão, sugerindo a autonomia do sujeito "
    "frente às situações-limite. Conclui-se que o Humane constitui uma ferramenta robusta para o diagnóstico pedagógico e a fundamentação de políticas públicas, "
    "recomendando-se estudos futuros com delineamento experimental para refinar a natureza binária do polo negativo."
)

print("Iniciando a recomendação otimizada (com filtro de Grande Área e novos pesos)...")
df_res = recomendar_periodicos(titulo=titulo, resumo=resumo, top_n=100, filtrar_area=True)

# Salva resultados
output_path = os.path.join(BASE_DIR, "resultados_recomendacao.csv")
df_res.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"Resultados completos salvos em: {output_path}")

# Exibe Top 15 resultados formatados
print("\n=== TOP 15 PERIODICOS RECOMENDADOS (OTIMIZADOS) ===")
for idx, row in df_res.head(15).reset_index().iterrows():
    title_safe = str(row['titulo_revista']).encode('ascii', 'ignore').decode('ascii')
    garea_safe = str(row['grande_area']).encode('ascii', 'ignore').decode('ascii')
    idx_safe = str(row['indexador']).encode('ascii', 'ignore').decode('ascii')
    scope_safe = str(row['aims_scope']).encode('ascii', 'ignore').decode('ascii')
    
    print(f"{idx+1}. {title_safe}")
    print(f"   Grande Área: {garea_safe}")
    print(f"   Score Final: {row['Score_final']:.4f} (S_text: {row['S_text']:.4f}, S_index: {row['S_index']:.1f})")
    print(f"   Fator de Impacto (Desempate): {row['fator_impacto']:.4f} (JIF: {row['jif']}, SJR: {row['sjr']})")
    print(f"   Indexadores: {idx_safe}")
    print(f"   Escopo (truncado): {scope_safe[:120]}...")
    print("-" * 50)
