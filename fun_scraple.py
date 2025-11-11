import requests
from bs4 import BeautifulSoup

import re
from urllib.parse import urlparse
from html import unescape

def scrape_and_text(url, filename):
    try:
        # Realizar la solicitud HTTP a la URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza un error para respuestas HTTP no exitosas

        # Analizar el contenido HTML de la página
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer todo el texto de la página como str
        text = soup.get_text(separator='\n', strip=True)

        # Devolver título y texto juntos
        return text

    except requests.exceptions.RequestException as e:
        print(f"Error al intentar acceder a la URL: {e}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")

# Generic junk often found before/after the real article
_START_DROP_PATTERNS = [
    r'^(The Standard|Sign in|News|Sport|Business|Lifestyle|Culture|Going Out|Homes & Property|Comment)\b',
    r'^(Home|News|Royals|U\.S\.|Sport|TV|Showbiz|Health|Science|Money|Travel|Podcasts|My Profile|Login|Logout|UK Edition)\b',
    r'^(UK|US|Australia|International) edition\b',
    r'^(Skip to (main content|navigation)|Support us)\b',
    r'^(Privacy|Cookie|Terms|Advertise|Contact Us|About us)\b',
    r'^\d{1,2}(AM|PM)$', r'^\d+°C$', r'^\d{1,2}\s*(shares|comments)\b',
    r'^\|?\s*Updated:\s*', r'^Published:\s*'
]

# Site-specific “stop before” markers (trim everything after these)
_DOMAIN_RULES = {
    'www.standard.co.uk': {  # Evening Standard
        'stop_before': [r'^Read More\b', r'^MORE ABOUT\b', r'^Have your say', r'^VIEW\b', r'^Most Read\b'],
    },
    'www.theguardian.com': {  # The Guardian
        'stop_before': [r'^Explore more on these topics', r'^Most viewed\b', r'^About us\b', r'^©'],
    },
    'www.dailymail.co.uk': {  # Daily Mail
        'stop_before': [r'^Share or comment', r'^Comments\b', r'^NEW ARTICLES\b', r'^Home$'],
    }
}

def clean_middle_article(text: str, url: str = None, title: str = None, keep_min_chars: int = 1200) -> str:
    """
    Keep the central article body:
      1) Drop obvious nav/header lines.
      2) Cut tail at common 'stop' sections (Read More, Comments, Most Read, etc.).
      3) Split into blocks and choose the most 'article-like' block (longest, sentence-y).
      4) Merge adjacent blocks if helpful and ensure a minimum size.
    """
    if not text:
        return text

    t = unescape(text).replace("\r", "")
    domain = urlparse(url).netloc.lower() if url else ""
    stop_pats = _DOMAIN_RULES.get(domain, {}).get('stop_before', [])
    stop_res = [re.compile(pat, re.I) for pat in stop_pats]
    drop_res = [re.compile(pat, re.I) for pat in _START_DROP_PATTERNS]

    # 1) Line-wise prefilter to remove obvious menu/utility lines
    keep_lines = []
    for ln in (ln.strip() for ln in t.split("\n")):
        if not ln:
            keep_lines.append("")  # keep paragraph boundaries
            continue
        if any(rx.search(ln) for rx in drop_res):
            continue
        keep_lines.append(ln)

    s = "\n".join(keep_lines)

    # 2) Hard cut at the first site-specific 'stop' marker we see
    for rx in stop_res:
        m = rx.search(s)
        if m:
            s = s[:m.start()]
            break

    # 3) Split into text blocks (paragraph groups) and score them
    blocks = [b.strip() for b in re.split(r"\n{2,}", s) if b.strip()]
    if not blocks:
        return s.strip()

    def score(block: str) -> float:
        chars = len(block)
        alpha = sum(c.isalpha() for c in block)
        digits = sum(c.isdigit() for c in block)
        lines = block.count("\n") + 1
        avg_line = chars / max(lines, 1)
        # prefer long, alphabetic, paragraph-like text
        return alpha - digits + 0.5 * avg_line

    best_i = max(range(len(blocks)), key=lambda i: score(blocks[i]))

    # Merge neighbor blocks if they’re substantial (typical multi-paragraph article)
    keep_idx = {best_i}
    if best_i > 0 and len(blocks[best_i - 1]) > 200:
        keep_idx.add(best_i - 1)
    if best_i + 1 < len(blocks) and len(blocks[best_i + 1]) > 200:
        keep_idx.add(best_i + 1)

    body = "\n\n".join(blocks[i] for i in sorted(keep_idx)).strip()

    # 4) If still short, append next-best blocks until we reach a reasonable length
    if len(body) < keep_min_chars:
        rest = sorted(
            ((i, score(b)) for i, b in enumerate(blocks) if i not in keep_idx),
            key=lambda x: x[1],
            reverse=True,
        )
        for i, _ in rest:
            body = (body + "\n\n" + blocks[i]).strip() if body else blocks[i]
            if len(body) >= keep_min_chars:
                break

    # 5) De-duplicate a title echoed at the top
    if title and body.lower().startswith(title.lower()):
        body = body[len(title):].lstrip()

    # Tidy excess whitespace
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body
