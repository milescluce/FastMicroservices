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
    <title>PhazeDash</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        :root {
            --sidebar-width: 250px;
            --header-height: 80px;
            --dark-blue: #1e3a8a;
            --darker-blue: #1e40af;
        }

        body { margin: 0; padding: 0; }

        .layout {
            display: grid;
            grid-template-areas:
                "sidebar header"
                "sidebar main";
            grid-template-columns: var(--sidebar-width) 1fr;
            grid-template-rows: var(--header-height) 1fr;
            min-height: 100vh;
        }

        header.main-header {
            grid-area: header;
            background: var(--dark-blue);
            color: white;
            display: flex;
            align-items: center;
            padding: 0 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        header.main-header h1 {
            margin: 0;
            color: white;
        }

        .sidebar {
            grid-area: sidebar;
            background: var(--dark-blue);
            padding: 1rem;
            box-shadow: 2px 0 4px rgba(0,0,0,0.1);
        }

        .sidebar ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
        }

        .sidebar li {
            margin-bottom: 0.5rem;
            width: 100%;
        }

        .sidebar a {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.2s ease;
            color: rgba(255, 255, 255, 0.8);
            border-left: 3px solid transparent;
            width: 100%;
            box-sizing: border-box;
        }

        .sidebar a:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            transform: translateX(4px);
        }

        .sidebar .page-icon {
            font-size: 1.2em;
            width: 24px;
            text-align: center;
        }

        .sidebar .page-title {
            font-weight: 500;
        }

        .content {
            grid-area: main;
            padding: 2rem;
            overflow-y: auto;
        }

        /* Color accents for sidebar links */
        {% for page in pages %}
        .sidebar a[data-page="{{ page.name }}"] {
            {% if page.color %}border-left-color: {{ page.color }};{% endif %}
        }
        .sidebar a[data-page="{{ page.name }}"]:hover {
            {% if page.color %}
            background: {{ page.color }}25;
            border-left-color: {{ page.color }};
            {% endif %}
        }
        {% endfor %}

        @media (max-width: 768px) {
            .layout {
                grid-template-areas:
                    "header"
                    "sidebar"
                    "main";
                grid-template-columns: 1fr;
                grid-template-rows: var(--header-height) auto 1fr;
            }

            .sidebar {
                padding: 0.5rem;
            }

            .sidebar ul {
                display: flex;
                gap: 0.5rem;
                overflow-x: auto;
                padding: 0.5rem 0;
            }

            .sidebar li {
                margin-bottom: 0;
                white-space: nowrap;
            }
        }
    </style>
</head>
<body>
    <div class="layout">
        <header class="main-header">
            <h1>My Index</h1>
        </header>

        <nav class="sidebar">
            <ul>
                {% for page in pages %}
                <li>
                    <a href="#"
                       hx-get="/page/{{ page.name }}"
                       hx-target="#main-content"
                       data-page="{{ page.name }}">
                        {% if page.icon %}
                        <span class="page-icon">{{ page.icon }}</span>
                        {% endif %}
                        <span class="page-title">{{ page.title }}</span>
                    </a>
                </li>
                {% endfor %}
            </ul>
        </nav>

        <main class="content">
            <div id="main-content">
                <h2>Welcome</h2>
                <p>Select a service from the sidebar.</p>
            </div>
        </main>
    </div>
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

