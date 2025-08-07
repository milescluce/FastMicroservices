from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List, Optional, Any

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastj2 import FastJ2
from loguru import logger as log
from starlette.responses import Response
from toomanyconfigs import CWD
from toomanythreads import ThreadedServer

default_index = """
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


class Macroservice(ThreadedServer, FastJ2, CWD):
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs.get(kwarg))
        self.microservices = {}
        self.cached_pages = []
        CWD.__init__(
            self,
            {
                "templates": {
                    "index_page": {
                        "index.html": default_index
                    },
                    "static_pages": {
                    },
                }
            }
        )
        self.templates: Path = self.templates._path
        self.index: Path = self.templates / "index_page" / "index.html"
        self.static_pages: Path = self.templates / "static_pages"
        FastJ2.__init__(
            self,
            cwd=self.cwd
        )
        ThreadedServer.__init__(
            self
        )

        @self.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return self.safe_render(
                f"index_page/{self.index.name}",
                request=request,
                pages=self.pages
            )

        @self.get("/page/{page_name}/{path:path}")
        async def get_page(page_name: str, path, request: Request):
            """Serve a specific static page by filename."""
            pages = self.pages
            log.debug(f"{self}: Looking for page_name: '{page_name}'")
            log.debug(f"{self}: Available pages: {[(p.name, p.type) for p in pages]}")
            page = next((p for p in self.pages if p.name == page_name), None)
            if not page: raise HTTPException(status_code=404, detail="Page not found")
            log.success(f"{self}: Found page: {page}")

            if page.type == "static":
                template_name = page.name
                return self.safe_render(
                    template_name,
                    request=request,
                    page=page
                )

            if page.type == "microservice":
                obj = page.obj
                if not getattr(obj, "forward", None):
                    log.error(
                        "Microservices need a 'forward' method to work properly."
                        "\nSee TooManyThreads.ThreadedServer.forward for reference."
                        "\nAlternatively, directly inherit your microservice from TooManyThreads.ThreadedServer."
                        "\nSee documentation: https://pypi.org/project/toomanythreads/"
                    )
                    raise AttributeError("Microservices need a 'forward' method")
                return await obj.forward(
                    path=f"/{path}",
                    request=request
                )

    def __repr__(self):
        return "[Macroservice]"

    def __getitem__(self, name: str):
        if name in self.microservices:
            return self.microservices[name]
        raise AttributeError(f"'{type(self).__name__}' has no microservice named '{name}'")

    def __setitem__(self, name: str, value: Any) -> None:
        if not name in self.microservices:
            self.microservices[name] = value
        return self[name]

    @property
    def pages(self) -> List[PageConfig]:
        discovered: List[PageConfig] = []
        new_pages = len(list(self.static_pages.glob("*.html"))) + len(self.microservices)
        if new_pages == 0:
            log.warning(f"{self}: No pages to load!")
        elif new_pages == len(self.cached_pages):
            log.debug(f"{self}: No new pages found! Using cache.")
        else:
            if self.verbose: log.debug(f"{self}: Discovering pages in {self.static_pages}...")
            for page_path in self.static_pages.glob("*.html"):
                title = extract_title_from_html(page_path) or page_path.stem.replace('_', ' ').title()
                cfg = PageConfig(
                    name=page_path.name,
                    title=title,
                    type="static",
                    cwd=self.static_pages,
                    obj=None,
                    color=generate_color_from_name(page_path.name),
                    icon="📄",
                    auto_discovered=True
                )
                discovered.append(cfg)
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")

            if self.verbose: log.debug(f"{self}: Discovering microservices in {self.microservices}...")
            for serv in self.microservices:
                inst = self.microservices.get(serv)
                title: str = serv or getattr(inst, 'title', None)
                cfg = PageConfig(
                    name=title.lower(),
                    title=title,
                    type="microservice",
                    cwd=None,
                    obj=inst,
                    color=generate_color_from_name(title),
                    icon="📄",
                    auto_discovered=True
                )
                discovered.append(cfg)
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")

        self.cached_pages = discovered
        return self.cached_pages