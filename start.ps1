# GEMMA-AGENT — Início Rápido
# Use este script após rodar run.ps1 uma vez.

$PythonExe = "C:\Users\web2a\AppData\Local\Python\bin\python.exe"
$Agent     = Join-Path $PSScriptRoot "agent.py"

if (-not (Test-Path $PythonExe)) {
    # fallback para python no PATH
    $PythonExe = "python"
}

if ($args.Count -gt 0) {
    & $PythonExe $Agent @args
} else {
    & $PythonExe $Agent
}
