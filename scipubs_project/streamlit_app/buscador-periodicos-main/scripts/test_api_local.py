"""
Testa a API FastAPI localmente.
Inicia o servidor, faz uma requisição e finaliza.
"""

import os
import sys
import time
import subprocess
import signal
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    env = os.environ.copy()
    env["DATABASE_URL"] = os.getenv("DATABASE_URL", "")
    env["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")
    env["EMBEDDING_PROVIDER"] = "tfidf"
    env["LLM_PROVIDER"] = "groq"

    print("Iniciando servidor uvicorn...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    try:
        time.sleep(8)  # Aguarda servidor subir

        print("Testando /health...")
        r = requests.get("http://127.0.0.1:8000/health", timeout=10)
        print(f"  /health: {r.status_code} - {r.json()}")

        print("Testando /recommend...")
        payload = {
            "title": "Literature and comparative studies in education",
            "abstract": "This article discusses comparative approaches to literature and education in Iberian contexts.",
            "top_n": 5,
            "generate_justifications": False
        }
        r = requests.post("http://127.0.0.1:8000/recommend", json=payload, timeout=30)
        print(f"  /recommend: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Resultados: {len(data['results'])}")
            for res in data['results'][:3]:
                print(f"    - {res['title']}: {res['match_score']}")
        else:
            print(f"  Erro: {r.text}")

    finally:
        print("Finalizando servidor...")
        proc.send_signal(signal.CTRL_BREAK_SIGNAL)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Servidor finalizado")


if __name__ == "__main__":
    main()
