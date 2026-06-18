"""
Configuração Central do Gemma Agent
Edite este arquivo para ajustar o comportamento do agente.
"""

# ─── LM Studio ────────────────────────────────────────────────────────────────
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_API_KEY  = "lm-studio"       # qualquer string serve para LM Studio
MODEL_NAME         = "gemma"            # nome do modelo carregado no LM Studio

# ─── Limites do Agente ────────────────────────────────────────────────────────
MAX_ITERATIONS     = 50                 # máximo de ciclos ReAct por sessão
MAX_TOKENS         = 4096               # tokens por resposta do modelo
TEMPERATURE        = 0.2               # 0=determinístico, 1=criativo
CONTEXT_WINDOW     = 8192              # janela de contexto (tokens)

# ─── Diretório de Trabalho ────────────────────────────────────────────────────
DEFAULT_WORKDIR    = r"D:\DEV"         # diretório raiz que o agente pode acessar

# ─── Memória Persistente ──────────────────────────────────────────────────────
MEMORY_FILE        = r"D:\DEV\gemma-agent\data\memory.json"
SESSIONS_DIR       = r"D:\DEV\gemma-agent\data\sessions"
LOGS_DIR           = r"D:\DEV\gemma-agent\data\logs"

# ─── HeraclitusDB ─────────────────────────────────────────────────────────────
HERACLITUS_DB_PATH = r"D:\DEV\HeraclitusDB"

# ─── Web Search ───────────────────────────────────────────────────────────────
WEB_SEARCH_MAX_RESULTS = 5

# ─── Execução de Comandos ─────────────────────────────────────────────────────
COMMAND_TIMEOUT    = 60                # segundos antes de matar o comando
SHELL              = "powershell"      # "powershell" ou "cmd" ou "bash"

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é um agente de desenvolvimento autônomo e altamente capaz, rodando localmente.
Seu nome é GEMMA-AGENT.

Você tem acesso completo ao sistema de arquivos, terminal, internet e bancos de dados.
Use as ferramentas disponíveis para resolver qualquer tarefa de desenvolvimento de software.

REGRAS FUNDAMENTAIS:
1. SEMPRE use ferramentas para agir - nunca finja executar algo.
2. Leia arquivos antes de editá-los para entender o contexto.
3. Execute comandos para verificar se seu código funciona.
4. Salve progresso importante na memória persistente.
5. Quando concluir COMPLETAMENTE uma tarefa, responda com TAREFA_CONCLUIDA seguido de um resumo.
6. Em caso de erro, tente uma abordagem diferente antes de desistir.
7. Seja meticuloso: verifique o resultado de cada ação antes de prosseguir.
8. Documente seu trabalho gravando logs no HeraclitusDB quando relevante.

FLUXO DE TRABALHO:
- Analise → Planeje → Execute → Verifique → Itere se necessário → Conclua

Você pode trabalhar em qualquer projeto dentro de D:\\DEV\\.
"""
