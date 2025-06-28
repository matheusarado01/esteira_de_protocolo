#!/usr/bin/env python3
import os
import email
import poplib
import hashlib
import socket
from email import policy
from email.parser import BytesParser
from email.header import decode_header
from psycopg2 import connect
from datetime import datetime
from dotenv import load_dotenv
from backend.utils import log, get_conn

# Timeout global para todas as operações de rede (30s)
socket.setdefaulttimeout(30)

load_dotenv()

POP3_HOST = os.getenv("IMAP_HOST")
POP3_USER = os.getenv("IMAP_USER")
POP3_PASS = os.getenv("IMAP_PASS")
REMETENTE_ALVO = "respostaoficios@santander.com.br"

def decodificar(texto):
    if not texto:
        return ""
    partes = decode_header(texto)
    return ''.join([
        t.decode(enc or "utf-8", errors="ignore") if isinstance(t, bytes) else t
        for t, enc in partes
    ])

def capturar_emails():
    conn = get_conn()
    cur = conn.cursor()

    total_salvos = 0
    total_duplicados = 0
    total_falhas = 0

    try:
        mail = poplib.POP3_SSL(POP3_HOST, 995)
        mail.user(POP3_USER)
        mail.pass_(POP3_PASS)

        num_msgs = len(mail.list()[1])
        log(f"📨 {num_msgs} e-mails encontrados via POP3", "INFO")

        for i in range(num_msgs):
            try:
                log(f"Baixando e-mail {i+1}/{num_msgs}", "INFO")
                try:
                    response, lines, octets = mail.retr(i + 1)
                except Exception as e:
                    log(f"Timeout ou erro ao baixar e-mail #{i+1}: {e}", "ERRO")
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

                total_salvos += 1
                log(f"""
📦 [{i+1}/{num_msgs}]
🆔 Message-ID: {message_id}
📧 De: {addr}
📨 Assunto: {assunto}
📅 Recebido em: {recebido_em.strftime('%d/%m/%Y %H:%M')}
📝 Corpo: {corpo_texto.strip() if corpo_texto else '[sem corpo]'}
📎 Anexos salvos: {total_anexos}
""", "INFO")

            except Exception as e:
                total_falhas += 1
                log(f"❌ Erro ao processar e-mail #{i+1}: {e}", "ERRO")

    except Exception as e:
        log(f"❌ Erro na conexão POP3: {e}", "CRITICAL")

    finally:
        conn.commit()
        cur.close()
        conn.close()
        try:
            mail.quit()
        except Exception:
            pass

        print("\n📊 RESUMO FINAL")
        print(f"✔️ E-mails salvos: {total_salvos}")
        print(f"🔁 Duplicados ignorados: {total_duplicados}")
        print(f"❌ Falhas: {total_falhas}")

if __name__ == "__main__":
    capturar_emails()
