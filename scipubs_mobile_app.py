"""
===============================================================================
📱 SCIPUBS MOBILE PWA - SERVIÇO WEB DEDICADO RENDER (512MB RAM EXCLUSIVO)
===============================================================================
Este arquivo executa o aplicativo PWA Mobile do SciPubs de forma 100% isolada,
garantindo 512 MB de RAM dedicados exclusivamente para smartphones e tablets.
"""
import os
import sys

# Importa todas as estruturas do scipubs_flet_app.py
import scipubs_flet_app

def main_mobile(page: scipubs_flet_app.ft.Page):
    # Força configurações de tela para PWA Mobile
    page.title = "SciPubs - App Mobile"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = scipubs_flet_app.ft.ThemeMode.DARK
    page.bgcolor = scipubs_flet_app.MAIN_BG
    
    # Executa o aplicativo Flet
    scipubs_flet_app.main(page)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    try:
        import flet.fastapi as flet_fastapi
        import uvicorn
        from starlette.middleware.gzip import GZipMiddleware
        
        fastapi_app = flet_fastapi.app(main_mobile, assets_dir=scipubs_flet_app.ICONS_DIR)
        fastapi_app.add_middleware(GZipMiddleware, minimum_size=500)
        
        print(f"[SCIPUBS MOBILE PWA] Serviço dedicado rodando na porta {port} com GZip Ativo!")
        uvicorn.run(fastapi_app, host=host, port=port, log_level="warning")
    except Exception as err:
        print(f"[FALLBACK] Iniciando ft.app mobile padrão: {err}")
        scipubs_flet_app.ft.app(main_mobile, assets_dir=scipubs_flet_app.ICONS_DIR, host=host, port=port, view=scipubs_flet_app.ft.AppView.WEB_BROWSER)
