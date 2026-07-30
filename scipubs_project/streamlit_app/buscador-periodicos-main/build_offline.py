import subprocess
import sys

def build():
    print("Iniciando build do PyInstaller para o Streamlit Offline...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SciPubs_Offline",
        "--onefile",
        "--noconsole",
        "--collect-all", "streamlit",
        "--add-data", "app.py;.",
        "--add-data", "dados_revistas.csv;.",
        "--add-data", "dados.csv;.",
        "--add-data", "usuarios.csv;.",
        "--add-data", "logo.png;.",
        "--add-data", "logo_en.png;.",
        "--add-data", "logo_es.png;.",
        "--add-data", "logo_azul.png;.",
        "--add-data", "Logo_Portal do Pesquisador.png;.",
        "--add-data", "favicon2.png;.",
        "--icon=icon.ico",
        "run_app.py"
    ]
    
    subprocess.run(cmd, check=True)
    print("Build finalizado com sucesso!")

if __name__ == "__main__":
    build()
