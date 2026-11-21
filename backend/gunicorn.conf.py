import os

from dotenv import load_dotenv


load_dotenv()

bind = f"{os.getenv('HOST', '127.0.0.1')}:{int(os.getenv('PORT', '5000'))}"
# O barramento SSE em memória é compartilhado pelas threads deste worker.
workers = 1
worker_class = "gthread"
threads = int(os.getenv("API_THREADS", "8"))

if threads < 2:
    raise ValueError("API_THREADS deve ser pelo menos 2 para atender SSE e POSTs.")
