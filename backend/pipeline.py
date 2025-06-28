import os
import io
import fitz  # PyMuPDF
from backend.utils import log, get_conn, extrair_referencias_assunto
from datetime import datetime
from dotenv import load_dotenv

from backend.ia_validador import validar_formal_ia
import traceback

load_dotenv()
USE_IA = os.getenv("USE_IA", "False").lower() == "true"

def classificar_anexo(nome, texto_pdf, tipo_arquivo):
    nome_low = (nome or "").lower().strip()
    # 1. Minuta de resposta (prioridade máxima)
    if any(x in nome_low for x in [
        "minuta de resposta", "minuta", "resposta", "resposta ofício", "oficio", "ofício"
    ]):
        return "minuta_resposta"
    if "assinatura" in nome_low or "certificado" in nome_low:
        return "comprovante_assinatura"
    if "extrato" in nome_low:
        return "extrato"
    if "comprovante" in nome_low and "assinatura" not in nome_low:
        return "comprovante"
    if "contrato" in nome_low:
        return "contrato"
    if "proposta" in nome_low:
        return "proposta"
    if "termo" in nome_low:
        return "termo"
    if "bloqueio" in nome_low:
        return "bloqueio"
    if nome_low.endswith(".zip") or tipo_arquivo == "application/zip":
        return "zip"
    texto_low = (texto_pdf or "").lower()
    if "extrato" in texto_low:
        return "extrato"
    if "comprovante" in texto_low and "assinatura" not in texto_low:
        return "comprovante"
    if "contrato" in texto_low:
        return "contrato"
    if "proposta" in texto_low:
        return "proposta"
    if "termo" in texto_low:
        return "termo"
    if "bloqueio" in texto_low:
        return "bloqueio"
    return "outro"

def extrair_texto_pdf(conteudo_pdf):
    try:
        with fitz.open(stream=conteudo_pdf, filetype="pdf") as doc:
            texto = ""
            for page in doc:
                texto += page.get_text()
        return texto
    except Exception as e:
        return f"ERRO_PDF: {str(e)}"

