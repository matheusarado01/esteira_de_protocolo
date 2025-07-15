from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, date
from typing import Optional
import io
import pandas as pd
import re
import logging
from dotenv import load_dotenv
from backend.dashboard_auth_utils import autenticar_usuario
from backend.utils import get_conn, extrair_campos, extrair_referencias_assunto, validar_contexto_email
from backend.ia_validador import validar_formal_ia
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- FUNÇÕES AUXILIARES PADRÃO ---
def extrair_processo(texto: str) -> str:
    match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{1,2}\.\d{4}", texto)
    return match.group(0) if match else ""

def extrair_opaj(texto: str) -> str:
    match = re.search(r"\b\d{7}\b", texto)
    return match.group(0) if match else ""

def tem_zip(nome: str) -> bool:
    return nome.endswith(".zip") if nome else False

def tem_pdf(nome: str) -> bool:
    return nome.endswith(".pdf") if nome else False

# --- pipeline principal com validação IA ---
def pipeline(limite=None, data=None):
    """
    1. Busca e-mails tipo 'protocolo' sem protocolo criado.
    2. Faz parsing, validação IA e salva status/resultados.
    3. Insere em 'protocolos' com status, IA, motivo e campos extras.
    """
    logger.info(f"Iniciando pipeline de validação de e-mails (limite={limite}, data={data})")
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT e.*
        FROM emails e
        LEFT JOIN protocolos p ON e.id_email = p.id_email
        WHERE p.id_email IS NULL
        AND e.tipo_email = 'protocolo'
    """
    params = []
    if data:
        query += " AND DATE(e.recebido_em) = %s"
        params.append(data)
    if limite:
        query += f" LIMIT {limite}"

    cur.execute(query, tuple(params))
    emails = cur.fetchall()

    if not emails:
        logger.info("Nenhum e-mail novo para processar.")
        cur.close()
        conn.close()
        return

    for email in emails:
        id_email = email['id_email']
        assunto = email.get('assunto') or ""
        corpo = email.get('corpo_email') or ""

        # Extrai anexos
        cur.execute("SELECT nome_arquivo, tipo_arquivo FROM anexos_email WHERE id_email = %s", (id_email,))
        anexos = cur.fetchall()
        nomes_anexos = [a["nome_arquivo"] for a in anexos]
        textos_anexos = [""] * len(anexos)

        # Usa utils para extrair campos relevantes
        processo, opaj, identificador = extrair_campos(f"{assunto} {corpo}")
        campos_extraidos = {
            "processo": processo,
            "opaj": opaj,
            "identificador": identificador
        }

        # Validação formal IA
        resultado_ia = validar_formal_ia(
            assunto, corpo, nomes_anexos, textos_anexos, campos_extraidos
        )
        status = "pending" if resultado_ia.get("valido") else "invalid"
        motivo_invalido = None if resultado_ia.get("valido") else resultado_ia.get("motivo")
        observacao = resultado_ia.get("motivo")
        coerente = resultado_ia.get("coerencia")
        campos_faltantes = resultado_ia.get("campos_faltantes", [])  # <-- LISTA DIRETA!
        acao_sugerida = resultado_ia.get("acao_sugerida")
        status_validacao = resultado_ia.get("acao_sugerida")
        resumo_ia = resultado_ia.get("motivo")

        # Insere/atualiza em respostas
        cur.execute("""
            INSERT INTO respostas (
                id_email, tipo_resposta, processo, opaj, coerente, erros,
                identificador, status, status_validacao, validado,
                data_chegada, nomes_anexos, resumo_ia, observacao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            ON CONFLICT (id_email) DO UPDATE SET
                tipo_resposta = EXCLUDED.tipo_resposta,
                processo = EXCLUDED.processo,
                opaj = EXCLUDED.opaj,
                coerente = EXCLUDED.coerente,
                erros = EXCLUDED.erros,
                identificador = EXCLUDED.identificador,
                status = EXCLUDED.status,
                status_validacao = EXCLUDED.status_validacao,
                validado = EXCLUDED.validado,
                nomes_anexos = EXCLUDED.nomes_anexos,
                resumo_ia = EXCLUDED.resumo_ia,
                observacao = EXCLUDED.observacao,
                data_chegada = EXCLUDED.data_chegada
        """, (
            id_email, acao_sugerida, processo, opaj, coerente, campos_faltantes,
            identificador, status, status_validacao, resultado_ia.get("valido"),
            nomes_anexos, resumo_ia, observacao
        ))

        # (Opcional: insere também em protocolos para controle/fluxo/fila)
        cur.execute("""
            INSERT INTO protocolos (
                id_email, status, motivo_invalido, criado_em, ultima_atualizacao,
                observacao, acao_usuario, hash_documento
            ) VALUES (%s, %s, %s, NOW(), NOW(), %s, %s, %s)
        """, (
            id_email, status, motivo_invalido, observacao, acao_sugerida, identificador
        ))

        logger.info(f"Resposta IA salva e protocolo criado para e-mail {id_email} com status '{status}'.")

    conn.commit()
    cur.close()
    conn.close()
    logger.info("Pipeline finalizado.")

# --- CONTROLE DE PAUSA DO PIPELINE ---
@router.post("/pipeline/pausar")
def pausar_pipeline():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO controle_pipeline (chave, valor)
        VALUES ('pausar_pipeline', 'true')
        ON CONFLICT (chave) DO UPDATE SET valor = 'true'
    """)
    conn.commit()
    cur.close()
    conn.close()
    return {"mensagem": "⛔ Pipeline pausado com sucesso."}

