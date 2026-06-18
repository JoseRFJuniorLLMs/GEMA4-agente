"""
Ferramenta de Análise de Código
Analisa estrutura de projetos, dependências, complexidade e qualidade.
"""

import os
import re
import ast
import json
from pathlib import Path
from collections import defaultdict


# Extensões conhecidas por linguagem
LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JSX", ".tsx": "TSX", ".html": "HTML", ".css": "CSS",
    ".scss": "SCSS", ".json": "JSON", ".md": "Markdown", ".sql": "SQL",
    ".sh": "Shell", ".ps1": "PowerShell", ".bat": "Batch",
    ".java": "Java", ".go": "Go", ".rs": "Rust", ".cpp": "C++",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".yaml": "YAML",
    ".yml": "YAML", ".toml": "TOML",
}


IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", ".next", "coverage",
    ".mypy_cache", ".ruff_cache", "eggs", ".eggs",
}


def analyze_project(path: str) -> str:
    """
    Analisa a estrutura completa de um projeto: linguagens, linhas de código,
    arquivos, dependências detectadas e ponto de entrada.
    """
    try:
        path = os.path.expandvars(path)
        root = Path(path)
        if not root.exists():
            return f"ERRO: Caminho não encontrado: {path}"

        stats = defaultdict(lambda: {"files": 0, "lines": 0})
        total_files = 0
        total_lines = 0
        entry_points = []
        dep_files = []
        all_files = []

        for item in root.rglob("*"):
            # Ignora diretórios banidos
            if any(part in IGNORE_DIRS for part in item.parts):
                continue
            if not item.is_file():
                continue

            total_files += 1
            ext = item.suffix.lower()
            lang = LANG_MAP.get(ext, ext if ext else "outros")

            try:
                with open(item, "r", encoding="utf-8", errors="ignore") as f:
                    lines = sum(1 for _ in f)
                stats[lang]["files"] += 1
                stats[lang]["lines"] += lines
                total_lines += lines
            except Exception:
                stats[lang]["files"] += 1

            rel = str(item.relative_to(root))
            all_files.append(rel)

            # Detecta pontos de entrada
            name = item.name.lower()
            if name in ("main.py", "app.py", "server.py", "index.py",
                         "agent.py", "run.py", "__main__.py",
                         "index.js", "index.ts", "main.js", "main.ts",
                         "app.js", "server.js", "manage.py"):
                entry_points.append(rel)

            # Detecta arquivos de dependência
            if name in ("requirements.txt", "package.json", "pyproject.toml",
                        "setup.py", "setup.cfg", "cargo.toml", "go.mod",
                        "pom.xml", "build.gradle", "gemfile", "composer.json"):
                dep_files.append(rel)

        # Monta relatório
        out = f"📊 ANÁLISE DE PROJETO: {root.name}\n"
        out += f"{'─'*50}\n"
        out += f"📁 Total de arquivos : {total_files}\n"
        out += f"📝 Total de linhas   : {total_lines:,}\n\n"

        out += "🔤 Linguagens detectadas:\n"
        sorted_langs = sorted(stats.items(), key=lambda x: x[1]["lines"], reverse=True)
        for lang, data in sorted_langs[:12]:
            pct = (data["lines"] / total_lines * 100) if total_lines > 0 else 0
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            out += f"  {lang:<15} {bar} {pct:5.1f}%  ({data['files']} arq, {data['lines']:,} linhas)\n"

        if entry_points:
            out += f"\n🚀 Pontos de entrada detectados:\n"
            for ep in entry_points:
                out += f"  • {ep}\n"

        if dep_files:
            out += f"\n📦 Arquivos de dependências:\n"
            for df in dep_files:
                out += f"  • {df}\n"

        return out

    except Exception as e:
        return f"ERRO na análise: {e}"


def analyze_python_file(path: str) -> str:
    """
    Analisa um arquivo Python: classes, funções, imports e complexidade básica.
    """
    try:
        path = os.path.expandvars(path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()

        tree = ast.parse(source, filename=path)

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                classes.append({"name": node.name, "line": node.lineno, "methods": methods})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not any(node.col_offset > 0 for _ in [node]):
                    functions.append({"name": node.name, "line": node.lineno,
                                       "async": isinstance(node, ast.AsyncFunctionDef)})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}")

        lines = source.split("\n")
        out = f"🐍 ANÁLISE PYTHON: {Path(path).name}\n"
        out += f"{'─'*50}\n"
        out += f"📝 Linhas: {len(lines)} | Chars: {len(source):,}\n\n"

        if classes:
            out += f"🏛️ Classes ({len(classes)}):\n"
            for c in classes:
                out += f"  • {c['name']} (L{c['line']}) → {len(c['methods'])} métodos: {', '.join(c['methods'][:5])}\n"

        top_fns = [f for f in functions if f["name"] != "__init__"][:15]
        if top_fns:
            out += f"\n⚙️ Funções de nível superior ({len(top_fns)}):\n"
            for fn in top_fns:
                prefix = "async " if fn["async"] else ""
                out += f"  • {prefix}{fn['name']} (L{fn['line']})\n"

        unique_imports = sorted(set(imports))[:20]
        if unique_imports:
            out += f"\n📦 Imports ({len(unique_imports)}):\n"
            out += "  " + ", ".join(unique_imports) + "\n"

        return out

    except SyntaxError as e:
        return f"❌ ERRO DE SINTAXE em {path}: {e}"
    except Exception as e:
        return f"ERRO na análise Python: {e}"


def count_todos(path: str) -> str:
    """Encontra todos os TODO, FIXME, HACK, XXX e NOTE em um projeto."""
    try:
        path = os.path.expandvars(path)
        root = Path(path)
        pattern = re.compile(r"(TODO|FIXME|HACK|XXX|NOTE|BUG|OPTIMIZE)[\s:](.*)",
                             re.IGNORECASE)
        found = []

        for item in root.rglob("*"):
            if any(part in IGNORE_DIRS for part in item.parts):
                continue
            if not item.is_file():
                continue
            if item.suffix not in (".py", ".js", ".ts", ".jsx", ".tsx",
                                    ".java", ".go", ".rs", ".cs", ".cpp"):
                continue
            try:
                with open(item, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        m = pattern.search(line)
                        if m:
                            rel = item.relative_to(root)
                            found.append(f"[{m.group(1)}] {rel}:{i} — {m.group(2).strip()[:80]}")
            except Exception:
                continue

        if not found:
            return f"✅ Nenhum TODO/FIXME encontrado em {path}"

        out = f"📋 {len(found)} item(ns) encontrado(s) em {path}:\n\n"
        out += "\n".join(found)
        return out

    except Exception as e:
        return f"ERRO ao buscar TODOs: {e}"
