# Script PowerShell para executar job com input interativo
Write-Host "=== CORTAI - Criar Novo Job ===" -ForegroundColor Cyan
Write-Host ""
$url = Read-Host "Digite a URL do vídeo do YouTube"

if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Host "ERRO: URL não pode ser vazia!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Enviando job para processamento..." -ForegroundColor Yellow
docker-compose run --rm backend python main.py --url "$url"

