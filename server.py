"""
Server Mode — Expõe o GEMMA-AGENT como uma API HTTP local.
Permite integrar com VSCode, outras ferramentas ou UIs customizadas.

Uso:
    python server.py
    python server.py --port 8080

API:
    POST /chat      {"message": "..."}        → Resposta do agente
    POST /task      {"task": "..."}           → Nova tarefa (reseta contexto)
    POST /pipeline  {"tasks": ["...", "..."]} → Executa pipeline
    GET  /health                              → Status do servidor
    GET  /stats                               → Estatísticas da sessão
    GET  /tools                               → Lista ferramentas
    GET  /memory                              → Lista memória persistente
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.loop import AgentLoop
from core.registry import TOOLS_SPEC, TOOL_FUNCTIONS
from tools.memory import memory_list


class AgentHandler(BaseHTTPRequestHandler):
    """Handler HTTP para o GEMMA-AGENT."""

    agent = None  # Compartilhado entre requests
    agent_lock = threading.Lock()

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, data, status=200):
        self._set_headers(status)
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body}

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self._json_response({
                "status": "ok",
                "agent": "GEMMA-AGENT",
                "version": "1.0.0",
                "tools_count": len(TOOL_FUNCTIONS),
            })

        elif path == "/stats":
            if self.agent:
                self._json_response(self.agent.get_stats())
            else:
                self._json_response({"error": "Agente nao iniciado"}, 503)

        elif path == "/tools":
            tools_list = [
                {"name": t["function"]["name"],
                 "description": t["function"]["description"]}
                for t in TOOLS_SPEC
            ]
            self._json_response({"tools": tools_list, "count": len(tools_list)})

        elif path == "/memory":
            result = memory_list()
            self._json_response({"memory": result})

        else:
            self._json_response({"error": f"Endpoint nao encontrado: {path}"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/chat":
            message = body.get("message", "")
            if not message:
                self._json_response({"error": "Campo 'message' obrigatorio"}, 400)
                return

            with self.agent_lock:
                try:
                    logs = []
                    def capture_ui(kind, text):
                        logs.append({"type": kind, "text": text[:500]})

                    self.agent.ui = capture_ui
                    result = self.agent.chat(message)
                    self._json_response({
                        "response": result,
                        "stats": self.agent.get_stats(),
                        "logs": logs[-20:],  # Últimos 20 eventos
                    })
                except Exception as e:
                    self._json_response({"error": str(e)}, 500)

        elif path == "/task":
            task = body.get("task", "")
            if not task:
                self._json_response({"error": "Campo 'task' obrigatorio"}, 400)
                return

            with self.agent_lock:
                try:
                    logs = []
                    def capture_ui(kind, text):
                        logs.append({"type": kind, "text": text[:500]})

                    self.agent.ui = capture_ui
                    result = self.agent.new_task(task)
                    self._json_response({
                        "response": result,
                        "stats": self.agent.get_stats(),
                        "logs": logs[-20:],
                    })
                except Exception as e:
                    self._json_response({"error": str(e)}, 500)

        elif path == "/pipeline":
            tasks = body.get("tasks", [])
            if not tasks:
                self._json_response({"error": "Campo 'tasks' (lista) obrigatorio"}, 400)
                return

            with self.agent_lock:
                try:
                    from core.pipeline import run_pipeline
                    result = run_pipeline(tasks)
                    self._json_response(result)
                except Exception as e:
                    self._json_response({"error": str(e)}, 500)

        else:
            self._json_response({"error": f"Endpoint nao encontrado: {path}"}, 404)

    def log_message(self, format, *args):
        """Override para log mais limpo."""
        timestamp = self.log_date_time_string()
        method = args[0] if args else "?"
        status = args[1] if len(args) > 1 else "?"
        print(f"  [{timestamp}] {method} -> {status}")


def start_server(host: str = "0.0.0.0", port: int = 5000):
    """Inicia o servidor HTTP do GEMMA-AGENT."""

    # Inicializa o agente
    print("="*55)
    print("  GEMMA-AGENT Server Mode")
    print("="*55)
    print(f"  Inicializando agente...")

    agent = AgentLoop()
    AgentHandler.agent = agent

    server = HTTPServer((host, port), AgentHandler)

    print(f"  Agente pronto!")
    print(f"  Servidor: http://{host}:{port}")
    print()
    print(f"  Endpoints:")
    print(f"    POST /chat      -> Conversa continua")
    print(f"    POST /task      -> Nova tarefa")
    print(f"    POST /pipeline  -> Pipeline de tarefas")
    print(f"    GET  /health    -> Health check")
    print(f"    GET  /stats     -> Estatisticas")
    print(f"    GET  /tools     -> Lista ferramentas")
    print(f"    GET  /memory    -> Memoria persistente")
    print()
    print(f"  Exemplo:")
    print(f"    curl -X POST http://localhost:{port}/chat \\")
    print(f"      -H 'Content-Type: application/json' \\")
    print(f"      -d '{{\"message\": \"Liste os projetos em D:\\\\DEV\"}}'")
    print()
    print(f"  Ctrl+C para parar")
    print("="*55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GEMMA-AGENT HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host (padrao: 0.0.0.0)")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Porta (padrao: 5000)")
    args = parser.parse_args()
    start_server(args.host, args.port)
