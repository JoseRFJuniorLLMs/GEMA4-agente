"""
GEMMA-AGENT — Interface de Terminal Rica
Agente de desenvolvimento autônomo local rodando via LM Studio.

Uso:
    python agent.py                    # modo interativo
    python agent.py "sua tarefa aqui" # executa uma tarefa e sai
    python agent.py --new "tarefa"    # força novo histórico
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Adiciona o diretório do projeto ao path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ─── Verifica dependências ─────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ─── Setup ────────────────────────────────────────────────────────────────────
if RICH_AVAILABLE:
    console = Console()
else:
    class _FallbackConsole:
        def print(self, *args, **kwargs): print(*args)
        def rule(self, *args, **kwargs): print("─" * 60)
    console = _FallbackConsole()


# ─── Banner ───────────────────────────────────────────────────────────────────
BANNER = """
[bold cyan]
  ██████  ███████ ███    ███ ███    ███  █████       █████   ██████  ███████ ███    ██ ████████
 ██       ██      ████  ████ ████  ████ ██   ██     ██   ██ ██       ██      ████   ██    ██
 ██   ███ █████   ██ ████ ██ ██ ████ ██ ███████     ███████ ██   ███ █████   ██ ██  ██    ██
 ██    ██ ██      ██  ██  ██ ██  ██  ██ ██   ██     ██   ██ ██    ██ ██      ██  ██ ██    ██
  ██████  ███████ ██      ██ ██      ██ ██   ██     ██   ██  ██████  ███████ ██   ████    ██
[/bold cyan]
[dim]Agente de Desenvolvimento Autônomo Local · Powered by LM Studio + Gemma[/dim]
"""

MINI_BANNER = "[bold cyan]◆ GEMMA-AGENT[/bold cyan] [dim]· Agente Autônomo Local[/dim]"


# ─── Cores por tipo de evento ─────────────────────────────────────────────────
EVENT_STYLES = {
    "user":        ("bold white", "💬"),
    "iteration":   ("dim cyan", "🔄"),
    "tool_call":   ("bold yellow", "⚙️"),
    "tool_result": ("dim green", "📤"),
    "response":    ("bold green", "🤖"),
    "done":        ("bold bright_green", "✅"),
    "warn":        ("bold yellow", "⚠️"),
    "error":       ("bold red", "❌"),
    "info":        ("dim white", "ℹ️"),
    "system":      ("bold blue", "🔧"),
}


def format_event(kind: str, text: str) -> None:
    """Formata e imprime um evento do agente no terminal."""
    if not RICH_AVAILABLE:
        icon = EVENT_STYLES.get(kind, ("", ""))[1]
        print(f"{icon} [{kind.upper()}] {text}")
        return

    style, icon = EVENT_STYLES.get(kind, ("white", "•"))
    ts = datetime.now().strftime("%H:%M:%S")

    if kind == "response":
        console.print()
        console.print(Panel(
            Markdown(text) if text.strip() else Text("(resposta vazia)", style="dim"),
            title=f"[bold green]{icon} GEMMA-AGENT[/bold green]",
            subtitle=f"[dim]{ts}[/dim]",
            border_style="green",
            padding=(1, 2),
        ))
    elif kind == "done":
        console.print(Rule(f"[bold bright_green]{icon} {text}[/bold bright_green]",
                           style="bright_green"))
    elif kind == "tool_call":
        console.print(f"  [dim]{ts}[/dim] [{style}]{icon} TOOL[/{style}] "
                      f"[yellow]{text}[/yellow]")
    elif kind == "tool_result":
        # Mostra apenas um preview do resultado
        preview = text[:120].replace("\n", " ") + ("..." if len(text) > 120 else "")
        console.print(f"  [dim]{ts}[/dim] [{style}]{icon}[/{style}] "
                      f"[dim]{preview}[/dim]")
    elif kind == "iteration":
        console.print(f"  [dim]{ts} {icon} {text}[/dim]")
    elif kind == "warn":
        console.print(f"  [{style}]{icon} {text}[/{style}]")
    elif kind == "error":
        console.print(Panel(text, title=f"[red]{icon} ERRO[/red]", border_style="red"))
    else:
        console.print(f"  [dim]{ts}[/dim] [{style}]{icon}[/{style}] {text}")


def show_banner():
    """Exibe o banner de boas-vindas."""
    if RICH_AVAILABLE:
        console.print(BANNER)
        # Info do sistema
        from config import LM_STUDIO_BASE_URL, MODEL_NAME, MAX_ITERATIONS, DEFAULT_WORKDIR
        table = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 1))
        table.add_column("Chave", style="dim cyan")
        table.add_column("Valor", style="white")
        table.add_row("🌐 LM Studio",    LM_STUDIO_BASE_URL)
        table.add_row("🧠 Modelo",       MODEL_NAME)
        table.add_row("🔁 Max Iterações", str(MAX_ITERATIONS))
        table.add_row("📁 Workdir",       DEFAULT_WORKDIR)
        table.add_row("🛠️  Ferramentas",  "28 ferramentas disponíveis")
        console.print(table)
        console.print()
    else:
        print("=" * 60)
        print("GEMMA-AGENT — Agente de Desenvolvimento Autônomo Local")
        print("=" * 60)


def show_help():
    """Mostra os comandos disponíveis."""
    help_text = """
