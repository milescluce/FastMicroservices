from pathlib import Path
from typing import List, Any

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastj2 import FastJ2
from loguru import logger as log
# from p2d2 import Database
from toomanyconfigs import CWD
from toomanysessions import SessionedServer
from toomanythreads import ThreadedServer

from . import DEFAULT_INDEX, extract_title_from_html, PageConfig, generate_color_from_name, DEBUG, check_type, are_both_sessioned_server


class Macroservice(FastJ2, CWD):
    def __init__(self, verbose = DEBUG, **kwargs):
        check_type(self)
        self.verbose = verbose
        # self.database = database
        # self.mount("/database", database._api) #type: ignore
        # if self.database:
        #     if not isinstance(database, Database): raise RuntimeError(
        #         "Macroservices are only compatible with P2D2.Database!\nSee https://pypi.org/project/p2d2/")
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs.get(kwarg))
        self.microservices = {}
        self.cached_pages = []
        CWD.__init__(
            self,
            {
                "templates": {
                    "index_page": {
                        "index.html": DEFAULT_INDEX
                    },
                    "static_pages": {
                    },
                    "microservice_iframe.html": """
<div class="page-content" style="height: calc(100vh - 60px); padding: 0; margin: 0;">
    <iframe src="{{ url }}"
            width="100%"
            height="100%"
            frameborder="0"
            class="microservice-frame"
            style="display: block;">
    </iframe>
</div>
"""
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

        @self.get("/", response_class=HTMLResponse)  #type: ignore
        async def home(request: Request):
            return self.safe_render(
                f"index_page/{self.index.name}",
                request=request,
                pages=self.pages
            )

        @self.get("/page/{page_name}/{path:path}")  #type: ignore
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
                obj: ThreadedServer = page.obj
                iframe_url = obj.url  # This is the microservice's URL (e.g., http://localhost:8001)

                return self.safe_render(
                    "microservice_iframe.html",
                    url=iframe_url,
                )

    def __repr__(self):
        return "[Macroservice]"

    def __getitem__(self, name: str):
        if name in self.microservices:
            return self.microservices[name]
        raise AttributeError(f"'{type(self).__name__}' has no microservice named '{name}'")

    def __setitem__(self, name: str, value: Any) -> None:
        if name not in self.microservices:
            self.microservices[name] = value
            if are_both_sessioned_server(self, value):
                mac: SessionedServer = self
                mic: SessionedServer = value
                setattr(mic, "sessions", mac.sessions)
                if id(mic.sessions) != id(mac.sessions): raise AttributeError("Failed attempted session sync")
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
            if self.verbose: log.debug(f"{self}: Discovering pages in {self.static_pages}...") #type: ignore
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
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")  #type: ignore

            if self.verbose: log.debug(f"{self}: Discovering microservices in {self.microservices}...")  #type: ignore
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
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")  #type: ignore

        self.cached_pages = discovered
        return self.cached_pages
