import asyncio
import time
from pathlib import Path
from typing import Any

import httpx
import starlette.responses
from loguru import logger as log
from starlette.requests import Request
from toomanyports import PortManager

from .publicapp import PublicApp
from fastcloudflare import Cloudflare


class Gateway(Cloudflare):
    def __init__(
            self,
            host: str = None,
            port: int = None,
            cfg: Path = None,
            app: Any = None,
            verbose: bool = True,
    ) -> None:
        self.host = "localhost" if host is None else host
        self.port = PortManager.random_port() if port is None else port
        if cfg:
            Cloudflare.__init__(self, toml=cfg)
        else:
            Cloudflare.__init__(self)
        self.cloudflare_cfg.service_url = self.url

        if app:
            self.app = app
        else:
            self.app = PublicApp()

        self.verbose = verbose
        if self.verbose: log.success(f"[{self}]: Initialized successfully!\n  - host={self.host}\n  - port={self.port}")

        # Create persistent client for connection reuse
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0, read=30.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20, keepalive_expiry=30.0),
            http2=False,
            headers={"Connection": "keep-alive"}
        )

        @self.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        async def forward(path: str, request: Request):
            url = f"{self.app.url}/{path}"

            try:
                # Use persistent client with keep-alive
                resp = await self.client.request(
                    request.method,
                    url,
                    headers={k: v for k, v in request.headers.items() if k.lower() not in {'host', 'content-length'}},
                    content=await request.body(),
                    params=request.query_params,
                    follow_redirects=True
                )

                # Clean headers that cause issues
                headers = {}
                for k, v in resp.headers.items():
                    if k.lower() not in {'content-encoding', 'transfer-encoding', 'content-length', 'connection'}:
                        headers[k] = v

                # Force connection keep-alive in response
                headers['Connection'] = 'keep-alive'
                headers['Keep-Alive'] = 'timeout=60, max=1000'

                return starlette.responses.Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=headers
                )

            except Exception as e:
                if self.verbose:
                    log.error(f"Gateway forward error: {e}")
                return starlette.responses.Response(
                    content=f"Gateway Error: {str(e)}",
                    status_code=502,
                    headers={"content-type": "text/plain"}
                )

    async def launch(self):
        loc = self.thread
        glo = await self.cloudflare_thread
        loc.start()
        glo.start()


async def debug():
    g = Gateway()
    await g.launch()


if __name__ == "__main__":
    asyncio.run(debug())
    time.sleep(1000)
