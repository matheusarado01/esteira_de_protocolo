from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

from backend.dashboard_auth_utils import autenticar_usuario, buscar_usuario
from backend.routers import protocolos
from backend.routers.protocolos import download_anexo_publico  # ✅ nova rota pública

# Configurações do JWT
SECRET_KEY = os.getenv("SECRET_KEY", "segredo-muito-seguro")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Inicializa o app
app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou restrinja a ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = autenticar_usuario(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "nome": user["nome"],
        "perfil": user["perfil"]
    }

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = buscar_usuario(username)
    if not user:
        raise credentials_exception
    return user

@app.get("/api/user/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "nome": current_user["nome"],
        "perfil": current_user["perfil"]
    }

# Rotas protegidas (com prefixo /api)
app.include_router(protocolos.router, prefix="/api")

# ✅ Rota pública de download direto de anexo
app.add_api_route(
    "/download-anexo/{id_anexo}",
    endpoint=download_anexo_publico,
    methods=["GET"],
    name="Download Anexo Público"
)
