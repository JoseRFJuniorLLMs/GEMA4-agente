"""
Ferramenta de Execução de Shell
Roda comandos PowerShell/CMD com timeout e captura completa de output.
"""

import subprocess
import os
import sys
from pathlib import Path
from config import COMMAND_TIMEOUT, DEFAULT_WORKDIR, SHELL


def run_command(command: str, cwd: str = None, timeout: int = None) -> str:
    """
    Executa um comando no shell e retorna stdout + stderr.
    
    Args:
        command: Comando a executar (PowerShell ou CMD)
        cwd: Diretório de trabalho (padrão: DEFAULT_WORKDIR)
        timeout: Timeout em segundos (padrão: config COMMAND_TIMEOUT)
    """
    cwd = os.path.expandvars(cwd or DEFAULT_WORKDIR)
    timeout = timeout or COMMAND_TIMEOUT

    if not Path(cwd).exists():
        return f"ERRO: Diretório de trabalho não encontrado: {cwd}"

    try:
        if sys.platform == "win32":
            if SHELL == "powershell":
                full_cmd = ["powershell", "-NoProfile", "-NonInteractive",
                            "-ExecutionPolicy", "Bypass", "-Command", command]
            else:
                full_cmd = ["cmd", "/c", command]
        else:
            full_cmd = ["bash", "-c", command]

        result = subprocess.run(
            full_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )

        output_parts = []
        if result.stdout.strip():
            output_parts.append(f"[STDOUT]\n{result.stdout.strip()}")
        if result.stderr.strip():
            output_parts.append(f"[STDERR]\n{result.stderr.strip()}")

        status = "✅ Sucesso" if result.returncode == 0 else f"⚠️ Exit code: {result.returncode}"
        output = "\n".join(output_parts) if output_parts else "(sem output)"

        return f"{status} | CWD: {cwd}\n{output}"

    except subprocess.TimeoutExpired:
        return f"⏰ TIMEOUT: Comando excedeu {timeout}s e foi cancelado.\nComando: {command}"
    except FileNotFoundError as e:
        return f"ERRO: Shell não encontrado ({SHELL}). Detalhes: {e}"
    except Exception as e:
        return f"ERRO ao executar comando: {e}"


def run_python(code: str, cwd: str = None) -> str:
    """
    Executa um trecho de código Python usando o interpretador atual.
    Útil para cálculos, testes rápidos e scripts inline.
    """
    cwd = os.path.expandvars(cwd or DEFAULT_WORKDIR)
    
    # Salva em arquivo temporário
    tmp_path = Path(cwd) / "_agent_tmp_exec.py"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            [sys.executable, str(tmp_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT
        )

        output_parts = []
        if result.stdout.strip():
            output_parts.append(f"[OUTPUT]\n{result.stdout.strip()}")
        if result.stderr.strip():
            output_parts.append(f"[ERRO]\n{result.stderr.strip()}")

        status = "✅ Executado" if result.returncode == 0 else f"❌ Falhou (exit {result.returncode})"
        output = "\n".join(output_parts) if output_parts else "(sem output)"
        return f"{status}\n{output}"

    except subprocess.TimeoutExpired:
        return f"⏰ TIMEOUT: Código Python excedeu {COMMAND_TIMEOUT}s"
    except Exception as e:
        return f"ERRO ao executar Python: {e}"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def git_command(args: str, cwd: str = None) -> str:
    """
    Executa um comando git no diretório especificado.
    
    Exemplos:
        git_command("status")
        git_command("add .")
        git_command("commit -m 'mensagem'")
        git_command("log --oneline -10")
    """
    cwd = os.path.expandvars(cwd or DEFAULT_WORKDIR)
    return run_command(f"git {args}", cwd=cwd)


def install_package(package: str, cwd: str = None) -> str:
    """Instala um pacote Python via pip."""
    cwd = os.path.expandvars(cwd or DEFAULT_WORKDIR)
    return run_command(f"pip install {package}", cwd=cwd, timeout=120)


def get_system_info() -> str:
    """Retorna informações do sistema operacional e ambiente."""
    return run_command(
        "$PSVersionTable | ConvertTo-Json; "
        "python --version; "
        "git --version; "
        "node --version 2>$null; "
        "Get-Location"
    )
