import time
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from loguru import logger as log
from singleton_decorator import singleton
from toomanythreads import ThreadedServer
from fastj2 import FastTemplates


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


@singleton
class PublicApp(ThreadedServer):
    @cached_property
    def cwd(self) -> SimpleNamespace:
        ns = SimpleNamespace(
            path=Path.cwd(),
            index=Path.cwd() / "index",
            index_file=Path.cwd() / "index" / "index.html",
            static_pages=Path.cwd() / "static_pages"
        )
        for name, p in vars(ns).items():
            if p.suffix:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch(exist_ok=True)
                if self.verbose:
                    log.debug(f"[{self}]: Ensured file {p}")
            else:
                p.mkdir(parents=True, exist_ok=True)
                if self.verbose:
                    log.debug(f"[{self}]: Ensured directory {p}")
        return ns

    @cached_property
    def base_url(self) -> str:
        url = f"http://{self.host}:{self.port}"
        if self.verbose: log.debug(f"[{self}]: base_url set to {url}")
        return url

    @cached_property
    def api(self) -> 'Macroservice':
        if self.verbose: log.debug(f"[{self}]: Initializing Macroservice API")
        return Macroservice()

    @cached_property
    def pages(self) -> List[PageConfig]:
        if self.verbose: log.debug(f"[{self}]: Discovering pages in {self.cwd.static_pages}")
        discovered: List[PageConfig] = []
        for page_path in self.cwd.static_pages.glob("*.html"):
            title = extract_title_from_html(page_path) or page_path.stem.replace('_', ' ').title()
            cfg = PageConfig(
                name=page_path.name,
                title=title,
                type="static",
                cwd=self.cwd.static_pages,
                color=generate_color_from_name(page_path.name),
                icon="📄",
                auto_discovered=True
            )
            discovered.append(cfg)
            if self.verbose: log.debug(f"[{self}]: Discovered page {cfg.name} titled '{cfg.title}'")
        return discovered

    @cached_property
    def index(self) -> FastTemplates:
        if self.verbose: log.debug(f"[{self}]: Initializing FastTemplates at {self.cwd.index}")
        return FastTemplates(self.cwd.index)

    @cached_property
    def static_env(self):
        return FastTemplates(self.cwd.static_pages)

    def __init__(self, host="localhost", port=None, verbose=True):
        super().__init__(host=host, port=port, verbose=verbose)
        app = self
        _ = self.pages

        @self.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            if self.verbose:
                log.debug(f"[{self}]: GET / home endpoint")
            return self.index.TemplateResponse(
                f"{self.cwd.index_file.name}",
                {"request": request, "pages": self.pages}
            )

        @self.get("/page/{page_name}")
        async def get_page(page_name: str, request: Request) -> HTMLResponse:
            """Serve a specific static page by filename."""
            if self.verbose:
                log.debug(f"[{self}]: Received GET /page/{page_name}")
            page = next((p for p in self.pages if p.name == page_name), None)
            if not page:
                if self.verbose:
                    log.warning(f"[{self}]: Page not found: {page_name}")
                raise HTTPException(status_code=404, detail="Page not found")

            if page.type == "static":
                template_name = page.name
                template_path = self.cwd.static_pages / template_name
                if self.verbose:
                    log.debug(f"[{self}]: Serving static template {template_name} from {template_path}")
                if not template_path.exists():
                    if self.verbose:
                        log.error(f"[{self}]: Template file missing: {template_path}")
                    raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
                return self.static_env.TemplateResponse(
                    template_name,
                    {"request": request, "page": page}
                )

        self.thread.start()


if __name__ == "__main__":
    # asyncio.run(debug())
    # PublicApp().thread.start()
    PublicApp()
    time.sleep(100)