**Comandos Especiais** (comece com /):

| Comando | Descrição |
|---------|-----------|
| `/help` | Mostra esta ajuda |
| `/new` | Inicia nova tarefa (reseta histórico) |
| `/stats` | Mostra estatísticas da sessão |
| `/memory` | Lista memória persistente |
| `/sessions` | Lista sessões salvas |
| `/clear` | Limpa o terminal |
| `/tools` | Lista todas as ferramentas |
| `/quit` ou `/exit` | Encerra o agente |

**Dicas:**
- Seja específico nas tarefas para melhores resultados
- O agente tem acesso a `D:\\DEV\\` e todos os projetos
- Resultados importantes são salvos automaticamente no HeraclitusDB
- Use `/new` para tarefas independentes que não precisam do contexto anterior
"""
    if RICH_AVAILABLE:
        console.print(Panel(Markdown(help_text), title="[cyan]Ajuda[/cyan]",
                            border_style="cyan", padding=(1, 2)))
    else:
        print(help_text)


def show_tools():
    """Lista todas as ferramentas disponíveis."""
    from core.registry import TOOLS_SPEC
    if RICH_AVAILABLE:
        table = Table(title="🛠️  Ferramentas Disponíveis", box=box.ROUNDED,
                      border_style="cyan", show_lines=True)
        table.add_column("Ferramenta", style="bold yellow", no_wrap=True)
        table.add_column("Descrição", style="white")
        for tool in TOOLS_SPEC:
            fn = tool["function"]
            name = fn["name"]
            desc = fn["description"][:80] + ("..." if len(fn["description"]) > 80 else "")
            table.add_row(name, desc)
        console.print(table)
    else:
        from core.registry import TOOLS_SPEC
        for t in TOOLS_SPEC:
            print(f"- {t['function']['name']}: {t['function']['description'][:60]}")


def check_dependencies() -> bool:
    """Verifica se todas as dependências estão instaladas."""
    missing = []
    if not RICH_AVAILABLE:
        missing.append("rich")
    if not OPENAI_AVAILABLE:
        missing.append("openai")

    if missing:
        print(f"❌ Dependências ausentes: {', '.join(missing)}")
        print(f"   Instale com: pip install {' '.join(missing)}")
        return False
    return True


def check_lm_studio() -> bool:
    """Verifica se o LM Studio está acessível."""
    import urllib.request
    from config import LM_STUDIO_BASE_URL
    try:
        url = LM_STUDIO_BASE_URL.rstrip("/v1") + "/v1/models"
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def run_interactive():
    """Modo interativo: REPL completo com histórico persistente."""
    if not check_dependencies():
        sys.exit(1)

    show_banner()

    # Verifica LM Studio
    if RICH_AVAILABLE:
        with console.status("[cyan]Verificando conexão com LM Studio...[/cyan]"):
            lm_ok = check_lm_studio()
    else:
        print("Verificando LM Studio...")
        lm_ok = check_lm_studio()

    if lm_ok:
        console.print("[green]✅ LM Studio conectado e pronto![/green]\n")
    else:
        console.print("[yellow]⚠️  LM Studio não detectado em localhost:1234[/yellow]")
        console.print("[dim]   Certifique-se de que o LM Studio está rodando com um modelo carregado.[/dim]")
        console.print("[dim]   O agente continuará mas falhará ao tentar chamar o modelo.\n[/dim]")

    # Importa o loop
    from core.loop import AgentLoop
    agent = AgentLoop(ui=format_event)

    console.print("[dim]Digite sua tarefa abaixo. Use /help para ver os comandos disponíveis.[/dim]")
    console.print()

    # REPL
    while True:
        try:
            if RICH_AVAILABLE:
                user_input = Prompt.ask("[bold cyan]você[/bold cyan]").strip()
            else:
                user_input = input("você> ").strip()

            if not user_input:
                continue

            # ── Comandos especiais ────────────────────────────────────────
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]

                if cmd in ("/quit", "/exit", "/sair"):
                    console.print("[dim]Até logo! 👋[/dim]")
                    break

                elif cmd == "/help":
                    show_help()

                elif cmd == "/new":
                    agent._reset_messages()
                    console.print("[green]✅ Novo histórico iniciado.[/green]")
                    # Aceita tarefa inline: /new faça X
                    rest = user_input[4:].strip()
                    if rest:
                        agent.run(rest)

                elif cmd == "/stats":
                    stats = agent.get_stats()
                    if RICH_AVAILABLE:
                        table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
                        table.add_column("Métrica", style="dim cyan")
                        table.add_column("Valor", style="white")
                        for k, v in stats.items():
                            table.add_row(k, str(v))
                        console.print(table)
                    else:
                        print(stats)

                elif cmd == "/memory":
                    from tools.memory import memory_list
                    console.print(memory_list())

                elif cmd == "/sessions":
                    from tools.memory import list_sessions
                    console.print(list_sessions())

                elif cmd == "/tools":
                    show_tools()

                elif cmd == "/clear":
                    console.clear()
                    console.print(MINI_BANNER)

                else:
                    console.print(f"[yellow]Comando desconhecido: {cmd}. Use /help.[/yellow]")

                continue

            # ── Executa a tarefa no agente ────────────────────────────────
            console.print()
            start = time.time()

            if RICH_AVAILABLE:
                # Mostra spinner enquanto pensa
                with Live(Spinner("dots", text=" Pensando..."), refresh_per_second=10,
                          transient=True):
                    time.sleep(0.1)  # pequeno delay para o spinner aparecer

            agent.chat(user_input)

            elapsed = time.time() - start
            console.print(f"\n[dim]⏱️  Concluído em {elapsed:.1f}s · "
                          f"Iterações: {agent.iteration}[/dim]\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrompido. Digite /quit para sair.[/yellow]")
        except EOFError:
            console.print("\n[dim]Sessão encerrada.[/dim]")
            break
        except Exception as e:
            console.print(f"\n[red]❌ Erro inesperado: {e}[/red]")


def run_task(task: str, new_session: bool = False):
    """Executa uma única tarefa e sai (modo não-interativo)."""
    if not check_dependencies():
        sys.exit(1)

    if RICH_AVAILABLE:
        console.print(MINI_BANNER)
        console.print(f"[dim]Tarefa:[/dim] {task}\n")

    from core.loop import AgentLoop
    agent = AgentLoop(ui=format_event)

    if new_session:
        result = agent.new_task(task)
    else:
        result = agent.run(task)

    if result:
        console.print(f"\n[dim]Resultado final:[/dim]\n{result}")

    stats = agent.get_stats()
    console.print(f"\n[dim]Iterações: {stats['iteracoes']} | "
                  f"Mensagens no histórico: {stats['mensagens_no_historico']}[/dim]")


# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GEMMA-AGENT — Agente de Desenvolvimento Autônomo Local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python agent.py
  python agent.py "Liste todos os projetos em D:\\DEV e me dê um resumo"
  python agent.py --new "Crie um README.md para o projeto EVA"
        """
    )
    parser.add_argument("task", nargs="?", help="Tarefa a executar (modo não-interativo)")
    parser.add_argument("--new", "-n", action="store_true",
                        help="Inicia nova sessão (reseta histórico)")
    parser.add_argument("--version", "-v", action="version", version="GEMMA-AGENT 1.0.0")

    args = parser.parse_args()

    if args.task:
        run_task(args.task, new_session=args.new)
    else:
        run_interactive()
