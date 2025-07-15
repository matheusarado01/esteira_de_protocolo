import os
import email
import poplib
import json
import socket
from email import policy
from email.parser import BytesParser
from email.header import decode_header
from psycopg2 import connect
from datetime import datetime
from dotenv import load_dotenv
from backend.utils import log, get_conn

socket.setdefaulttimeout(30)
load_dotenv()

POP3_HOST = os.getenv("IMAP_HOST")
POP3_USER = os.getenv("IMAP_USER")
POP3_PASS = os.getenv("IMAP_PASS")
REMETENTE_ALVO = "respostaoficios@santander.com.br"
PROGRESS_FILE = "progress_captura.json"
LOG_FILE = "log_captura_tmp.json"

def limpar_logs_anteriores():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

def log_frontend(msg, tipo="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    registro = {"tipo": tipo, "mensagem": msg, "timestamp": timestamp}
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro) + "\n")
    except:
        pass
    log(msg, tipo)

def salvar_progresso(total, atual):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"total": total, "atual": atual, "finalizado": False}, f)

def finalizar_progresso():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r+", encoding="utf-8") as f:
            progresso = json.load(f)
            progresso["finalizado"] = True
            f.seek(0)
            json.dump(progresso, f)
            f.truncate()

def decodificar(texto):
    if not texto:
        return ""
    partes = decode_header(texto)
    return ''.join([
        t.decode(enc or "utf-8", errors="ignore") if isinstance(t, bytes) else t
        for t, enc in partes
    ])

def pipeline_pausado():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM controle_pipeline WHERE chave = 'pausar_pipeline'")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row and row[0].lower() == "true"

def capturar_emails():
    if pipeline_pausado():
        log_frontend("🚫 Pipeline pausado. Captura de e-mails cancelada.", "WARNING")
        return {"mensagem": "Pipeline pausado. Captura cancelada."}

    limpar_logs_anteriores()
    conn = get_conn()
    cur = conn.cursor()

    total_salvos = 0
    total_duplicados = 0
    total_falhas = 0
    mail = None

    try:
        mail = poplib.POP3_SSL(POP3_HOST, 995)
        mail.user(POP3_USER)
        mail.pass_(POP3_PASS)

        num_msgs = len(mail.list()[1])
        salvar_progresso(num_msgs, 0)
        log_frontend(f"📨 {num_msgs} e-mails encontrados via POP3")

        for i in range(num_msgs):
            salvar_progresso(num_msgs, i)
            try:
                log_frontend(f"Baixando e-mail {i+1}/{num_msgs}")
                try:
                    response, lines, octets = mail.retr(i + 1)
                except Exception as e:
                    log_frontend(f"Timeout ou erro ao baixar e-mail #{i+1}: {e}", "ERROR")
                    total_falhas += 1
                    continue

                raw_email = b"\n".join(lines)
                msg = BytesParser(policy=policy.default).parsebytes(raw_email)

                hdr_from = decodificar(msg["From"])
                _, addr = email.utils.parseaddr(hdr_from)
                if addr.lower() != REMETENTE_ALVO:
                    continue

                message_id = msg.get("Message-ID") or f"<POP3-MSG-{i+1}>"
                cur.execute("SELECT 1 FROM emails WHERE message_id = %s", (message_id,))
                if cur.fetchone():
                    total_duplicados += 1
                    log_frontend(f"🔁 E-mail #{i+1} já registrado — ignorado.")
                    continue

                assunto = decodificar(msg.get("Subject", ""))
                corpo = msg.get_body(preferencelist=('plain', 'html'))
                corpo_texto = corpo.get_content().strip() if corpo else None

                date_hdr = msg.get("Date", "")
                try:
                    recebido_em = datetime.strptime(date_hdr[:31], "%a, %d %b %Y %H:%M:%S %z")
                except:
                    recebido_em = datetime.now()

                cur.execute("""
                    INSERT INTO emails (remetente, assunto, recebido_em, message_id, corpo_email)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_email
                """, (addr, assunto, recebido_em, message_id, corpo_texto))
                id_email = cur.fetchone()[0]

                total_anexos = 0
                for part in msg.iter_attachments():
                    nome = decodificar(part.get_filename() or "sem_nome")
                    tipo = part.get_content_type()
                    conteudo = part.get_payload(decode=True)
                    if conteudo:
                        cur.execute("""
                            INSERT INTO anexos_email (id_email, nome_arquivo, tipo_arquivo, conteudo)
                            VALUES (%s, %s, %s, %s)
                        """, (id_email, nome, tipo, conteudo))
                        total_anexos += 1

                if total_anexos == 0:
                    obs = "E-mail sem anexo. Não é possível realizar análise completa."
                    cur.execute("""
                        INSERT INTO respostas (
                            id_email, tipo_resposta, status_validacao, validado, erros, data_chegada, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id_email, "sem_anexo", "erro", False, [obs], recebido_em, "sem_anexo"
                    ))
                    log_frontend(f"⚠️ E-mail {id_email} salvo sem anexo.", "WARNING")

                elif not corpo_texto or len(corpo_texto.strip()) < 20:
                    obs = "Corpo da mensagem está vazio ou fora do padrão esperado."
                    cur.execute("""
                        INSERT INTO respostas (
                            id_email, tipo_resposta, status_validacao, validado, erros, data_chegada, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id_email, "fora_do_padrao", "erro", False, [obs], recebido_em, "fora_do_padrao"
                    ))
                    log_frontend(f"⚠️ E-mail {id_email} com corpo fora do padrão.", "WARNING")

                total_salvos += 1

            except Exception as e:
                total_falhas += 1
                log_frontend(f"❌ Erro ao processar e-mail #{i+1}: {e}", "ERROR")

    except Exception as e:
        log_frontend(f"❌ Erro na conexão POP3: {e}", "CRITICAL")

    finally:
        conn.commit()
        cur.close()
        conn.close()
        if mail:
            try:
                mail.quit()
            except Exception:
                pass

        finalizar_progresso()
        log_frontend(f"📊 RESUMO FINAL\n✔️ E-mails salvos: {total_salvos}\n🔁 Duplicados ignorados: {total_duplicados}\n❌ Falhas: {total_falhas}")