@router.post("/pipeline/retomar")
def retomar_pipeline():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE controle_pipeline SET valor = 'false' WHERE chave = 'pausar_pipeline'")
    conn.commit()
    cur.close()
    conn.close()
    return {"mensagem": "✅ Pipeline retomado com sucesso."}

@router.get("/pipeline/status")
def status_pipeline():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM controle_pipeline WHERE chave = 'pausar_pipeline'")
    valor = cur.fetchone()
    cur.close()
    conn.close()
    return {"pausado": (valor and valor[0] == "true")}

# --- CAPTURA E VALIDAÇÃO IA ---
@router.post("/captura-emails")
def executar_captura():
    from backend.captura_emails import capturar_emails
    capturar_emails()
    return {"status": "ok", "mensagem": "Captura de e-mails executada com sucesso."}

@router.post("/validar-ia")
def executar_validacao_ia(limite: Optional[int] = Query(None)):
    from backend.pipeline import pipeline
    pipeline(limite=limite)
    return {"status": "ok", "mensagem": f"Validação IA executada com sucesso (limite={limite or 'sem limite'})"}

# --- CONTAGEM CASOS E ESTEIRA --- 
@router.get("/painel-controle/contagem-casos")
def contagem_casos_em_processamento(
    tipo_email: str = Query("protocolo"),
    status: str = Query(None)
):
    conn = get_conn()
    cur = conn.cursor()
    query = """
        SELECT COUNT(DISTINCT p.id_protocolo)
        FROM protocolos p
        JOIN emails e ON e.id_email = p.id_email
        WHERE TRUE
    """
    params = []
    if tipo_email:
        query += " AND e.tipo_email = %s"
        params.append(tipo_email)
    if status:
        query += " AND p.status = %s"
        params.append(status)
    else:
        query += " AND p.status NOT IN ('protocolado', 'cancelado')"
    cur.execute(query, tuple(params))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"total": total}

@router.get("/esteira")
def esteira_protocolos(
    data: str = Query(None),
    status: str = Query(None),
    tipo_email: str = Query("protocolo"),
    limite: int = Query(100)
):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        SELECT 
            e.id_email, e.assunto, e.recebido_em, e.tipo_email, e.corpo_email,
            p.id_protocolo, p.id_resposta, p.status, p.acao_usuario, p.observacao, p.criado_em, p.ultima_atualizacao,
            r.tipo_resposta, r.processo, r.opaj, r.status_final
        FROM emails e
        LEFT JOIN protocolos p ON p.id_email = e.id_email
        LEFT JOIN respostas r ON r.id_resposta = p.id_resposta
        WHERE TRUE
    """
    params = []
    if tipo_email:
        query += " AND e.tipo_email = %s"
        params.append(tipo_email)
    if status:
        query += " AND p.status = %s"
        params.append(status)
    if data:
        query += " AND DATE(e.recebido_em) = %s"
        params.append(data)
    query += " ORDER BY COALESCE(p.criado_em, e.recebido_em) DESC"
    query += f" LIMIT {limite}"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    # Buscar os anexos de cada email:
    for row in rows:
        cur.execute("""
            SELECT id_anexo, nome_arquivo, tipo_arquivo
            FROM anexos_email WHERE id_email = %s
        """, (row['id_email'],))
        row['anexos'] = cur.fetchall()

    cur.close()
    conn.close()
    return {"esteira": rows}

