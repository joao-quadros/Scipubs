import webview

def create_app():
    # URL oficial do portal
    url = "https://www.scipubs.com"
    
    # Cria uma janela nativa (webview) sem bordas de navegador
    window = webview.create_window(
        'SciPubs - Open Science Matters', 
        url,
        width=1200, 
        height=800,
        min_size=(800, 600),
        text_select=True,
        zoomable=True
    )
    
    # Inicia a interface gráfica
    webview.start()

if __name__ == '__main__':
    create_app()
