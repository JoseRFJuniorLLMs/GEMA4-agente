"""
Loop Central do Agente (ReAct)
Gerencia o ciclo Razão → Ação → Observação → Razão...
"""

import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import (
    LM_STUDIO_BASE_URL, LM_STUDIO_API_KEY, MODEL_NAME,
    MAX_ITERATIONS, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT,
    CONTEXT_WINDOW
)
from core.registry import TOOL_FUNCTIONS, TOOLS_SPEC
from core.context import trim_context, get_context_stats


class AgentLoop:
    def __init__(self, ui=None):
        self.client = OpenAI(
            base_url=LM_STUDIO_BASE_URL,
            api_key=LM_STUDIO_API_KEY
        )
        self.messages = []
        self.iteration = 0
        self.ui = ui  # UI callback (opcional)
        self._reset_messages()

    def _reset_messages(self):
        """Inicializa o histórico com o system prompt."""
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.iteration = 0

    def _log(self, kind: str, text: str):
        """Emite evento de log para a UI ou para stdout."""
        if self.ui:
            self.ui(kind, text)

    def _call_model(self) -> object:
        """Chama o LM Studio e retorna a resposta do modelo."""
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=self.messages,
                tools=TOOLS_SPEC,
                tool_choice="auto",
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar ao LM Studio: {e}\n"
                               "Verifique se o LM Studio está rodando em http://localhost:1234")

    def _execute_tool(self, tool_call) -> str:
        """Executa uma chamada de ferramenta e retorna o resultado."""
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            return f"ERRO: Argumentos inválidos (JSON malformado): {tool_call.function.arguments}"

        self._log("tool_call", f"{name}({json.dumps(args, ensure_ascii=False)[:200]})")

        if name not in TOOL_FUNCTIONS:
            return f"ERRO: Ferramenta '{name}' não encontrada. Ferramentas disponíveis: {list(TOOL_FUNCTIONS.keys())}"

        try:
            result = TOOL_FUNCTIONS[name](**args)
            return str(result)
        except TypeError as e:
            return f"ERRO nos argumentos de '{name}': {e}"
        except Exception as e:
            return f"ERRO ao executar '{name}': {e}"

    def run(self, user_message: str) -> str:
        """
        Executa o loop ReAct para uma mensagem do usuário.
        Retorna a resposta final do agente.
        """
        self.messages.append({"role": "user", "content": user_message})
        self._log("user", user_message)

        final_response = ""

        while self.iteration < MAX_ITERATIONS:
            self.iteration += 1
            self._log("iteration", f"Iteração {self.iteration}/{MAX_ITERATIONS}")

            # ── Trim contexto se necessário ──────────────────────────────
            self.messages = trim_context(
                self.messages,
                max_tokens=int(CONTEXT_WINDOW * 0.85),  # margem de 15%
                keep_last_n=10
            )

            # ── Pensa ────────────────────────────────────────────────────────
            response = self._call_model()
            msg = response.choices[0].message

            # Adiciona a resposta do modelo ao histórico
            self.messages.append(msg)

            # ── Sem tool calls → resposta final ──────────────────────────────
            if not msg.tool_calls:
                content = msg.content or ""
                self._log("response", content)
                final_response = content

                # Verifica se o agente declarou conclusão
                if "TAREFA_CONCLUIDA" in content:
                    self._log("done", "✅ Agente declarou tarefa concluída.")
                    break

                # Sem tool calls e sem conclusão → pode estar esperando input
                # Continua para não travar em loop vazio
                if not content.strip():
                    self._log("warn", "Resposta vazia do modelo. Encerrando.")
                    break

                # Se for apenas texto intermediário, continua
                continue

            # ── Executa tools ────────────────────────────────────────────────
            tool_results = []
            for tool_call in msg.tool_calls:
                result = self._execute_tool(tool_call)
                self._log("tool_result", f"[{tool_call.function.name}] → {result[:300]}{'...' if len(result) > 300 else ''}")

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": result,
                })

            # Adiciona resultados das ferramentas ao histórico
            self.messages.extend(tool_results)

        else:
            # Limite de iterações atingido
            self._log("warn", f"⚠️ Limite de {MAX_ITERATIONS} iterações atingido.")
            if not final_response:
                final_response = (f"O agente atingiu o limite de {MAX_ITERATIONS} iterações. "
                                  "A tarefa pode estar incompleta.")

        return final_response

    def chat(self, user_message: str) -> str:
        """
        Modo chat: mantém histórico entre mensagens (não reseta).
        Ideal para conversas contínuas sobre um projeto.
        """
        return self.run(user_message)

    def new_task(self, user_message: str) -> str:
        """
        Nova tarefa: reseta o histórico e começa do zero.
        Ideal para tarefas independentes.
        """
        self._reset_messages()
        return self.run(user_message)

    def get_stats(self) -> dict:
        """Retorna estatísticas da sessão atual."""
        return {
            "iteracoes": self.iteration,
            "mensagens_no_historico": len(self.messages),
            "ferramentas_disponiveis": len(TOOL_FUNCTIONS),
        }
