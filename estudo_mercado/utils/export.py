import pandas as pd
import json
import io

def export_to_excel(competitors_list, swot_dict, project_info):
    """Gera um arquivo Excel em memória com múltiplas abas de análise."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Aba 1: Resumo do Projeto
        df_proj = pd.DataFrame([project_info])
        df_proj.to_excel(writer, sheet_name='Informações do Projeto', index=False)
        
        # Aba 2: Concorrentes
        if competitors_list:
            df_comp = pd.DataFrame(competitors_list)
            df_comp.to_excel(writer, sheet_name='Análise Competitiva', index=False)
            
        # Aba 3: Matriz SWOT
        if swot_dict:
            swot_rows = []
            for category, items in swot_dict.items():
                for item in items:
                    swot_rows.append({"Categoria": category, "Item": item})
            df_swot = pd.DataFrame(swot_rows)
            df_swot.to_excel(writer, sheet_name='Matriz SWOT', index=False)
            
    output.seek(0)
    return output.getvalue()

def export_to_json(analysis_data):
    """Exporta o objeto completo de análise em formato JSON."""
    return json.dumps(analysis_data, ensure_ascii=False, indent=2)
