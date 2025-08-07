from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List, Optional, Any

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastj2 import FastJ2
from loguru import logger as log
from toomanyconfigs import CWD
from toomanythreads import ThreadedServer


@dataclass
class PageConfig:
    name: str
    title: str
    type: str
    cwd: Path
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
    microservices = {}
    cached_pages = []

    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs.get(kwarg))

        CWD.__init__(
            self,
            {
                "templates": {
                    "index_page": {
                        "index.html": None
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
        _ = self.pages

        @self.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return self.safe_render(
                f"index_page/{self.index.name}",
                request=request,
                pages=self.pages
            )

        @self.get("/page/{page_name}")
        async def get_page(page_name: str, request: Request):
            """Serve a specific static page by filename."""
            page = next((p for p in self.pages if p.name == page_name), None)
            if not page: raise HTTPException(status_code=404, detail="Page not found")

            if page.type == "static":
                template_name = page.name
                return self.safe_render(
                    template_name,
                    request=request,
                    page=page
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
        new_pages = len(enumerate(self.static_pages.glob("*.html"))) + len(self.microservices)
        if new_pages == 0:
            log.warning(f"{self}: No pages to load!")
        elif (new_pages == enumerate(self.cached_pages)):
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
                    color=generate_color_from_name(page_path.name),
                    icon="📄",
                    auto_discovered=True
                )
                discovered.append(cfg)
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")

            if self.verbose: log.debug(f"{self}: Discovering microservices in {self.microservices}...")
            for serv in self.microservices:
                title = serv or serv.title
                cfg = PageConfig(
                    name=title,
                    title=title,
                    type="microservices",
                    cwd=None,
                    color=generate_color_from_name(title),
                    icon="📄",
                    auto_discovered=True
                )
                discovered.append(cfg)
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")

        self.cached_pages = discovered
        return self.cached_pages
