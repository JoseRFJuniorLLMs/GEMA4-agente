# GEMMA-AGENT — Script de Instalação e Inicialização
# Execute: .\run.ps1

Write-Host ""
Write-Host "  ◆ GEMMA-AGENT Setup" -ForegroundColor Cyan
Write-Host "  Agente de Desenvolvimento Autônomo Local" -ForegroundColor DarkCyan
Write-Host ""

$AgentDir = $PSScriptRoot
$PythonCmd = "python"

# Verifica Python
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow
try {
    $pyVersion = & $PythonCmd --version 2>&1
    Write-Host "      ✅ $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "      ❌ Python não encontrado. Instale em python.org" -ForegroundColor Red
    exit 1
}

# Verifica/cria ambiente virtual
$VenvPath = Join-Path $AgentDir ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "[2/4] Criando ambiente virtual..." -ForegroundColor Yellow
    & $PythonCmd -m venv $VenvPath
    Write-Host "      ✅ Ambiente virtual criado em .venv/" -ForegroundColor Green
} else {
    Write-Host "[2/4] ✅ Ambiente virtual já existe." -ForegroundColor Green
}

# Ativa o ambiente virtual
$PipCmd   = Join-Path $VenvPath "Scripts\pip.exe"
$PythonVenv = Join-Path $VenvPath "Scripts\python.exe"

# Instala dependências
Write-Host "[3/4] Instalando dependências (openai + rich)..." -ForegroundColor Yellow
& $PipCmd install -r (Join-Path $AgentDir "requirements.txt") -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✅ Dependências instaladas!" -ForegroundColor Green
} else {
    Write-Host "      ❌ Falha ao instalar dependências." -ForegroundColor Red
    exit 1
}

# Cria diretórios de dados
Write-Host "[4/4] Criando diretórios de dados..." -ForegroundColor Yellow
$dirs = @(
    (Join-Path $AgentDir "data"),
    (Join-Path $AgentDir "data\sessions"),
    (Join-Path $AgentDir "data\logs")
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}
Write-Host "      ✅ Diretórios criados!" -ForegroundColor Green

Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ GEMMA-AGENT pronto para uso!" -ForegroundColor Green
Write-Host ""
Write-Host "  ANTES DE INICIAR:" -ForegroundColor Yellow
Write-Host "  1. Abra o LM Studio" -ForegroundColor White
Write-Host "  2. Carregue o modelo Gemma" -ForegroundColor White
Write-Host "  3. Vá em Local Server → Start Server" -ForegroundColor White
Write-Host ""
Write-Host "  PARA INICIAR O AGENTE:" -ForegroundColor Yellow
Write-Host "  & '$PythonVenv' '$AgentDir\agent.py'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ATALHO (próximas vezes):" -ForegroundColor Yellow
Write-Host "  .\start.ps1" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Cria script de início rápido
$startScript = @"
# GEMMA-AGENT — Início Rápido
`$PythonVenv = Join-Path `$PSScriptRoot ".venv\Scripts\python.exe"
`$Agent = Join-Path `$PSScriptRoot "agent.py"

if (`$args.Count -gt 0) {
    & `$PythonVenv `$Agent `$args
} else {
    & `$PythonVenv `$Agent
}
"@
Set-Content -Path (Join-Path $AgentDir "start.ps1") -Value $startScript -Encoding UTF8
Write-Host "  Script 'start.ps1' criado para inicializações futuras." -ForegroundColor DarkCyan

# Pergunta se quer iniciar agora
$resp = Read-Host "Deseja iniciar o agente agora? (S/N)"
if ($resp -match "^[Ss]") {
    Write-Host ""
    & $PythonVenv (Join-Path $AgentDir "agent.py")
}
