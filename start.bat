@echo off
REM Script para iniciar o sistema CortAI completo

echo ========================================
echo   Iniciando CortAI - Sistema Completo
echo ========================================
echo.

echo [1/4] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao encontrado! Instale o Docker Desktop.
    pause
    exit /b 1
)
echo OK - Docker instalado

echo.
echo [2/4] Parando containers antigos...
docker-compose down

echo.
echo [3/4] Iniciando servicos com Docker Compose...
docker-compose up -d

echo.
echo [4/4] Aguardando servicos iniciarem (30s)...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo   Sistema Iniciado!
echo ========================================
echo.
echo Servicos disponiveis:
echo   - Frontend:        http://localhost:5173
echo   - Backend API:     http://localhost:8000
echo   - API Docs:        http://localhost:8000/docs
echo   - RabbitMQ Admin:  http://localhost:15672
echo     User: cortai / Pass: cortai_password
echo.
echo Workers ativos:
docker-compose ps
echo.
echo Para ver logs: docker-compose logs -f
echo Para parar:    docker-compose down
echo.
pause
