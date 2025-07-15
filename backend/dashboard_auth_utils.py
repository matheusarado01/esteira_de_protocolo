import psycopg2
import bcrypt
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
    "dbname": os.getenv("DB_NAME", "esteira_protocolo"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "486975"),
}

def get_conn():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Conexão com o banco estabelecida")
        return conn
    except psycopg2.Error as e:
        logger.critical(f"Erro ao conectar ao banco: {str(e)}")
        raise

def autenticar_usuario(username, senha):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT senha_hash, nome, perfil, ativo FROM usuarios WHERE username = %s", (username,))
                row = cur.fetchone()
                if row:
                    if row[3]:  # Verifica se ativo é True
                        senha_hash = row[0].encode('utf-8')
                        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash):
                            logger.info(f"Usuário {username} autenticado com sucesso")
                            return {
                                "username": username,
                                "nome": row[1],
                                "perfil": row[2]
                            }
                        else:
                            logger.warning(f"Senha incorreta para o usuário {username}")
                    else:
                        logger.warning(f"Usuário {username} está inativo")
                else:
                    logger.warning(f"Usuário {username} não encontrado")
                return None
    except psycopg2.Error as e:
        logger.error(f"Erro ao autenticar usuário {username}: {str(e)}")
        raise

def criar_usuario(username, senha, nome, perfil='usuario'):
    try:
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (nome, username, senha_hash, perfil, ativo) VALUES (%s, %s, %s, %s, TRUE)",
                    (nome, username, senha_hash, perfil)
                )
                conn.commit()
                logger.info(f"Usuário {username} criado com sucesso")
        return True
    except psycopg2.IntegrityError:
        logger.error(f"Usuário {username} já existe")
        raise
    except psycopg2.Error as e:
        logger.error(f"Erro ao criar usuário {username}: {str(e)}")
        raise

def usuario_existe(username):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM usuarios WHERE username=%s", (username,))
                return cur.fetchone() is not None
    except psycopg2.Error as e:
        logger.error(f"Erro ao verificar existência de usuário {username}: {str(e)}")
        raise

# NOVA FUNÇÃO para consulta do usuário pelo nome (sem validar senha de novo)
def buscar_usuario(username):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT nome, perfil, ativo FROM usuarios WHERE username = %s", (username,))
                row = cur.fetchone()
                if row and row[2]:  # ativo = True
                    return {
                        "username": username,
                        "nome": row[0],
                        "perfil": row[1]
                    }
                return None
    except psycopg2.Error as e:
        logger.error(f"Erro ao buscar usuário {username}: {str(e)}")
        raise

if __name__ == "__main__":
    import getpass
    print("Criação de novo usuário admin")
    username = input("Login de usuário: ")
    if usuario_existe(username):
        print("Usuário já existe.")
    else:
        nome = input("Nome completo: ")
        senha = getpass.getpass("Senha: ")
        try:
            criar_usuario(username, senha, nome, perfil="admin")
            print("Usuário criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
