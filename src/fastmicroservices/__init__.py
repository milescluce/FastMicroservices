from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from loguru import logger as log

from toomanysessions import SessionedServer
from toomanythreads import ThreadedServer

DEBUG = True
ACCEPTED_TYPES = [ThreadedServer, SessionedServer]

def check_type(self):
    type_matches = 0
    for typ in ACCEPTED_TYPES:
        if not isinstance(self, typ): continue
        type_matches = type_matches + 1
    if type_matches == 0: raise TypeError(f"Inheriting class is not one of the following: {ACCEPTED_TYPES}")

def is_sessioned_server(self: object) -> bool:
    return isinstance(self, SessionedServer)

def are_both_sessioned_server(a: object, b: object) -> bool:
    if is_sessioned_server(a) and is_sessioned_server(b): return True
    else: return False

DEFAULT_INDEX = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FastMicroservices</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #1a1a2e;
            color: white;
            height: 100vh;
            overflow: hidden;
        }

        .topbar {
            height: 60px;
            background: #2d2d44;
            border-bottom: 1px solid #444;
            display: flex;
            align-items: center;
            padding: 0 1rem;
            gap: 2rem;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
        }

        .nav-buttons {
            display: flex;
            gap: 0.5rem;
        }

        .nav-btn {
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            color: white;
            text-decoration: none;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .nav-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }

        .nav-btn.active {
            background: #4f46e5;
            border-color: #4f46e5;
        }

        .main-content {
            height: calc(100vh - 60px);
            width: 100%;
        }

        .main-content iframe {
            width: 100%;
            height: 100%;
            border: none;
            display: block;
        }

        .welcome {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }

        .welcome h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        .welcome p {
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="logo">PhazeDash</div>

        <nav class="nav-buttons">
            {% for page in pages %}
            <a class="nav-btn"
               hx-get="/page/{{ page.name }}"
               hx-target="#main-content"
               data-page="{{ page.name }}"
               onclick="setActiveButton(this)">
                {{ page.title }}
            </a>
            {% endfor %}
        </nav>
    </div>

    <div id="main-content" class="main-content"
         hx-get="/page/dashboard"
         hx-trigger="load"
         hx-swap="innerHTML">
        <div class="welcome">
            <div>
                <h1>Welcome to PhazeDash</h1>
                <p>Select a service from the navigation above to get started.</p>
            </div>
        </div>
    </div>

    <script>
        function setActiveButton(clickedButton) {
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            clickedButton.classList.add('active');
        }
    </script>
</body>
</html>
"""

@dataclass
class PageConfig:
    name: str
    title: str
    type: str
    cwd: Path
    obj: object
    color: Optional[str] = None  # hex color for styling
    icon: Optional[str] = None  # icon class or emoji
    auto_discovered: bool = False  # flag for auto-discovered pages


def extract_title_from_html(html_file: Path) -> Optional[str]:
    """Extract title from HTML file's <title> tag"""
    try:
        content = html_file.read_text(encoding='utf-8')
        import re
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            log.debug(f"Extracted title '{title}' from {html_file.name}")
            return title
    except Exception as e:
        log.debug(f"Could not extract title from {html_file.name}: {e}")
    return None


def generate_color_from_name(name: str) -> str:
    """Generate a consistent color hex code based on the page name"""
    hash_value = hash(name)
    hue = abs(hash_value) % 360
    saturation = 70
    lightness = 50

    import colorsys
    r, g, b = colorsys.hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

from .microservice import Microservice
from .macroservice import Macroservice