def pipeline():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT e.id_email, e.assunto, e.recebido_em, e.corpo_email
        FROM emails e
        JOIN anexos_email a ON e.id_email = a.id_email
        WHERE a.id_anexo NOT IN (SELECT id_anexo FROM respostas)
        ORDER BY e.recebido_em
    """)
    emails = cur.fetchall()

    total_processados = 0

    for e in emails:
        try:
            id_email, assunto, recebido_em, corpo_email = e

            cur.execute("""
                SELECT id_anexo, nome_arquivo, tipo_arquivo, conteudo
                FROM anexos_email
                WHERE id_email = %s
            """, (id_email,))
            anexos_email = cur.fetchall()

            log(f"----- Processando e-mail ID {id_email} | {len(anexos_email)} anexos")
            nomes_anexos = []
            textos_anexos = []
            tipos_anexos = []
            id_respostas = []
            tem_minuta = tem_assinatura = False

            processo, opaj, identificador, status_final, tipo_processo = extrair_referencias_assunto(assunto)

            for anexo in anexos_email:
                try:
                    id_anexo, nome_arquivo, tipo_arquivo, conteudo = anexo
                    nome = nome_arquivo or ""
                    texto_pdf = extrair_texto_pdf(conteudo) if "pdf" in (tipo_arquivo or "") else None
                    tipo = classificar_anexo(nome, texto_pdf, tipo_arquivo)
                    nomes_anexos.append(nome)
                    textos_anexos.append((texto_pdf or '')[:1000])
                    tipos_anexos.append(tipo)
                    status_parser = "ok"
                    obs = ""

                    if tipo == "minuta_resposta":
                        tem_minuta = True
                        obs = f"Minuta de resposta detectada ({len(texto_pdf or '')} caracteres)."
                    elif tipo == "comprovante_assinatura":
                        tem_assinatura = True
                        obs = "Comprovante de assinatura detectado."
                    elif tipo == "extrato":
                        obs = "Extrato bancário detectado."
                    elif tipo == "proposta":
                        obs = "Proposta detectada."
                    elif tipo == "contrato":
                        obs = "Contrato detectado."
                    elif tipo == "termo":
                        obs = "Termo detectado."
                    elif tipo == "comprovante":
                        obs = "Comprovante detectado."
                    elif tipo == "bloqueio":
                        obs = "Bloqueio detectado."
                    elif tipo == "zip":
                        obs = "Anexo ZIP identificado."
                    else:
                        obs = "Tipo de anexo não classificado."

                    if texto_pdf and texto_pdf.startswith("ERRO_PDF"):
                        obs = texto_pdf
                        status_parser = "erro"

                    erros_pg = [obs[:900]] if obs else []

                    cur.execute("""
                        INSERT INTO respostas
                            (id_anexo, id_email, tipo_resposta, processo, opaj, identificador, status_final, status_validacao, validado, erros, data_chegada, prazo_fatal)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_resposta
                    """, (
                        id_anexo, id_email, tipo, processo, opaj, identificador, status_final,
                        status_parser, True if status_parser == "ok" else False, erros_pg,
                        recebido_em if recebido_em else datetime.now(), None
                    ))
                    id_resposta = cur.fetchone()[0]
                    conn.commit()
                    id_respostas.append(id_resposta)
                    log(f"[{tipo.upper()}] {nome} | Status: {status_parser} | Obs: {obs[:100]}")

                except Exception as e:
                    log(f"[ERRO] Falha ao processar/salvar anexo do e-mail {id_email}: {str(e)}", "ERROR")
                    traceback.print_exc()
                    conn.rollback()
                    continue

            if USE_IA and id_respostas:
                try:
                    resultado_ia = validar_formal_ia(
                        assunto=assunto,
                        corpo=corpo_email,
                        nomes_anexos=nomes_anexos,
                        textos_anexos=textos_anexos,
                        campos_extraidos={
                            "processo": processo,
                            "opaj": opaj,
                            "identificador": identificador,
                            "status_final": status_final,
                            "tipo_processo": tipo_processo,
                            "tipos_anexos": tipos_anexos
                        },
                        model="gpt-4o"
                    )
                    for id_resposta in id_respostas:
                        cur.execute("""
                            INSERT INTO validacoes
                            (id_resposta, agente, resultado, motivo, coerencia, acao_sugerida, campos_faltantes, validador, data_validacao)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            id_resposta,
                            "ia_gpt4o",
                            resultado_ia.get("valido"),
                            resultado_ia.get("motivo"),
                            resultado_ia.get("coerencia"),
                            resultado_ia.get("acao_sugerida"),
                            resultado_ia.get("campos_faltantes") or [],
                            "gpt-4o",
                            datetime.now()
                        ))
                    conn.commit()
                    log(f"[IA] Validação formal IA salva: {resultado_ia}")
                except Exception as e:
                    log(f"Erro na validação formal IA (e-mail {id_email}): {str(e)}", "ERRO")
                    traceback.print_exc()
                    conn.rollback()

            if not tem_minuta:
                log(f"⚠️ E-mail {id_email} SEM minuta de resposta!", "ERRO")
            if not tem_assinatura:
                log(f"⚠️ E-mail {id_email} SEM comprovante de assinatura!", "ERRO")

            total_processados += len(anexos_email)

        except Exception as e:
            log(f"[ERRO] Falha geral ao processar e-mail {id_email}: {str(e)}", "ERROR")
            traceback.print_exc()
            conn.rollback()

    try:
        conn.commit()
    except Exception as e:
        log(f"[ERRO] Falha ao commitar no final: {str(e)}", "ERROR")
        traceback.print_exc()
    cur.close()
    conn.close()
    log(f"✅ Pipeline finalizado: {total_processados} anexos processados.")

if __name__ == "__main__":
    pipeline()
