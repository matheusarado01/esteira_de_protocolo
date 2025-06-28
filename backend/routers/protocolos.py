from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
import psycopg2
import psycopg2.extras
import re
import io
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.dashboard_auth_utils import autenticar_usuario

load_dotenv()

router = APIRouter()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
}

def get_conn():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Conexão com o banco estabelecida")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao banco: {str(e)}")

def extrair_processo(texto: str) -> str:
    match = re.search(r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{1,2}\.\d{4}", texto)
    return match.group(0) if match else ""

def extrair_opaj(texto: str) -> str:
    match = re.search(r"\b\d{7}\b", texto)
    return match.group(0) if match else ""

def tem_zip(caminho: str) -> bool:
    return caminho.endswith(".zip") if caminho else False

def tem_pdf(caminho: str) -> bool:
    return caminho.endswith(".pdf") if caminho else False

@router.get("/protocolos")
async def listar_protocolos():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT 
            e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
            r.tipo_resposta, r.processo, r.opaj, r.status_final, r.ramo_justica,
            r.tribunal_nome, r.estado, r.prazo_fatal, r.nomes_anexos,
            v.motivo, -- AJUSTADO AQUI
            a.id_anexo, a.nome_arquivo, a.tipo_arquivo
        FROM emails e
        LEFT JOIN respostas r ON r.id_email = e.id_email
        LEFT JOIN validacoes v ON v.id_resposta = r.id_resposta
        LEFT JOIN anexos_email a ON a.id_email = e.id_email
        ORDER BY e.recebido_em DESC
        LIMIT 200
    """
    try:
        cur.execute(query)
        rows = cur.fetchall()

        resultados = []
        for row in rows:
            processo = row["processo"] or extrair_processo(row["corpo_email"] or row["assunto"])
            tribunal = row["tribunal_nome"] or ("TJSP" if ".8.26." in processo else "TRT" if ".5." in processo else "")
            resultado = {
                "id_email": row["id_email"],
                "assunto": row["assunto"],
                "remetente": row["remetente"],
                "recebido_em": row["recebido_em"].isoformat() if row["recebido_em"] else "",
                "processo": processo,
                "opaj": row["opaj"] or extrair_opaj(row["corpo_email"] or ""),
                "tribunal": tribunal,
                "ramo_justica": row["ramo_justica"] or "",
                "estado": row["estado"] or "",
                "prazo_fatal": row["prazo_fatal"].isoformat() if row["prazo_fatal"] else "",
                "tipo_resposta": row["tipo_resposta"] or "",
                "status_final": row["status_final"] or "",
                "motivo": row["motivo"] or "",    # <-- Só motivo agora!
                "tem_zip": tem_zip(row["nome_arquivo"] or ""),
                "tem_pdf": tem_pdf(row["nome_arquivo"] or ""),
                "id_anexo": row["id_anexo"],
                "nome_anexo": row["nome_arquivo"],
            }
            resultados.append(resultado)
        logger.info("Lista de protocolos retornada com sucesso")
    except psycopg2.Error as e:
        logger.error(f"Erro ao consultar protocolos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar protocolos: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return {"protocolos": resultados}

@router.get("/protocolos/{id_email}")
async def get_protocolo(id_email: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
        SELECT 
            e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
            r.tipo_resposta, r.processo, r.opaj, r.status_final, r.ramo_justica,
            r.tribunal_nome, r.estado, r.prazo_fatal, r.nomes_anexos,
            v.motivo, -- AJUSTADO AQUI
            a.id_anexo, a.nome_arquivo, a.tipo_arquivo
        FROM emails e
        LEFT JOIN respostas r ON r.id_email = e.id_email
        LEFT JOIN validacoes v ON v.id_resposta = r.id_resposta
        LEFT JOIN anexos_email a ON a.id_email = e.id_email
        WHERE e.id_email = %s
    """
    try:
        cur.execute(query, (id_email,))
        row = cur.fetchone()

        if not row:
            logger.warning(f"Protocolo com id_email {id_email} não encontrado")
            raise HTTPException(status_code=404, detail="Protocolo não encontrado")

        processo = row["processo"] or extrair_processo(row["corpo_email"] or row["assunto"])
        tribunal = row["tribunal_nome"] or ("TJSP" if ".8.26." in processo else "TRT" if ".5." in processo else "")
        resultado = {
            "id_email": row["id_email"],
            "assunto": row["assunto"],
            "remetente": row["remetente"],
            "recebido_em": row["recebido_em"].isoformat() if row["recebido_em"] else "",
            "processo": processo,
            "opaj": row["opaj"] or extrair_opaj(row["corpo_email"] or ""),
            "tribunal": tribunal,
            "ramo_justica": row["ramo_justica"] or "",
            "estado": row["estado"] or "",
            "prazo_fatal": row["prazo_fatal"].isoformat() if row["prazo_fatal"] else "",
            "tipo_resposta": row["tipo_resposta"] or "",
            "status_final": row["status_final"] or "",
            "motivo": row["motivo"] or "",
            "tem_zip": tem_zip(row["nome_arquivo"] or ""),
            "tem_pdf": tem_pdf(row["nome_arquivo"] or ""),
            "id_anexo": row["id_anexo"],
            "nome_anexo": row["nome_arquivo"],
        }
        logger.info(f"Protocolo com id_email {id_email} retornado com sucesso")
        return resultado
    except psycopg2.Error as e:
        logger.error(f"Erro ao consultar protocolo {id_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar protocolo: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.get("/anexos/{id_anexo}")
async def download_anexo(id_anexo: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT nome_arquivo, conteudo FROM anexos_email WHERE id_anexo = %s", (id_anexo,))
        anexo = cur.fetchone()

        if not anexo or not anexo["conteudo"]:
            logger.warning(f"Anexo com id_anexo {id_anexo} não encontrado")
            raise HTTPException(status_code=404, detail="Anexo não encontrado")

        logger.info(f"Anexo com id_anexo {id_anexo} enviado com sucesso")
        return StreamingResponse(
            io.BytesIO(anexo["conteudo"]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={anexo['nome_arquivo']}"},
        )
    except psycopg2.Error as e:
        logger.error(f"Erro ao baixar anexo {id_anexo}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao baixar anexo: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.post("/protocolos/{id_email}/upload")
async def upload_recibo(id_email: int, file: UploadFile = File(...)):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id_email FROM emails WHERE id_email = %s", (id_email,))
        if not cur.fetchone():
            logger.warning(f"Protocolo com id_email {id_email} não encontrado")
            raise HTTPException(status_code=404, detail="Protocolo não encontrado")

        conteudo = await file.read()

        cur.execute(
            """
            INSERT INTO protocolos (
                id_email, data_protocolo, hora_protocolo, usuario, acao_usuario, nome_arquivo, arquivo, data_registro
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id_protocolo
            """,
            (
                id_email,
                datetime.now().date(),
                datetime.now().time(),
                "system",
                "UPLOAD_RECIBO",
                file.filename,
                conteudo,
            ),
        )
        conn.commit()
        logger.info(f"Recibo enviado com sucesso para id_email {id_email}")
        return {"message": "Recibo enviado com sucesso", "filename": file.filename}
    except psycopg2.Error as e:
        logger.error(f"Erro ao enviar recibo para id_email {id_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar recibo: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.post("/protocolos/{id_email}/divergencia")
async def registrar_divergencia(id_email: int, divergencia: Dict):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id_email FROM emails WHERE id_email = %s", (id_email,))
        if not cur.fetchone():
            logger.warning(f"Protocolo com id_email {id_email} não encontrado")
            raise HTTPException(status_code=404, detail="Protocolo não encontrado")

        cur.execute("SELECT id_resposta FROM respostas WHERE id_email = %s", (id_email,))
        resposta = cur.fetchone()
        if not resposta:
            logger.warning(f"Resposta para id_email {id_email} não encontrada")
            raise HTTPException(status_code=404, detail="Resposta não encontrada")

        motivo = divergencia.get("motivo")
        cur.execute(
            """
            INSERT INTO validacoes (id_resposta, agente, resultado, motivo, data_validacao)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (resposta[0], "system", False, motivo),
        )
        cur.execute(
            """
            UPDATE respostas SET status_final = %s WHERE id_email = %s
            """,
            ("EM CORREÇÃO", id_email),
        )
        conn.commit()
        logger.info(f"Divergência registrada com sucesso para id_email {id_email}")
        return {"message": "Divergência registrada com sucesso"}
    except psycopg2.Error as e:
        logger.error(f"Erro ao registrar divergência para id_email {id_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao registrar divergência: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.get("/relatorios")
async def gerar_relatorio(data_inicio: str = None, data_fim: str = None, tribunal: str = None, status: str = None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        query = """
            SELECT 
                e.id_email, e.assunto, e.remetente, e.recebido_em,
                r.processo, r.tribunal_nome, r.ramo_justica, r.estado, 
                r.status_final, r.prazo_fatal, r.tipo_resposta,
                v.motivo -- AJUSTADO AQUI
            FROM emails e
            LEFT JOIN respostas r ON r.id_email = e.id_email
            LEFT JOIN validacoes v ON v.id_resposta = r.id_resposta
            WHERE (%s IS NULL OR e.recebido_em >= %s)
            AND (%s IS NULL OR e.recebido_em <= %s)
            AND (%s IS NULL OR r.tribunal_nome = %s)
            AND (%s IS NULL OR r.status_final = %s)
            ORDER BY e.recebido_em DESC
        """
        cur.execute(query, (data_inicio, data_inicio, data_fim, data_fim, tribunal, tribunal, status, status))
        rows = cur.fetchall()

        dados = [
            {
                "id_email": row["id_email"],
                "assunto": row["assunto"],
                "remetente": row["remetente"],
                "recebido_em": row["recebido_em"].isoformat() if row["recebido_em"] else "",
                "processo": row["processo"],
                "tribunal": row["tribunal_nome"],
                "ramo_justica": row["ramo_justica"],
                "estado": row["estado"],
                "status_final": row["status_final"],
                "prazo_fatal": row["prazo_fatal"].isoformat() if row["prazo_fatal"] else "",
                "tipo_resposta": row["tipo_resposta"],
                "motivo": row["motivo"],
            }
            for row in rows
        ]

        df = pd.DataFrame(dados)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        logger.info("Relatório gerado com sucesso")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=relatorio_protocolos.xlsx"},
        )
    except psycopg2.Error as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.post("/login")
async def login(credentials: Dict):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        logger.info(f"Tentativa de login para usuário {username}")
        usuario = autenticar_usuario(username, password)
        if not usuario:
            logger.warning(f"Falha no login para usuário {username}")
            raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
        logger.info(f"Login bem-sucedido para usuário {username}")
        return {
            "token": "fake-jwt-token",
            "username": usuario["username"]
        }
    except psycopg2.Error as e:
        logger.error(f"Erro ao autenticar usuário {credentials.get('username')}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao autenticar: {str(e)}")
    finally:
        cur.close()
        conn.close()
