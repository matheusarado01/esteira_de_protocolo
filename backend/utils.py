import re
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import logging

# Corrige o carregamento do .env para garantir que funcione fora da raiz
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_conn():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        logger.info("Conexão com o banco estabelecida")
        return conn
    except psycopg2.Error as e:
        logger.critical(f"Erro na conexão com banco de dados: {e}")
        raise

def log(msg, tipo="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.log(getattr(logging, tipo), f"[{timestamp}] {msg}")

CNJ_RE = re.compile(r"\d{7}-\d{2}(?:\.\d{4})?\.\d(?:\.\d{2})?\.\d{4}|\d{20}")
NUMERIC_RE = re.compile(r"\d{6,25}")
OPAJ_RE = re.compile(r"OPAJ[-–:/\s]*([0-9]+)", re.IGNORECASE)
ID_RE = re.compile(r"\b(FNDA|DILA)[-–:/\s]?(\d{6,})\b", re.IGNORECASE)
STATUS_RE = re.compile(
    r"(RESPOSTA FINAL|RESPOSTA PARCIAL|DILAÇÃO|RESPOSTA MONITORAMENTO)",
    re.IGNORECASE
)

def extrair_referencias_assunto(assunto):
    processo = None
    tipo_processo = None
    match = CNJ_RE.search(assunto)
    if match:
        processo = match.group(0)
        tipo_processo = "CNJ"
    else:
        alt_match = NUMERIC_RE.search(assunto)
        if alt_match:
            processo = alt_match.group(0)
            tipo_processo = "ADMINISTRATIVO"
    opaj_match = OPAJ_RE.search(assunto)
    opaj = opaj_match.group(1) if opaj_match else None
    id_match = ID_RE.search(assunto)
    identificador = f"{id_match.group(1).upper()}-{id_match.group(2)}" if id_match else None
    status_matches = STATUS_RE.findall(assunto.upper())
    status_final = status_matches[-1] if status_matches else None
    return processo.strip() if processo else None, opaj, identificador, status_final, tipo_processo

def extrair_campos(texto):
    processo = None
    match = CNJ_RE.search(texto)
    if match:
        processo = match.group(0)
    else:
        alt_match = NUMERIC_RE.search(texto)
        processo = alt_match.group(0) if alt_match else None
    opaj_match = OPAJ_RE.search(texto)
    opaj = opaj_match.group(1) if opaj_match else None
    id_match = ID_RE.search(texto)
    identificador = f"{id_match.group(1).upper()}-{id_match.group(2)}" if id_match else None
    return processo.strip() if processo else None, opaj, identificador

def get_id_resposta_by_id_anexo(cur, id_anexo):
    try:
        cur.execute("SELECT id_resposta FROM respostas WHERE id_anexo = %s", (id_anexo,))
        row = cur.fetchone()
        return row[0] if row else None
    except psycopg2.Error as e:
        logger.error(f"Erro ao buscar id_resposta pelo id_anexo {id_anexo}: {e}")
        return None

def log_query(cur, query, params=None):
    try:
        cur.execute(query, params)
        log(f"Query executada: {query} | Params: {params}")
    except psycopg2.Error as e:
        log(f"Erro ao executar query: {query} | Params: {params} | Erro: {e}", "ERRO")
        raise

def testar_conexao():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                log("Conexão com o banco de dados funcionando.", "INFO")
        return True
    except psycopg2.Error as e:
        log(f"Falha na conexão: {e}", "CRITICAL")
        return False

def buscar_validacoes_por_resposta(cur, id_resposta):
    try:
        cur.execute("""
            SELECT * FROM validacoes WHERE id_resposta = %s ORDER BY data_validacao DESC
        """, (id_resposta,))
        return cur.fetchall()
    except psycopg2.Error as e:
        log(f"Erro ao buscar validações: {e}", "ERRO")
        return []
