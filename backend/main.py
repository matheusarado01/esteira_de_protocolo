# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import protocolos

app = FastAPI(
    title="API de Protocolo e Validação",
    description="Este backend gerencia protocolos de e-mails judiciais, permitindo registro de divergências, envio de recibos e geração de relatórios.",
    version="1.0.0",
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou defina explicitamente ["http://localhost:3000"] para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão das rotas
app.include_router(protocolos.router)
