"""
Wrapper que reinicia o update de embeddings em lotes pequenos,
tolerante a falhas silenciosas do processo Python no Windows.
"""

import os
import sys
import subprocess
import time

os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_wCkrIFD9L2Tt@ep-rough-shape-avypfnm7-pooler.c-11.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script_path = os.path.join(project_dir, "scripts", "update_embeddings_fastembed.py")
log_path = os.path.join(project_dir, "logs", "update_fastembed.log")

while True:
    print(f"[LOOP] Iniciando lote... ({time.strftime('%H:%M:%S')})")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[LOOP] Iniciando lote... ({time.strftime('%H:%M:%S')})\n")
        proc = subprocess.Popen(
            [sys.executable, "-u", script_path, "--max-batches", "10"],
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=project_dir
        )
        proc.wait()
        log.write(f"[LOOP] Processo encerrou com codigo {proc.returncode}. Reiniciando em 5s...\n")
    print(f"[LOOP] Processo encerrou com codigo {proc.returncode}. Reiniciando em 5s...")
    time.sleep(5)
