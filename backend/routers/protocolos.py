# backend/routers/protocolos.py

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
from backend.utils import get_conn

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

# --- LISTAGEM PRINCIPAL DE PROTOCOLOS (NOVA BASE: TABELA PROTOCOLOS) ---

@router.get("/protocolos")
def listar_protocolos(
    data: str = Query(None),
    status: str = Query(None),
    tipo_email: str = Query("protocolo"),
    limite: int = Query(200)
):
    """
    Listagem principal, puxando protocolos, status, dados do e-mail, anexos etc.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        SELECT 
            p.id_protocolo, p.id_email, p.id_resposta, p.status, p.acao_usuario,
            p.hash_documento, p.hash_email, p.observacao, p.motivo_invalido,
            p.criado_em, p.ultima_atualizacao,
            e.assunto, e.remetente, e.recebido_em, e.corpo_email, e.tipo_email,
            r.tipo_resposta, r.processo, r.opaj, r.status_final,
            r.acao_sugerida, r.status_validacao, r.motivo_invalido,
            a.id_anexo, a.nome_arquivo, a.tipo_arquivo
        FROM protocolos p
        JOIN emails e ON e.id_email = p.id_email
        LEFT JOIN respostas r ON r.id_resposta = p.id_resposta
        LEFT JOIN anexos_email a ON a.id_email = p.id_email
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
    query += " ORDER BY p.criado_em DESC"
    query += f" LIMIT {limite}"

    try:
        cur.execute(query, tuple(params))
        resultados = []
        for row in cur.fetchall():
            row["tem_zip"] = tem_zip(row["nome_arquivo"] or "")
            row["tem_pdf"] = tem_pdf(row["nome_arquivo"] or "")
            resultados.append(row)
        logger.info("Lista de protocolos retornada com sucesso")
        return {"protocolos": resultados}
    except Exception as e:
        logger.error(f"Erro ao consultar protocolos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar protocolos: {str(e)}")
    finally:
        cur.close()
        conn.close()


# --- LISTAR SÓ PROTOCOLOS DE COMUNICAÇÕES / CANCELAMENTOS ---
@router.get("/comunicacoes")
def listar_comunicacoes(data: str = Query(None), tipo: str = Query(None)):
    """
    Lista comunicações e cancelamentos (tipo_email <> protocolo)
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        SELECT e.id_email, e.assunto, e.remetente, e.recebido_em, e.tipo_email, e.corpo_email
        FROM emails e
        WHERE e.tipo_email <> 'protocolo'
    """
    params = []
    if tipo:
        query += " AND e.tipo_email = %s"
        params.append(tipo)
    if data:
        query += " AND DATE(e.recebido_em) = %s"
        params.append(data)
    query += " ORDER BY e.recebido_em DESC LIMIT 200"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"comunicacoes": rows}

# --- DETALHE DO PROTOCOLO ---
@router.get("/protocolos/{id_protocolo}")
def detalhe_protocolo(id_protocolo: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.*, e.assunto, e.remetente, e.corpo_email, e.recebido_em, r.*, a.*
        FROM protocolos p
        JOIN emails e ON e.id_email = p.id_email
        LEFT JOIN respostas r ON r.id_resposta = p.id_resposta
        LEFT JOIN anexos_email a ON a.id_email = p.id_email
        WHERE p.id_protocolo = %s
        LIMIT 1
    """, (id_protocolo,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    return row

# --- PROTOCOLAR OFÍCIO (UPLOAD DE RECIBO) ---
@router.post("/protocolos/{id_protocolo}/upload_recibo")
async def upload_recibo(
    id_protocolo: int,
    usuario: str = Form(...),
    file: UploadFile = File(...),
    observacao: str = Form("")
):
    conn = get_conn()
    cur = conn.cursor()
    contents = await file.read()
    cur.execute("""
        UPDATE protocolos
        SET acao_usuario='protocolado', usuario_protocolo=%s, protocolado_em=NOW(),
            recibo_protocolo=%s, observacao=%s
        WHERE id_protocolo=%s
    """, (
        usuario, file.filename, observacao, id_protocolo
    ))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Recibo protocolado com sucesso."}

# --- REPORTAR DIVERGÊNCIA ---
@router.post("/protocolos/{id_protocolo}/divergencia")
async def registrar_divergencia(
    id_protocolo: int,
    usuario: str = Form(...),
    motivo_manual: str = Form(...),
    observacao: str = Form("")
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO divergencias (id_protocolo, usuario, motivo_manual, observacao, data_registro)
        VALUES (%s, %s, %s, %s, NOW())
    """, (id_protocolo, usuario, motivo_manual, observacao))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Divergência registrada com sucesso"}

# --- DOWNLOAD DE ANEXO ---
@router.get("/anexos/{id_anexo}/download")
def download_anexo_publico(id_anexo: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT nome_arquivo, tipo_arquivo, conteudo
        FROM anexos_email
        WHERE id_anexo = %s
    """, (id_anexo,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    if not resultado:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    nome_arquivo = resultado["nome_arquivo"]
    tipo_arquivo = resultado["tipo_arquivo"] or "application/octet-stream"
    conteudo = resultado["conteudo"]
    if not conteudo:
        raise HTTPException(status_code=404, detail="Conteúdo do anexo está vazio")
    return StreamingResponse(io.BytesIO(conteudo), media_type=tipo_arquivo, headers={
        "Content-Disposition": f'attachment; filename="{nome_arquivo}"'
    })

# --- RELATÓRIO EM EXCEL ---
@router.get("/protocolos/relatorio")
def gerar_relatorio_protocolos(
    data_inicio: str = Query(None),
    data_fim: str = Query(None),
    status: str = Query(None),
    tipo_email: str = Query("protocolo"),
):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = """
        SELECT
            p.*, e.assunto, e.remetente, e.recebido_em, e.tipo_email, r.tipo_resposta, r.processo, r.opaj
        FROM protocolos p
        JOIN emails e ON e.id_email = p.id_email
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
    if data_inicio:
        query += " AND e.recebido_em::date >= %s"
        params.append(data_inicio)
    if data_fim:
        query += " AND e.recebido_em::date <= %s"
        params.append(data_fim)
    query += " ORDER BY p.criado_em DESC"
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        raise HTTPException(status_code=400, detail="Nenhum protocolo encontrado.")
    df = pd.DataFrame(rows)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Protocolos", index=False)
        writer.sheets["Protocolos"].autofilter(0, 0, len(df), len(df.columns) - 1)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": "attachment; filename=protocolos.xlsx"})

# --- CONTROLE DE PAUSA DO PIPELINE (SEM ALTERAÇÃO) ---
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

# --- CAPTURA E VALIDAÇÃO IA (SEM ALTERAÇÃO) ---
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

# --- CONTAGEM CASOS E ESTEIRA (EXEMPLO) ---
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


@router.get("/captura-emails/progresso")
def progresso_captura():
    progress_file = "progress_captura.json"
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data
            except Exception:
                return {"total": 0, "atual": 0, "finalizado": False, "erro": "Arquivo corrompido"}
    return {"total": 0, "atual": 0, "finalizado": False, "erro": "Sem progresso disponível"}

@router.post("/captura-emails/stop")
def stop_captura():
    with open("progress_captura.json", "w") as f:
        json.dump({"status": "cancelado"}, f)
    return {"status": "cancelado"}
