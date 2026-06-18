"""
Context Manager — Gerenciamento Inteligente de Contexto
Evita estouro de contexto comprimindo ou cortando mensagens antigas.
"""

import json
import tiktoken
from typing import Optional


def estimate_tokens(text: str) -> int:
    """
    Estima o número de tokens em um texto.
    Usa regra de ~4 chars por token como fallback rápido.
    """
    if not text:
        return 0
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Fallback: ~4 chars por token (boa estimativa para modelos modernos)
        return len(text) // 4


def count_messages_tokens(messages: list) -> int:
    """Conta o total de tokens em todo o histórico de mensagens."""
    total = 0
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if content:
                total += estimate_tokens(str(content))
            # tool calls no formato OpenAI
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    if hasattr(tc, "function"):
                        total += estimate_tokens(tc.function.arguments or "")
                    elif isinstance(tc, dict):
                        total += estimate_tokens(json.dumps(tc))
        elif hasattr(msg, "content") and msg.content:
            total += estimate_tokens(str(msg.content))
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    total += estimate_tokens(tc.function.arguments or "")
    return total


def summarize_tool_result(content: str, max_chars: int = 800) -> str:
    """Resume resultados de ferramentas longos para economizar contexto."""
    if not content or len(content) <= max_chars:
        return content
    # Mantém início e final
    half = max_chars // 2
    return (content[:half] +
            f"\n\n[... {len(content) - max_chars} chars omitidos para economizar contexto ...]\n\n" +
            content[-half:])


def trim_context(messages: list, max_tokens: int = 6000,
                 keep_system: bool = True,
                 keep_last_n: int = 8) -> list:
    """
    Reduz o histórico de mensagens para caber na janela de contexto.
    
    Estratégia:
    1. Sempre mantém o system prompt
    2. Sempre mantém as últimas N mensagens
    3. Resume resultados de tool calls antigos
    4. Remove mensagens intermediárias se necessário
    
    Args:
        messages: Lista de mensagens do chat
        max_tokens: Máximo de tokens permitidos
        keep_system: Manter o system prompt
        keep_last_n: Número de mensagens recentes a sempre manter
    
    Returns:
        Lista de mensagens trimada
    """
    current_tokens = count_messages_tokens(messages)

    if current_tokens <= max_tokens:
        return messages  # Cabe, sem cortes

    result = []

    # 1. Separa system prompt
    system_msgs = []
    other_msgs = []
    for msg in messages:
        role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", "")
        if role == "system" and keep_system:
            system_msgs.append(msg)
        else:
            other_msgs.append(msg)

    # 2. Mensagens recentes (intocáveis)
    recent = other_msgs[-keep_last_n:] if len(other_msgs) > keep_last_n else other_msgs
    older = other_msgs[:-keep_last_n] if len(other_msgs) > keep_last_n else []

    # 3. Resume tool results antigos
    compressed_older = []
    for msg in older:
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "tool" and content and len(content) > 200:
                compressed = dict(msg)
                compressed["content"] = summarize_tool_result(content, 200)
                compressed_older.append(compressed)
            else:
                compressed_older.append(msg)
        else:
            compressed_older.append(msg)

    # 4. Verifica se cabe
    candidate = system_msgs + compressed_older + recent
    if count_messages_tokens(candidate) <= max_tokens:
        return candidate

    # 5. Ainda não cabe — insere resumo e descarta mensagens antigas
    summary_msg = {
        "role": "system",
        "content": (f"[CONTEXTO COMPRIMIDO: {len(older)} mensagens anteriores foram removidas "
                    f"para economizar contexto. Apenas as {keep_last_n} mensagens mais recentes "
                    f"foram mantidas. Continue a partir do contexto disponível.]")
    }

    candidate = system_msgs + [summary_msg] + recent
    if count_messages_tokens(candidate) <= max_tokens:
        return candidate

    # 6. Último recurso: mantém apenas system + últimas 4
    minimal_recent = recent[-4:] if len(recent) > 4 else recent
    return system_msgs + [summary_msg] + minimal_recent


def get_context_stats(messages: list, max_tokens: int = 8192) -> dict:
    """
    Retorna estatísticas de uso do contexto.
    Útil para monitorar e debugar uso de tokens.
    """
    total_tokens = count_messages_tokens(messages)
    pct = (total_tokens / max_tokens * 100) if max_tokens > 0 else 0

    roles = {}
    for msg in messages:
        role = msg.get("role", "?") if isinstance(msg, dict) else getattr(msg, "role", "?")
        if role not in roles:
            roles[role] = 0
        roles[role] += 1

    return {
        "total_tokens": total_tokens,
        "max_tokens": max_tokens,
        "uso_percentual": f"{pct:.1f}%",
        "mensagens": len(messages),
        "por_role": roles,
        "status": "OK" if pct < 80 else "ALERTA" if pct < 95 else "CRITICO",
    }
