"""
Memória Persistente do Agente
Salva e recupera informações entre sessões usando JSON.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from config import MEMORY_FILE, SESSIONS_DIR


def _load_memory() -> dict:
    """Carrega o arquivo de memória do disco."""
    path = Path(MEMORY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_memory(data: dict) -> None:
    """Salva o arquivo de memória no disco."""
    path = Path(MEMORY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def memory_save(key: str, value: str) -> str:
    """
    Salva um par chave-valor na memória persistente.
    A memória persiste entre sessões do agente.
    
    Use para guardar: credenciais de projeto, contextos importantes,
    resultados de pesquisas, decisões arquiteturais, etc.
    """
    try:
        mem = _load_memory()
        mem[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        _save_memory(mem)
        return f"✅ Memória salva: '{key}' = '{value[:100]}{'...' if len(value) > 100 else ''}'"
    except Exception as e:
        return f"ERRO ao salvar memória: {e}"


def memory_read(key: str) -> str:
    """
    Lê um valor da memória persistente pelo nome da chave.
    Retorna erro se a chave não existir.
    """
    try:
        mem = _load_memory()
        if key not in mem:
            keys = list(mem.keys())
            hint = f"\nChaves disponíveis: {keys}" if keys else "\n(memória vazia)"
            return f"ERRO: Chave '{key}' não encontrada na memória.{hint}"
        entry = mem[key]
        val = entry["value"] if isinstance(entry, dict) else entry
        updated = entry.get("updated_at", "desconhecido") if isinstance(entry, dict) else "N/A"
        return f"🧠 '{key}' (atualizado em {updated}):\n{val}"
    except Exception as e:
        return f"ERRO ao ler memória: {e}"


def memory_list() -> str:
    """Lista todas as chaves armazenadas na memória persistente."""
    try:
        mem = _load_memory()
        if not mem:
            return "🧠 Memória vazia. Nenhuma chave armazenada ainda."
        output = f"🧠 Memória persistente ({len(mem)} entradas):\n"
        for key, entry in mem.items():
            val = entry["value"] if isinstance(entry, dict) else str(entry)
            updated = entry.get("updated_at", "N/A") if isinstance(entry, dict) else "N/A"
            preview = val[:60] + "..." if len(val) > 60 else val
            output += f"  • {key}: {preview} [atualizado: {updated}]\n"
        return output
    except Exception as e:
        return f"ERRO ao listar memória: {e}"


def memory_delete(key: str) -> str:
    """Remove uma chave da memória persistente."""
    try:
        mem = _load_memory()
        if key not in mem:
            return f"ERRO: Chave '{key}' não existe na memória."
        del mem[key]
        _save_memory(mem)
        return f"✅ Chave '{key}' removida da memória."
    except Exception as e:
        return f"ERRO ao deletar memória: {e}"


def save_session(session_id: str, messages: list) -> str:
    """Salva o histórico completo de uma sessão de conversa."""
    try:
        sessions_path = Path(SESSIONS_DIR)
        sessions_path.mkdir(parents=True, exist_ok=True)
        file = sessions_path / f"{session_id}.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump({"session_id": session_id,
                       "saved_at": datetime.now().isoformat(),
                       "messages": messages}, f, ensure_ascii=False, indent=2)
        return f"✅ Sessão '{session_id}' salva com {len(messages)} mensagens."
    except Exception as e:
        return f"ERRO ao salvar sessão: {e}"


def load_session(session_id: str) -> list:
    """Carrega o histórico de uma sessão salva."""
    try:
        file = Path(SESSIONS_DIR) / f"{session_id}.json"
        if not file.exists():
            return []
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("messages", [])
    except Exception:
        return []


def list_sessions() -> str:
    """Lista todas as sessões salvas."""
    try:
        sessions_path = Path(SESSIONS_DIR)
        if not sessions_path.exists():
            return "Nenhuma sessão salva ainda."
        files = sorted(sessions_path.glob("*.json"), key=os.path.getmtime, reverse=True)
        if not files:
            return "Nenhuma sessão salva ainda."
        output = f"📚 Sessões salvas ({len(files)}):\n"
        for f in files[:20]:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                msg_count = len(data.get("messages", []))
                saved = data.get("saved_at", "N/A")[:19]
                output += f"  • {f.stem} | {msg_count} mensagens | {saved}\n"
            except Exception:
                output += f"  • {f.stem} | (erro ao ler)\n"
        return output
    except Exception as e:
        return f"ERRO ao listar sessões: {e}"
