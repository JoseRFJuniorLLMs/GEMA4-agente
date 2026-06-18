"""
Pipeline & Batch — Execução de múltiplas tarefas em sequência.
Permite definir um plano de tarefas e executá-las automaticamente.
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_pipeline(tasks: list, output_dir: str = None):
    """
    Executa uma lista de tarefas sequencialmente.
    Cada tarefa é uma string descrevendo o que o agente deve fazer.
    
    Exemplo:
        run_pipeline([
            "Analise o projeto EVA-Back e liste os endpoints",
            "Crie testes unitários para os endpoints listados",
            "Execute os testes e reporte os resultados",
        ])
    """
    from core.loop import AgentLoop

    output_dir = output_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "pipelines"
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Registra a pipeline
    pipeline_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = {
        "pipeline_id": pipeline_id,
        "started_at": datetime.now().isoformat(),
        "total_tasks": len(tasks),
        "results": [],
    }

    print(f"\n{'='*60}")
    print(f"  PIPELINE: {pipeline_id}")
    print(f"  Tarefas: {len(tasks)}")
    print(f"{'='*60}\n")

    def ui_callback(kind, text):
        prefix = {"tool_call": "  [TOOL]", "tool_result": "  [RES]",
                   "response": "  [AGENT]", "done": "  [DONE]",
                   "iteration": "  [ITER]", "warn": "  [WARN]"
                   }.get(kind, f"  [{kind.upper()}]")
        preview = text[:150].replace("\n", " ")
        print(f"{prefix} {preview}")

    agent = AgentLoop(ui=ui_callback)

    for i, task in enumerate(tasks, 1):
        print(f"\n{'─'*60}")
        print(f"  Tarefa {i}/{len(tasks)}: {task[:80]}{'...' if len(task) > 80 else ''}")
        print(f"{'─'*60}")

        start = time.time()
        try:
            result = agent.new_task(task)
            elapsed = time.time() - start
            log["results"].append({
                "task_index": i,
                "task": task,
                "result": result[:2000] if result else "",
                "status": "success",
                "elapsed_seconds": round(elapsed, 1),
                "iterations": agent.iteration,
            })
            print(f"\n  [OK] Tarefa {i} concluida em {elapsed:.1f}s ({agent.iteration} iteracoes)")
        except Exception as e:
            elapsed = time.time() - start
            log["results"].append({
                "task_index": i,
                "task": task,
                "result": str(e),
                "status": "error",
                "elapsed_seconds": round(elapsed, 1),
            })
            print(f"\n  [ERRO] Tarefa {i} falhou: {e}")

    # Salva relatório
    log["finished_at"] = datetime.now().isoformat()
    total_elapsed = sum(r["elapsed_seconds"] for r in log["results"])
    log["total_elapsed_seconds"] = round(total_elapsed, 1)
    log["success_count"] = sum(1 for r in log["results"] if r["status"] == "success")
    log["error_count"] = sum(1 for r in log["results"] if r["status"] == "error")

    report_path = os.path.join(output_dir, f"pipeline_{pipeline_id}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  PIPELINE CONCLUIDA")
    print(f"  Sucesso: {log['success_count']}/{len(tasks)}")
    print(f"  Erros:   {log['error_count']}/{len(tasks)}")
    print(f"  Tempo:   {total_elapsed:.1f}s")
    print(f"  Report:  {report_path}")
    print(f"{'='*60}\n")

    return log


# ─── CLI para pipeline via arquivo ────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Executa uma pipeline de tarefas do GEMMA-AGENT")
    parser.add_argument("file", help="Arquivo .json ou .txt com lista de tarefas")
    args = parser.parse_args()

    filepath = args.file
    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        if isinstance(tasks, dict):
            tasks = tasks.get("tasks", [])
    elif filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            tasks = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        print(f"Formato não suportado: {filepath}")
        print("Use .json ou .txt")
        sys.exit(1)

    if not tasks:
        print("Nenhuma tarefa encontrada no arquivo.")
        sys.exit(1)

    run_pipeline(tasks)
