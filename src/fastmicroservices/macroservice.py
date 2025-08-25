import urllib
from pathlib import Path
from typing import List, Any

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastj2 import FastJ2
from loguru import logger as log
from starlette.responses import Response
# from p2d2 import Database
from toomanyconfigs import CWD
from toomanysessions import SessionedServer
from toomanythreads import ThreadedServer

from . import extract_title_from_html, PageConfig, generate_color_from_name, DEBUG, check_type, \
    are_both_sessioned_server
from .templates import microservice_iframe, index, fastmicroservices_css


class Macroservice(FastJ2, CWD):
    def __init__(self, verbose=DEBUG, **kwargs):
        check_type(self)
        self.verbose = verbose
        # self.database = database
        # self.mount("/database", database._api) #type: ignore
        # if self.database:
        #     if not isinstance(database, Database): raise RuntimeError(
        #         "Macroservices are only compatible with P2D2.Database!\nSee https://pypi.org/project/p2d2/")
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs.get(kwarg))
        FastJ2.__init__(
            self,
            {
                "templates": {
                    "css": {
                        "9-fastmicroservices": {
                            "fastmicroservices.css": fastmicroservices_css
                        }
                    },
                    "html": {
                        "content": {
                            "microservice_iframe.html": microservice_iframe,
                            "index.html": index,
                            "static_pages": {

                            },
                        }
                    },
                }
            },
            cwd=Path.cwd()
        )
        self.microservices = {}
        self.cached_pages = []
        self.templates: Path = self.templates._path
        self.index: Path = self.templates / "html" / "content" / "index.html"
        self.static_pages: Path = self.templates / "html" / "content" / "static_pages"

        @self.get("/", response_class=HTMLResponse)  # type: ignore
        async def home(request: Request):
            return self.safe_render(
                f"{self.index.name}",
                request=request,
                pages=self.pages
            )

        @self.get("/microservice/{page_name}/{path:path}")
        @self.post("/microservice/{page_name}/{path:path}")
        async def proxy_microservice(request: Request, page_name: str, path: str):
            # Get the microservice URL from your registry
            pages = self.pages
            log.debug(f"{self}: Looking for page_name: '{page_name}'")
            log.debug(f"{self}: Available pages: {[(p.name, p.type) for p in pages]}")
            microservice = next((p for p in self.pages if p.name == page_name), None)
            if not microservice: raise HTTPException(status_code=404, detail=f"Microservice '{page_name}' not found")
            target_url = f"{microservice.obj.url}/{path}"

            # Forward all query params
            if request.query_params:
                target_url += f"?{request.query_params}"

            import httpx
            async with httpx.AsyncClient() as client:
                # Forward the request with all headers, cookies, and body
                if request.method == "GET":
                    response = await client.get(
                        target_url,
                        cookies=request.cookies,
                        headers=dict(request.headers)
                    )
                else:  # POST, PUT, etc.
                    body = await request.body()
                    response = await client.request(
                        request.method,
                        target_url,
                        content=body,
                        cookies=request.cookies,
                        headers=dict(request.headers)
                    )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        @self.get("/page/{page_name}")  # type: ignore
        async def get_page(page_name: str, request: Request):
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
                    f"static_pages/{template_name}",
                    request=request,
                    page=page
                )

            if page.type == "microservice":
                cookies = request.cookies.copy()
                obj: ThreadedServer = page.obj
                query_string = urllib.parse.urlencode(cookies, doseq=True)
                iframe_url = f"/microservice/{page_name}/?{query_string}"
                log.debug(f"{self}: Requesting iframe from {iframe_url}")
                return self.safe_render(
                    "microservice_iframe.html",
                    url=iframe_url
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
            if self.verbose: log.debug(f"{self}: Discovering pages in {self.static_pages}...")  # type: ignore
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
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")  # type: ignore

            if self.verbose: log.debug(f"{self}: Discovering microservices in {self.microservices}...")  # type: ignore
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
                if self.verbose: log.debug(f"{self}: Discovered page {cfg.name} titled '{cfg.title}'")  # type: ignore

        self.cached_pages = discovered
        return self.cached_pages
