"""
Ferramenta de Busca na Web
Usa DuckDuckGo (sem API key) + extração de conteúdo de páginas.
"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from config import WEB_SEARCH_MAX_RESULTS


def search_web(query: str, max_results: int = None) -> str:
    """
    Busca informações na web usando DuckDuckGo.
    Retorna título, URL e snippet dos resultados.
    """
    max_results = max_results or WEB_SEARCH_MAX_RESULTS
    try:
        # DuckDuckGo HTML search (sem API key)
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")

        # Extrai resultados via regex simples
        results = []
        # Padrão para links de resultado
        link_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        snippet_pattern = re.compile(
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        # Limpeza de HTML
        def clean(text):
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"&amp;", "&", text)
            text = re.sub(r"&lt;", "<", text)
            text = re.sub(r"&gt;", ">", text)
            text = re.sub(r"&quot;", '"', text)
            text = re.sub(r"&#x27;", "'", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text

        for i, (href, title) in enumerate(links[:max_results]):
            snippet = clean(snippets[i]) if i < len(snippets) else ""
            # Extrai URL real de redirecionamentos DuckDuckGo
            if "uddg=" in href:
                try:
                    href = urllib.parse.unquote(href.split("uddg=")[-1].split("&")[0])
                except Exception:
                    pass
            results.append({
                "titulo": clean(title),
                "url": href,
                "resumo": snippet
            })

        if not results:
            return f"Nenhum resultado encontrado para: {query}"

        output = f"🌐 Resultados para '{query}':\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. **{r['titulo']}**\n"
            output += f"   URL: {r['url']}\n"
            output += f"   {r['resumo']}\n\n"
        return output

    except urllib.error.URLError as e:
        return f"ERRO de rede ao buscar: {e}. Verifique sua conexão."
    except Exception as e:
        return f"ERRO na busca web: {e}"


def fetch_url(url: str, max_chars: int = 8000) -> str:
    """
    Faz o download e extrai o texto de uma página web.
    Útil para ler documentação, artigos e READMEs online.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()

            # Detecta encoding
            encoding = "utf-8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].strip()

            html = raw.decode(encoding, errors="replace")

        # Remove scripts, estilos e tags
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<nav[^>]*>.*?</nav>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<header[^>]*>.*?</header>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<footer[^>]*>.*?</footer>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<[^>]+>", " ", html)

        # Limpa entidades HTML
        replacements = {"&amp;": "&", "&lt;": "<", "&gt;": ">",
                        "&quot;": '"', "&#x27;": "'", "&nbsp;": " ", "&#39;": "'"}
        for k, v in replacements.items():
            html = html.replace(k, v)

        # Normaliza espaços
        text = re.sub(r"\n{3,}", "\n\n", html)
        text = re.sub(r" {2,}", " ", text).strip()

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... conteúdo truncado após {max_chars} chars]"

        return f"📄 Conteúdo de {url}:\n\n{text}"

    except urllib.error.HTTPError as e:
        return f"ERRO HTTP {e.code}: {e.reason} em {url}"
    except urllib.error.URLError as e:
        return f"ERRO de rede: {e}. URL: {url}"
    except Exception as e:
        return f"ERRO ao buscar URL: {e}"


def make_http_request(url: str, method: str = "GET",
                      headers: dict = None, body: str = None) -> str:
    """
    Faz uma requisição HTTP genérica. Útil para testar APIs e webhooks.
    
    Args:
        url: URL completa
        method: GET, POST, PUT, DELETE, PATCH
        headers: Dicionário de headers (ex: {"Authorization": "Bearer token"})
        body: Corpo da requisição em string (ex: JSON serializado)
    """
    try:
        data = body.encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, method=method.upper())

        # Headers padrão
        req.add_header("User-Agent", "GemmaAgent/1.0")
        req.add_header("Content-Type", "application/json")

        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            resp_body = response.read().decode("utf-8", errors="replace")

            # Tenta formatar JSON
            try:
                parsed = json.loads(resp_body)
                resp_body = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                pass

            return f"✅ HTTP {status}\n{resp_body[:5000]}"

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return f"❌ HTTP {e.code} {e.reason}\n{err_body[:2000]}"
    except Exception as e:
        return f"ERRO na requisição HTTP: {e}"
