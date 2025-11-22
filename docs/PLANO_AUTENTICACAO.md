# 🎯 Sistema de Autenticação - Plano Incremental Detalhado

## Filosofia: Qualidade > Velocidade
Cada fase será completamente implementada e testada antes de prosseguir para a próxima. Validação contínua.

---

## 📦 **FASE 1: Infraestrutura Database (Async SQLAlchemy + Alembic)**

### Objetivo
Configurar SQLAlchemy 2.0 assíncrono e Alembic para migrations.

### Arquivos a Criar
**1. `backend/src/database.py`**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.core.config import DATABASE_URL

# Engine assíncrono
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# Dependency para FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**2. Atualizar `backend/src/core/config.py`**
```python
# Adicionar variável DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cortai:cortai_password@postgres:5432/cortai")
```

**3. Inicializar Alembic**
```bash
cd backend
alembic init alembic
```

**4. Configurar `backend/alembic.ini`**
```ini
# Remover sqlalchemy.url hardcoded
# sqlalchemy.url =
```

**5. Configurar `backend/alembic/env.py`**
```python
from src.database import Base
from src.core.config import DATABASE_URL
import asyncio

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=DATABASE_URL.replace('+asyncpg', ''),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    from sqlalchemy.ext.asyncio import create_async_engine
    connectable = create_async_engine(DATABASE_URL)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### Dependências Necessárias
- `asyncpg` (driver PostgreSQL assíncrono)

### Validação
```bash
# Testar conexão
python -c "from src.database import engine; import asyncio; asyncio.run(engine.connect())"

# Criar primeira migration vazia
alembic revision -m "initial"
alembic upgrade head
```

---

## 📦 **FASE 2: Modelo User + Migration**

### Objetivo
Criar modelo User no banco usando melhores práticas SQLAlchemy 2.0.

### Arquivos a Criar
**1. `backend/src/models/user.py`**
```python
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
```

**2. `backend/src/models/__init__.py`**
```python
from src.models.user import User

__all__ = ["User"]
```

**3. Atualizar `backend/alembic/env.py`**
```python
# Importar todos os models antes de target_metadata
from src.models import User  # Garante que Base.metadata tenha todas as tabelas
target_metadata = Base.metadata
```

### Validação
```bash
# Gerar migration automática
alembic revision --autogenerate -m "create users table"

# Revisar migration gerada em alembic/versions/

# Aplicar migration
alembic upgrade head

# Validar no banco
docker exec -it cortai-postgres psql -U cortai -c "\d users"
```

---

## 📦 **FASE 3: Sistema de Segurança (JWT + Password)**

### Objetivo
Implementar utilitários para hash de senha e JWT tokens seguros.

### Arquivos a Criar
**1. `backend/src/utils/security.py`**
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing com bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera hash bcrypt da senha"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica e valida JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
```

**2. Atualizar `backend/src/core/config.py`**
```python
# Adicionar configurações JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
```

### Validação
```python
# Testar em shell Python
from src.utils.security import get_password_hash, verify_password, create_access_token, decode_access_token

# Hash password
hashed = get_password_hash("senha123")
assert verify_password("senha123", hashed) == True
assert verify_password("senha_errada", hashed) == False

# JWT
token = create_access_token({"sub": "user@example.com"})
payload = decode_access_token(token)
assert payload["sub"] == "user@example.com"
```

---

## 📦 **FASE 4: Schemas Pydantic + Endpoints de Autenticação**

### Objetivo
Criar endpoints de registro, login e obtenção de usuário atual.

### Arquivos a Criar
**1. `backend/src/schemas/auth.py`**
**2. `backend/src/api/dependencies/auth.py`**
**3. `backend/src/api/routes/auth.py`**
**4. Registrar router em `backend/src/main.py`**

### Validação
```bash
# Testar com curl ou HTTPie
http POST localhost:8000/api/v1/auth/register email=teste@example.com password=senha123 name="Usuario Teste"
http POST localhost:8000/api/v1/auth/login username=teste@example.com password=senha123
http GET localhost:8000/api/v1/auth/me "Authorization: Bearer {TOKEN}"
```

---

## 📦 **FASE 5: Modelo Video + Relacionamento com User**

### Objetivo
Criar modelo Video com foreign key para User.

---

## 📦 **FASE 6: Refatorar Rotas de Vídeos com Auth**

### Objetivo
Proteger rotas de vídeos e persistir no banco.

---

## 📦 **FASE 7: Frontend - Auth Store + API Client com Axios**

### Objetivo
Implementar gerenciamento de autenticação no frontend com persist.

---

## 📦 **FASE 8: Frontend - Páginas Login/Registro**

### Objetivo
Criar telas de autenticação com validação.

---

## 📦 **FASE 9: Frontend - Atualizar Rotas + Sidebar**

### Objetivo
Proteger rotas privadas e adicionar logout no sidebar.

---

## 📦 **FASE 10: Frontend - Biblioteca de Highlights**

### Objetivo
Criar página "Biblioteca" mostrando vídeos processados do usuário.

---

## 📦 **FASE 11: Testes End-to-End**

### Checklist
- [ ] Registro de novo usuário
- [ ] Login e persistência de token
- [ ] Redirecionamento para /login quando não autenticado
- [ ] Processamento de vídeo associado ao usuário
- [ ] Listagem de vídeos apenas do usuário logado
- [ ] Logout e limpeza de token
- [ ] Biblioteca mostrando highlights processados

---

## ⏱️ Estimativa Realista
- **Fases 1-3**: ~2-3 horas (Infraestrutura)
- **Fases 4-6**: ~3-4 horas (Backend Auth)
- **Fases 7-10**: ~3-4 horas (Frontend)
- **Fase 11**: ~1 hora (Testes)
- **Total**: ~9-12 horas de desenvolvimento focado e incremental

## 📝 Notas Importantes
- Cada fase pode ser commitada separadamente
- Validar antes de prosseguir
- Usar `asyncpg` no requirements.txt
- Documentar endpoints conforme criamos
