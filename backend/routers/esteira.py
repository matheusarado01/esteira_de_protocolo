# backend/routers/esteira.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

router = APIRouter()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# 1. PENDENTES DE PROTOCOLO
@router.get("/oficios/pendentes")
def listar_oficios_pendentes():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        query = """
            SELECT 
                e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
                v.acao_sugerida, v.motivo, v.coerencia, v.resultado,
                r.status_final,
                ARRAY_AGG(json_build_object(
                    'id_anexo', a.id_anexo,
                    'nome_arquivo', a.nome_arquivo,
                    'tipo_arquivo', a.tipo_arquivo
                )) as anexos
            FROM emails e
            JOIN respostas r ON r.id_email = e.id_email
            JOIN validacoes v ON v.id_resposta = r.id_resposta
            LEFT JOIN anexos_email a ON a.id_email = e.id_email
            WHERE v.acao_sugerida = 'protocolar'
              AND NOT EXISTS (
                SELECT 1 FROM protocolos p WHERE p.id_email = e.id_email AND p.acao_usuario = 'PROTOCOLAR'
              )
            GROUP BY e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
                     v.acao_sugerida, v.motivo, v.coerencia, v.resultado, r.status_final
            ORDER BY e.recebido_em DESC
            LIMIT 200
        """
        cur.execute(query)
        rows = cur.fetchall()
        resultados = []
        for row in rows:
            resultados.append({
                "id_email": row["id_email"],
                "assunto": row["assunto"],
                "remetente": row["remetente"],
                "recebido_em": row["recebido_em"].isoformat() if row["recebido_em"] else "",
                "corpo_email": row["corpo_email"],
                "acao_sugerida": row["acao_sugerida"],
                "motivo_ia": row["motivo"],
                "coerencia_ia": row["coerencia"],
                "resultado_ia": row["resultado"],
                "status_final": row["status_final"],
                "anexos": row["anexos"] or []
            })
        return {"oficios_pendentes": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 2. PROTOCOLADOS
@router.get("/oficios/protocolados")
def listar_oficios_protocolados():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        query = """
            SELECT 
                e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
                p.data_protocolo, p.usuario, p.nome_arquivo as recibo_nome,
                p.data_registro, p.id_protocolo,
                v.acao_sugerida, v.motivo, v.coerencia, v.resultado,
                r.status_final,
                ARRAY_AGG(json_build_object(
                    'id_anexo', a.id_anexo,
                    'nome_arquivo', a.nome_arquivo,
                    'tipo_arquivo', a.tipo_arquivo
                )) as anexos
            FROM protocolos p
            JOIN emails e ON e.id_email = p.id_email
            JOIN respostas r ON r.id_email = e.id_email
            JOIN validacoes v ON v.id_resposta = r.id_resposta
            LEFT JOIN anexos_email a ON a.id_email = e.id_email
            WHERE p.acao_usuario = 'PROTOCOLAR'
            GROUP BY e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
                     p.data_protocolo, p.usuario, p.nome_arquivo, p.data_registro, p.id_protocolo,
                     v.acao_sugerida, v.motivo, v.coerencia, v.resultado, r.status_final
            ORDER BY p.data_protocolo DESC
            LIMIT 200
        """
        cur.execute(query)
        rows = cur.fetchall()
        resultados = []
        for row in rows:
            resultados.append({
                "id_email": row["id_email"],
                "assunto": row["assunto"],
                "remetente": row["remetente"],
                "recebido_em": row["recebido_em"].isoformat() if row["recebido_em"] else "",
                "corpo_email": row["corpo_email"],
                "data_protocolo": row["data_protocolo"].isoformat() if row["data_protocolo"] else "",
                "usuario_protocolo": row["usuario"],
                "recibo_nome": row["recibo_nome"],
                "data_registro": row["data_registro"].isoformat() if row["data_registro"] else "",
                "id_protocolo": row["id_protocolo"],
                "acao_sugerida": row["acao_sugerida"],
                "motivo_ia": row["motivo"],
                "coerencia_ia": row["coerencia"],
                "resultado_ia": row["resultado"],
                "status_final": row["status_final"],
                "anexos": row["anexos"] or []
            })
        return {"oficios_protocolados": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 3. REPORTADOS/CORREÇÃO
@router.get("/oficios/reportados")
def listar_oficios_reportados():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        query = """
            SELECT 
                e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
                p.data_protocolo, p.usuario, p.nome_arquivo as recibo_nome,
                p.data_registro, p.id_protocolo, p.motivo_manual,
                v.acao_sugerida, v.motivo, v.coerencia, v.resultado,
                r.status_final,
                ARRAY_AGG(json_build_object(
                    'id_anexo', a.id_anexo,
                    'nome_arquivo', a.nome_arquivo,
                    'tipo_arquivo', a.tipo_arquivo
                )) as anexos
            FROM protocolos p
            JOIN emails e ON e.id_email = p.id_email
            JOIN respostas r ON r.id_email = e.id_email
            JOIN validacoes v ON v.id_resposta = r.id_resposta
            LEFT JOIN anexos_email a ON a.id_email = e.id_email
            WHERE p.acao_usuario = 'REPORTAR'
            GROUP BY e.id_email, e.assunto, e.remetente, e.recebido_em, e.corpo_email,
                     p.data_protocolo, p.usuario, p.nome_arquivo, p.data_registro, p.id_protocolo, p.motivo_manual,
                     v.acao_sugerida, v.motivo, v.coerencia, v.resultado, r.status_final
            ORDER BY p.data_protocolo DESC
            LIMIT 200
        """
        cur.execute(query)
        rows = cur.fetchall()
        resultados = []
        for row in rows:
            resultados.append({
                "id_email": row["id_email"],
                "assunto": row["assunto"],
                "remetente": row["remetente"],
                "recebido_em": row["recebido_em"].isoformat() if row["recebido_em"] else "",
                "corpo_email": row["corpo_email"],
                "data_reportado": row["data_protocolo"].isoformat() if row["data_protocolo"] else "",
                "usuario_reportou": row["usuario"],
                "recibo_nome": row["recibo_nome"],
                "data_registro": row["data_registro"].isoformat() if row["data_registro"] else "",
                "id_protocolo": row["id_protocolo"],
                "motivo_manual": row["motivo_manual"],
                "acao_sugerida": row["acao_sugerida"],
                "motivo_ia": row["motivo"],
                "coerencia_ia": row["coerencia"],
                "resultado_ia": row["resultado"],
                "status_final": row["status_final"],
                "anexos": row["anexos"] or []
            })
        return {"oficios_reportados": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 4. DETALHE DO OFÍCIO
@router.get("/oficios/{id_email}")
def detalhes_oficio(id_email: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Dados básicos
        cur.execute("""
            SELECT e.*, r.*, v.*, 
                ARRAY_AGG(json_build_object(
                    'id_anexo', a.id_anexo,
                    'nome_arquivo', a.nome_arquivo,
                    'tipo_arquivo', a.tipo_arquivo
                )) as anexos
            FROM emails e
            LEFT JOIN respostas r ON r.id_email = e.id_email
            LEFT JOIN validacoes v ON v.id_resposta = r.id_resposta
            LEFT JOIN anexos_email a ON a.id_email = e.id_email
            WHERE e.id_email = %s
            GROUP BY e.id_email, r.id_resposta, v.id_validacao
        """, (id_email,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ofício não encontrado")
        resultado = {k: row[k] for k in row.keys()}
        resultado["anexos"] = row["anexos"] or []
        # Protocolo/manual (se houver)
        cur.execute("""
            SELECT * FROM protocolos WHERE id_email = %s
        """, (id_email,))
        protocolos = cur.fetchall()
        resultado["protocolos"] = [dict(p) for p in protocolos] if protocolos else []
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 5. PROTOCOLAR OFÍCIO (UPLOAD DE RECIBO)
@router.post("/oficios/{id_email}/protocolar")
def protocolar_oficio(
    id_email: int,
    usuario: str = Form(...),
    file: UploadFile = File(...),
    observacao: str = Form(None)
):
    conn = get_conn()
    cur = conn.cursor()
    try:
        conteudo = file.file.read()
        cur.execute("""
            INSERT INTO protocolos
                (id_email, data_protocolo, hora_protocolo, usuario, acao_usuario, arquivo, nome_arquivo, observacao, data_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            id_email,
            datetime.now().date(),
            datetime.now().time(),
            usuario,
            "PROTOCOLAR",
            conteudo,
            file.filename,
            observacao
        ))
        conn.commit()
        return {"message": "Protocolo registrado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 6. REPORTAR DIVERGÊNCIA
@router.post("/oficios/{id_email}/reportar")
def reportar_oficio(
    id_email: int,
    usuario: str = Form(...),
    motivo_manual: str = Form(...),
    observacao: str = Form(None)
):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO protocolos
                (id_email, data_protocolo, hora_protocolo, usuario, acao_usuario, motivo_manual, observacao, data_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            id_email,
            datetime.now().date(),
            datetime.now().time(),
            usuario,
            "REPORTAR",
            motivo_manual,
            observacao
        ))
        conn.commit()
        return {"message": "Divergência reportada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 7. LISTAR ANEXOS DE UM OFÍCIO
@router.get("/oficios/{id_email}/anexos")
def listar_anexos_oficio(id_email: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("""
            SELECT id_anexo, nome_arquivo, tipo_arquivo
            FROM anexos_email
            WHERE id_email = %s
        """, (id_email,))
        anexos = cur.fetchall()
        return {"anexos": [dict(a) for a in anexos]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 8. DOWNLOAD DE ANEXO
@router.get("/oficios/anexo/{id_anexo}/download")
def download_anexo(id_anexo: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("SELECT nome_arquivo, conteudo, tipo_arquivo FROM anexos_email WHERE id_anexo = %s", (id_anexo,))
        anexo = cur.fetchone()
        if not anexo or not anexo["conteudo"]:
            raise HTTPException(status_code=404, detail="Anexo não encontrado")
        return StreamingResponse(
            content=anexo["conteudo"],
            media_type=anexo["tipo_arquivo"] or "application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={anexo['nome_arquivo']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
