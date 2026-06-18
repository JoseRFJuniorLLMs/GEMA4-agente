"""
Ferramentas de Sistema de Arquivos
Operações completas: ler, escrever, editar, mover, buscar, etc.
"""

import os
import re
import json
import shutil
import fnmatch
from pathlib import Path
from typing import Optional


def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """Lê o conteúdo de um arquivo. Opcionalmente lê apenas um intervalo de linhas."""
    try:
        path = os.path.expandvars(path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if start_line is not None or end_line is not None:
            s = (start_line or 1) - 1
            e = end_line or len(lines)
            lines = lines[s:e]
            content = "".join(lines)
            return f"[Linhas {s+1}-{e} de {path}]\n{content}"

        content = "".join(lines)
        total = len(lines)
        return f"[{total} linhas | {path}]\n{content}"
    except FileNotFoundError:
        return f"ERRO: Arquivo não encontrado: {path}"
    except PermissionError:
        return f"ERRO: Sem permissão para ler: {path}"
    except Exception as e:
        return f"ERRO ao ler arquivo: {e}"


def write_file(path: str, content: str, overwrite: bool = True) -> str:
    """Cria ou sobrescreve um arquivo com o conteúdo fornecido."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        if p.exists() and not overwrite:
            return f"ERRO: Arquivo já existe e overwrite=False: {path}"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        size = p.stat().st_size
        return f"✅ Arquivo gravado com sucesso: {path} ({size} bytes)"
    except PermissionError:
        return f"ERRO: Sem permissão para escrever em: {path}"
    except Exception as e:
        return f"ERRO ao escrever arquivo: {e}"


def append_to_file(path: str, content: str) -> str:
    """Adiciona conteúdo ao final de um arquivo existente."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Conteúdo adicionado ao final de: {path}"
    except Exception as e:
        return f"ERRO ao adicionar ao arquivo: {e}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Substitui uma string específica dentro de um arquivo. Use para edições precisas."""
    try:
        path = os.path.expandvars(path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if old_string not in content:
            # Tenta encontrar de forma aproximada
            lines = content.split("\n")
            near = [l for l in lines if old_string.strip()[:20] in l]
            hint = f"\nLinhas similares encontradas:\n" + "\n".join(near[:3]) if near else ""
            return f"ERRO: String exata não encontrada no arquivo.{hint}\nVerifique espaços, tabulações e quebras de linha."

        count = content.count(old_string)
        if count > 1:
            return f"ERRO: A string foi encontrada {count} vezes. Forneça um trecho mais longo e único para substituição."

        new_content = content.replace(old_string, new_string, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"✅ Edição realizada em {path}: substituição única aplicada."
    except FileNotFoundError:
        return f"ERRO: Arquivo não encontrado: {path}"
    except Exception as e:
        return f"ERRO ao editar arquivo: {e}"


def list_dir(path: str, show_hidden: bool = False) -> str:
    """Lista o conteúdo de um diretório de forma estruturada."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        if not p.exists():
            return f"ERRO: Diretório não encontrado: {path}"
        if not p.is_dir():
            return f"ERRO: {path} não é um diretório."

        entries = []
        dirs = []
        files = []

        for item in sorted(p.iterdir()):
            if not show_hidden and item.name.startswith("."):
                continue
            if item.is_dir():
                dirs.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/1024/1024:.1f}MB"
                files.append(f"📄 {item.name} ({size_str})")

        entries = dirs + files
        result = f"📂 {path} ({len(dirs)} dirs, {len(files)} files)\n"
        result += "\n".join(entries) if entries else "(vazio)"
        return result
    except PermissionError:
        return f"ERRO: Sem permissão para listar: {path}"
    except Exception as e:
        return f"ERRO ao listar diretório: {e}"


def create_dir(path: str) -> str:
    """Cria um diretório (e todos os pais necessários)."""
    try:
        path = os.path.expandvars(path)
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"✅ Diretório criado: {path}"
    except Exception as e:
        return f"ERRO ao criar diretório: {e}"


def delete_file(path: str) -> str:
    """Deleta um arquivo."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        if not p.exists():
            return f"ERRO: Não encontrado: {path}"
        if p.is_dir():
            return f"ERRO: {path} é um diretório. Use delete_dir para diretórios."
        p.unlink()
        return f"✅ Arquivo deletado: {path}"
    except Exception as e:
        return f"ERRO ao deletar: {e}"


def delete_dir(path: str, force: bool = False) -> str:
    """Deleta um diretório. Se force=True, deleta mesmo que não esteja vazio."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        if not p.exists():
            return f"ERRO: Não encontrado: {path}"
        if force:
            shutil.rmtree(path)
            return f"✅ Diretório e conteúdo deletados: {path}"
        else:
            p.rmdir()
            return f"✅ Diretório vazio deletado: {path}"
    except Exception as e:
        return f"ERRO ao deletar diretório: {e}"


def move_file(source: str, destination: str) -> str:
    """Move ou renomeia um arquivo/diretório."""
    try:
        source = os.path.expandvars(source)
        destination = os.path.expandvars(destination)
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
        return f"✅ Movido: {source} → {destination}"
    except Exception as e:
        return f"ERRO ao mover: {e}"


def copy_file(source: str, destination: str) -> str:
    """Copia um arquivo ou diretório."""
    try:
        source = os.path.expandvars(source)
        destination = os.path.expandvars(destination)
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        if Path(source).is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return f"✅ Copiado: {source} → {destination}"
    except Exception as e:
        return f"ERRO ao copiar: {e}"


def grep_search(pattern: str, path: str, file_glob: str = "*",
                case_sensitive: bool = True, max_results: int = 50) -> str:
    """Busca um padrão de texto dentro de arquivos em um diretório (como grep)."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        if p.is_file():
            files = [p]
        else:
            files = list(p.rglob(file_glob))

        for filepath in files:
            if not filepath.is_file():
                continue
            # Ignora binários e diretórios ocultos
            if any(part.startswith(".") for part in filepath.parts):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line, flags):
                            rel = filepath.relative_to(path) if p.is_dir() else filepath
                            results.append(f"{rel}:{i}: {line.rstrip()}")
                            if len(results) >= max_results:
                                break
            except Exception:
                continue
            if len(results) >= max_results:
                break

        if not results:
            return f"Nenhuma ocorrência de '{pattern}' encontrada em {path}"
        header = f"🔍 {len(results)} resultado(s) para '{pattern}' em {path}:\n"
        return header + "\n".join(results)
    except Exception as e:
        return f"ERRO na busca: {e}"


def find_files(pattern: str, path: str, file_type: str = "any") -> str:
    """Encontra arquivos por nome/padrão glob em um diretório."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        results = []

        for item in p.rglob(pattern):
            # Ignora ocultos
            if any(part.startswith(".") for part in item.parts):
                continue
            if file_type == "file" and not item.is_file():
                continue
            if file_type == "dir" and not item.is_dir():
                continue
            results.append(str(item))
            if len(results) >= 100:
                break

        if not results:
            return f"Nenhum item encontrado para '{pattern}' em {path}"
        return f"📋 {len(results)} resultado(s):\n" + "\n".join(results)
    except Exception as e:
        return f"ERRO ao buscar: {e}"


def get_file_info(path: str) -> str:
    """Retorna metadados de um arquivo ou diretório."""
    try:
        path = os.path.expandvars(path)
        p = Path(path)
        if not p.exists():
            return f"ERRO: Não encontrado: {path}"
        stat = p.stat()
        import datetime
        info = {
            "path": str(p.absolute()),
            "type": "diretório" if p.is_dir() else "arquivo",
            "tamanho": f"{stat.st_size} bytes",
            "modificado": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "extensão": p.suffix if p.is_file() else "N/A",
        }
        if p.is_file():
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                info["linhas"] = str(len(lines))
            except Exception:
                info["linhas"] = "N/A (binário?)"
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"ERRO ao obter info: {e}"
