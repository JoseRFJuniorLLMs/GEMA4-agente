"""
Integração com HeraclitusDB
Gravação imutável de logs, eventos e decisões do agente.
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from config import HERACLITUS_DB_PATH


def _get_lsn(collection_path: Path) -> int:
    """Retorna o próximo Log Sequence Number (LSN) para a coleção."""
    files = list(collection_path.glob("*.jsonl")) + list(collection_path.glob("*.json"))
    if not files:
        return 1
    # Conta linhas totais de todos os arquivos como LSN
    total = 0
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                total += sum(1 for _ in fh)
        except Exception:
            pass
    return total + 1


def heraclitus_append(collection: str, data: str, metadata: dict = None) -> str:
    """
    Grava um registro imutável no HeraclitusDB.
    
    O HeraclitusDB é um log append-only: eventos gravados nunca são
    alterados ou deletados, apenas acumulados cronologicamente.
    
    Args:
        collection: Nome da coleção (ex: "agent_logs", "decisoes", "erros")
        data: Conteúdo a gravar (string ou JSON serializado)
        metadata: Metadados adicionais (ex: {"projeto": "EVA", "tipo": "decisao"})
    """
    try:
        db_path = Path(HERACLITUS_DB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)

        # Garante nome de coleção seguro
        safe_collection = "".join(c if c.isalnum() or c in "._-" else "_" for c in collection)
        col_path = db_path / safe_collection
        col_path.mkdir(exist_ok=True)

        # Arquivo de log rotacionado por mês
        now = datetime.now(timezone.utc)
        log_file = col_path / f"{now.strftime('%Y-%m')}.jsonl"

        lsn = _get_lsn(col_path)

        # Monta o registro
        record = {
            "lsn": lsn,
            "timestamp": now.isoformat(),
            "collection": safe_collection,
            "data": data,
            "hash": hashlib.sha256(data.encode()).hexdigest()[:16],
        }
        if metadata:
            record["metadata"] = metadata

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return (f"✅ HeraclitusDB: Evento imutável gravado.\n"
                f"   Coleção: {safe_collection} | LSN: {lsn} | "
                f"Hash: {record['hash']} | Arquivo: {log_file.name}")

    except Exception as e:
        return f"ERRO ao gravar no HeraclitusDB: {e}"


def heraclitus_read(collection: str, limit: int = 20) -> str:
    """
    Lê os últimos N registros de uma coleção do HeraclitusDB.
    """
    try:
        col_path = Path(HERACLITUS_DB_PATH) / collection
        if not col_path.exists():
            available = [d.name for d in Path(HERACLITUS_DB_PATH).iterdir() if d.is_dir()]
            return (f"ERRO: Coleção '{collection}' não encontrada.\n"
                    f"Coleções disponíveis: {available}")

        log_files = sorted(col_path.glob("*.jsonl"), reverse=True)
        if not log_files:
            return f"Coleção '{collection}' está vazia."

        records = []
        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in reversed(lines):
                try:
                    records.append(json.loads(line.strip()))
                    if len(records) >= limit:
                        break
                except Exception:
                    continue
            if len(records) >= limit:
                break

        output = f"📜 HeraclitusDB | Coleção: '{collection}' | Últimos {len(records)} registros:\n\n"
        for r in records:
            ts = r.get("timestamp", "?")[:19]
            lsn = r.get("lsn", "?")
            data = r.get("data", "")[:200]
            output += f"[LSN:{lsn} | {ts}] {data}\n"
            if r.get("metadata"):
                output += f"  Metadata: {r['metadata']}\n"
            output += "\n"
        return output

    except Exception as e:
        return f"ERRO ao ler HeraclitusDB: {e}"


def heraclitus_list_collections() -> str:
    """Lista todas as coleções existentes no HeraclitusDB."""
    try:
        db_path = Path(HERACLITUS_DB_PATH)
        if not db_path.exists():
            return "HeraclitusDB não encontrado no caminho configurado."

        collections = [d for d in db_path.iterdir() if d.is_dir()]
        if not collections:
            return "HeraclitusDB está vazio. Nenhuma coleção criada ainda."

        output = f"🗄️ HeraclitusDB | {len(collections)} coleção(ões):\n"
        for col in sorted(collections):
            files = list(col.glob("*.jsonl"))
            total_records = 0
            for f in files:
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        total_records += sum(1 for _ in fh)
                except Exception:
                    pass
            output += f"  • {col.name}: {total_records} registros em {len(files)} arquivo(s)\n"
        return output

    except Exception as e:
        return f"ERRO ao listar coleções: {e}"
