"""
Registry de Ferramentas
Registra todas as ferramentas disponíveis no formato OpenAI Tool Calling.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.filesystem import (
    read_file, write_file, append_to_file, edit_file,
    list_dir, create_dir, delete_file, delete_dir,
    move_file, copy_file, grep_search, find_files, get_file_info
)
from tools.shell import run_command, run_python, git_command, install_package, get_system_info
from tools.web import search_web, fetch_url, make_http_request
from tools.memory import memory_save, memory_read, memory_list, memory_delete, list_sessions
from tools.heraclitus import heraclitus_append, heraclitus_read, heraclitus_list_collections
from tools.code_analysis import analyze_project, analyze_python_file, count_todos


# ─── Mapeamento nome → função ─────────────────────────────────────────────────
TOOL_FUNCTIONS = {
    # Filesystem
    "read_file":          read_file,
    "write_file":         write_file,
    "append_to_file":     append_to_file,
    "edit_file":          edit_file,
    "list_dir":           list_dir,
    "create_dir":         create_dir,
    "delete_file":        delete_file,
    "delete_dir":         delete_dir,
    "move_file":          move_file,
    "copy_file":          copy_file,
    "grep_search":        grep_search,
    "find_files":         find_files,
    "get_file_info":      get_file_info,
    # Shell
    "run_command":        run_command,
    "run_python":         run_python,
    "git_command":        git_command,
    "install_package":    install_package,
    "get_system_info":    get_system_info,
    # Web
    "search_web":         search_web,
    "fetch_url":          fetch_url,
    "make_http_request":  make_http_request,
    # Memória
    "memory_save":        memory_save,
    "memory_read":        memory_read,
    "memory_list":        memory_list,
    "memory_delete":      memory_delete,
    "list_sessions":      list_sessions,
    # HeraclitusDB
    "heraclitus_append":            heraclitus_append,
    "heraclitus_read":              heraclitus_read,
    "heraclitus_list_collections":  heraclitus_list_collections,
    # Análise de Código
    "analyze_project":       analyze_project,
    "analyze_python_file":   analyze_python_file,
    "count_todos":           count_todos,
}


# ─── Especificação das Ferramentas (formato OpenAI) ───────────────────────────
TOOLS_SPEC = [
    # ── FILESYSTEM ──────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê o conteúdo de um arquivo. Use para ler código, configs, logs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho absoluto do arquivo"},
                    "start_line": {"type": "integer", "description": "Linha inicial (opcional)"},
                    "end_line": {"type": "integer", "description": "Linha final (opcional)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Cria ou sobrescreve um arquivo com o conteúdo fornecido. Cria diretórios pais automaticamente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho absoluto do arquivo"},
                    "content": {"type": "string", "description": "Conteúdo completo a escrever"},
                    "overwrite": {"type": "boolean", "description": "Sobrescrever se existir (padrão: true)"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_to_file",
            "description": "Adiciona conteúdo ao final de um arquivo sem sobrescrever o existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do arquivo"},
                    "content": {"type": "string", "description": "Conteúdo a adicionar"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Substitui um trecho específico de texto em um arquivo. Use para edições cirúrgicas sem reescrever o arquivo todo. A string old_string DEVE existir exatamente uma vez no arquivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do arquivo"},
                    "old_string": {"type": "string", "description": "Texto exato a substituir (deve ser único no arquivo)"},
                    "new_string": {"type": "string", "description": "Texto de substituição"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Lista arquivos e subdiretórios de um diretório.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do diretório"},
                    "show_hidden": {"type": "boolean", "description": "Mostrar arquivos ocultos (padrão: false)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_dir",
            "description": "Cria um diretório (incluindo pais) se não existir.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do diretório a criar"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Deleta um arquivo permanentemente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do arquivo a deletar"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_dir",
            "description": "Deleta um diretório. Use force=true para deletar com conteúdo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do diretório"},
                    "force": {"type": "boolean", "description": "Deletar mesmo com conteúdo (padrão: false)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move ou renomeia um arquivo ou diretório.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Caminho de origem"},
                    "destination": {"type": "string", "description": "Caminho de destino"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copia um arquivo ou diretório para outro local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Caminho de origem"},
                    "destination": {"type": "string", "description": "Caminho de destino"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Busca um padrão de texto (regex ou literal) dentro de arquivos. Retorna linha e número.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Padrão de busca (regex ou texto)"},
                    "path": {"type": "string", "description": "Arquivo ou diretório onde buscar"},
                    "file_glob": {"type": "string", "description": "Filtro de arquivo (ex: '*.py', '*.json'). Padrão: '*'"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive (padrão: true)"},
                    "max_results": {"type": "integer", "description": "Máximo de resultados (padrão: 50)"},
                },
                "required": ["pattern", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Encontra arquivos por padrão de nome (glob) em um diretório.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Padrão glob (ex: '*.py', 'requirements*.txt')"},
                    "path": {"type": "string", "description": "Diretório raiz da busca"},
                    "file_type": {"type": "string", "enum": ["any", "file", "dir"], "description": "Tipo a buscar (padrão: 'any')"},
                },
                "required": ["pattern", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_info",
            "description": "Retorna metadados de um arquivo: tamanho, data de modificação, número de linhas, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do arquivo ou diretório"},
                },
                "required": ["path"],
            },
        },
    },

    # ── SHELL ────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executa qualquer comando no PowerShell/terminal. Use para npm, pip, compilar, testar, listar processos, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando a executar"},
                    "cwd": {"type": "string", "description": "Diretório de trabalho (padrão: D:\\DEV)"},
                    "timeout": {"type": "integer", "description": "Timeout em segundos (padrão: 60)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Executa um trecho de código Python diretamente. Ideal para scripts, cálculos e testes rápidos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Código Python completo a executar"},
                    "cwd": {"type": "string", "description": "Diretório de trabalho"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_command",
            "description": "Executa um comando git (sem o prefixo 'git'). Ex: 'status', 'add .', 'commit -m \"msg\"'",
            "parameters": {
                "type": "object",
                "properties": {
                    "args": {"type": "string", "description": "Argumentos do git (sem 'git' no início)"},
                    "cwd": {"type": "string", "description": "Repositório git de trabalho"},
                },
                "required": ["args"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "install_package",
            "description": "Instala um pacote Python via pip.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Nome do pacote (ex: 'requests', 'fastapi==0.100.0')"},
                    "cwd": {"type": "string", "description": "Diretório de trabalho"},
                },
                "required": ["package"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Retorna informações do sistema: versão Python, Git, Node.js, PowerShell.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ── WEB ──────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca informações atualizadas na web via DuckDuckGo. Use para pesquisar documentação, tutoriais, erros, notícias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de busca"},
                    "max_results": {"type": "integer", "description": "Número de resultados (padrão: 5)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Baixa e extrai o texto de uma página web. Use para ler documentação, artigos e READMEs online.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL da página a ler"},
                    "max_chars": {"type": "integer", "description": "Máximo de caracteres a retornar (padrão: 8000)"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_http_request",
            "description": "Faz uma requisição HTTP genérica (GET, POST, PUT, etc). Útil para testar APIs REST.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL completa"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "description": "Método HTTP"},
                    "headers": {"type": "object", "description": "Headers HTTP (dicionário)"},
                    "body": {"type": "string", "description": "Corpo da requisição (JSON string)"},
                },
                "required": ["url"],
            },
        },
    },

    # ── MEMÓRIA ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "memory_save",
            "description": "Salva informação importante na memória persistente (persiste entre sessões). Use para guardar contexto, decisões, configurações de projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Identificador único (ex: 'eva_db_host', 'projeto_atual')"},
                    "value": {"type": "string", "description": "Valor a armazenar"},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_read",
            "description": "Lê um valor da memória persistente pelo nome da chave.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Chave a buscar na memória"},
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_list",
            "description": "Lista todas as chaves e valores armazenados na memória persistente.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_delete",
            "description": "Remove uma chave da memória persistente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Chave a remover"},
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_sessions",
            "description": "Lista todas as sessões de conversa salvas anteriormente.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ── HERACLITUSDB ─────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "heraclitus_append",
            "description": "Grava um evento imutável no HeraclitusDB (log append-only). Use para registrar decisões, logs de agente, resultados de tarefas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Nome da coleção (ex: 'agent_logs', 'decisoes', 'bugs_encontrados')"},
                    "data": {"type": "string", "description": "Dados a gravar (texto ou JSON serializado)"},
                    "metadata": {"type": "object", "description": "Metadados adicionais (dicionário opcional)"},
                },
                "required": ["collection", "data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "heraclitus_read",
            "description": "Lê os últimos N registros de uma coleção do HeraclitusDB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Nome da coleção"},
                    "limit": {"type": "integer", "description": "Máximo de registros a retornar (padrão: 20)"},
                },
                "required": ["collection"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "heraclitus_list_collections",
            "description": "Lista todas as coleções existentes no HeraclitusDB com contagem de registros.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },

    # ── ANÁLISE DE CÓDIGO ────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "analyze_project",
            "description": "Analisa a estrutura completa de um projeto: linguagens usadas, total de linhas, arquivos, pontos de entrada e dependências detectadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho raiz do projeto a analisar"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_python_file",
            "description": "Analisa um arquivo Python: classes, métodos, funções de nível superior e imports. Útil para entender a estrutura antes de editar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Caminho do arquivo .py"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_todos",
            "description": "Encontra todos os comentários TODO, FIXME, HACK, BUG e NOTE em um projeto ou arquivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Arquivo ou diretório raiz para buscar"},
                },
                "required": ["path"],
            },
        },
    },
]

