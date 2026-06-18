"""
Testes de verificação do GEMMA-AGENT
Verifica se todas as ferramentas importam corretamente e estão funcionais.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("[TEST] Testando imports...")
    failures = []

    modules = [
        ("config", ["LM_STUDIO_BASE_URL", "MODEL_NAME", "SYSTEM_PROMPT"]),
        ("tools.filesystem", ["read_file", "write_file", "edit_file", "list_dir", "grep_search"]),
        ("tools.shell", ["run_command", "run_python", "git_command"]),
        ("tools.web", ["search_web", "fetch_url", "make_http_request"]),
        ("tools.memory", ["memory_save", "memory_read", "memory_list"]),
        ("tools.heraclitus", ["heraclitus_append", "heraclitus_read"]),
        ("tools.code_analysis", ["analyze_project", "analyze_python_file"]),
        ("core.registry", ["TOOL_FUNCTIONS", "TOOLS_SPEC"]),
        ("core.loop", ["AgentLoop"]),
    ]

    for mod_name, attrs in modules:
        try:
            mod = __import__(mod_name, fromlist=attrs)
            for attr in attrs:
                if not hasattr(mod, attr):
                    failures.append(f"  ❌ {mod_name}.{attr} — atributo não encontrado")
                    continue
            print(f"  [OK] {mod_name}")
        except ImportError as e:
            failures.append(f"  [FAIL] {mod_name} -- {e}")
        except Exception as e:
            failures.append(f"  [WARN] {mod_name} -- {e}")

    return failures


def test_filesystem_tools():
    print("\n[TEST] Testando ferramentas de filesystem...")
    from tools.filesystem import write_file, read_file, edit_file, delete_file, list_dir

    test_path = os.path.join(os.path.dirname(__file__), "data", "_test_file.txt")
    failures = []

    # write
    r = write_file(test_path, "linha 1\nlinha 2\nlinha 3\n")
    if "✅" not in r:
        failures.append(f"  ❌ write_file: {r}")
    else:
        print("  ✅ write_file")

    # read
    r = read_file(test_path)
    if "linha 1" not in r:
        failures.append(f"  ❌ read_file: {r}")
    else:
        print("  ✅ read_file")

    # edit
    r = edit_file(test_path, "linha 2", "LINHA EDITADA")
    if "✅" not in r:
        failures.append(f"  ❌ edit_file: {r}")
    else:
        print("  ✅ edit_file")

    # verifica edição
    content = read_file(test_path)
    if "LINHA EDITADA" not in content:
        failures.append("  ❌ edit_file não funcionou corretamente")
    else:
        print("  ✅ edit_file verificado")

    # list_dir
    r = list_dir(os.path.dirname(__file__))
    if "agent.py" not in r and "ERRO" in r:
        failures.append(f"  ❌ list_dir: {r}")
    else:
        print("  ✅ list_dir")

    # delete
    r = delete_file(test_path)
    if "✅" not in r:
        failures.append(f"  ❌ delete_file: {r}")
    else:
        print("  ✅ delete_file")

    return failures


def test_shell_tools():
    print("\n[TEST] Testando ferramentas de shell...")
    from tools.shell import run_command, run_python
    failures = []

    # run_command simples
    r = run_command("echo 'Olá GEMMA-AGENT'")
    if "ERRO" in r and "Olá" not in r and "Ol" not in r:
        failures.append(f"  ❌ run_command: {r}")
    else:
        print("  ✅ run_command")

    # run_python
    r = run_python("print('Python OK:', 2 + 2)")
    if "4" not in r:
        failures.append(f"  ❌ run_python: {r}")
    else:
        print("  ✅ run_python")

    return failures


def test_memory_tools():
    print("\n[TEST] Testando ferramentas de memoria...")
    from tools.memory import memory_save, memory_read, memory_delete
    failures = []

    r = memory_save("_test_key", "valor de teste 123")
    if "✅" not in r:
        failures.append(f"  ❌ memory_save: {r}")
    else:
        print("  ✅ memory_save")

    r = memory_read("_test_key")
    if "valor de teste 123" not in r:
        failures.append(f"  ❌ memory_read: {r}")
    else:
        print("  ✅ memory_read")

    r = memory_delete("_test_key")
    if "✅" not in r:
        failures.append(f"  ❌ memory_delete: {r}")
    else:
        print("  ✅ memory_delete")

    return failures


def test_heraclitus():
    print("\n[TEST] Testando HeraclitusDB...")
    from tools.heraclitus import heraclitus_append, heraclitus_list_collections
    failures = []

    r = heraclitus_append("agent_test", "Teste de gravação do GEMMA-AGENT",
                           {"origem": "test_agent.py"})
    if "✅" not in r:
        failures.append(f"  ❌ heraclitus_append: {r}")
    else:
        print("  ✅ heraclitus_append")

    r = heraclitus_list_collections()
    if "ERRO" in r and "agent_test" not in r:
        failures.append(f"  ❌ heraclitus_list_collections: {r}")
    else:
        print("  ✅ heraclitus_list_collections")

    return failures


def test_registry():
    print("\n[TEST] Testando registry de ferramentas...")
    from core.registry import TOOL_FUNCTIONS, TOOLS_SPEC
    failures = []

    if len(TOOL_FUNCTIONS) < 20:
        failures.append(f"  ❌ Poucas ferramentas: {len(TOOL_FUNCTIONS)}")
    else:
        print(f"  ✅ {len(TOOL_FUNCTIONS)} funções registradas")

    if len(TOOLS_SPEC) < 20:
        failures.append(f"  ❌ Poucas specs: {len(TOOLS_SPEC)}")
    else:
        print(f"  ✅ {len(TOOLS_SPEC)} specs OpenAI registradas")

    # Verifica que todas as funções no registry têm spec correspondente
    spec_names = {t["function"]["name"] for t in TOOLS_SPEC}
    func_names = set(TOOL_FUNCTIONS.keys())
    missing_specs = func_names - spec_names
    if missing_specs:
        failures.append(f"  ⚠️  Funções sem spec: {missing_specs}")
    else:
        print("  ✅ Todas as funções têm spec OpenAI correspondente")

    return failures


def run_all_tests():
    print("=" * 55)
    print("  GEMMA-AGENT — Suite de Testes")
    print("=" * 55)

    all_failures = []
    all_failures += test_imports()
    all_failures += test_filesystem_tools()
    all_failures += test_shell_tools()
    all_failures += test_memory_tools()
    all_failures += test_heraclitus()
    all_failures += test_registry()

    print("\n" + "=" * 55)
    if all_failures:
        print(f"❌ {len(all_failures)} FALHA(S) ENCONTRADA(S):")
        for f in all_failures:
            print(f)
        return False
    else:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("   O GEMMA-AGENT está pronto para uso.")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
