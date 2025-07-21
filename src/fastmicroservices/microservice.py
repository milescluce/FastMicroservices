import asyncio
import time
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import aiohttp
from loguru import logger as log
from toomanythreads import ThreadedServer
from .macroservice import Macroservice

class Microservice(ThreadedServer):
    _last_route_count = None
    _api_client = None

    def __init__(self, host="localhost", port=None, alias: str = None, verbose=True):
        super().__init__(host=host, port=port, verbose=verbose)
        _ = self.base_url
        self.name = str(port)
        if alias: self.name = alias
        Macroservice.microservices[self.name] = self

    def __repr__(self):
        return f"[Microservices.{self.name}]"

    @cached_property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

    @property
    def api(self):
        """Smart API client - only regenerates when routes change"""
        current_route_count = len(self.routes)

        if (self._api_client is None or
                current_route_count != self._last_route_count):

            if self.verbose: log.debug(
                f"Regenerating API client ({self._last_route_count} -> {current_route_count} routes)")

            self._api_client = APIClient(self)
            self._last_route_count = current_route_count

        return self._api_client

@dataclass
class Response:
    status: int
    method: str
    headers: dict
    body: Any


class APIClient:
    def __init__(self, app: Microservice):
        self.app = app

        for route in app.routes:
            if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__name__'):
                method_name = route.endpoint.__name__  # Use function name!
                setattr(self, method_name, self._make_method(route))

    def _make_method(self, route):
        """Create a simple async method for each route"""

        async def api_call(*args, **kwargs):
            if not self.app.thread.is_alive(): raise RuntimeError(f"{self.app.base_url} isn't running!")
            method = list(route.methods)[0] if route.methods else 'GET'
            path = route.path

            # Simple path parameter substitution
            for i, arg in enumerate(args):
                path = path.replace(f'{{{list(route.path_regex.groupindex.keys())[i]}}}', str(arg), 1)

            async with aiohttp.ClientSession() as session:
                async with session.request(method, f"{self.app.base_url}{path}", **kwargs) as res:
                    try:
                        content_type = res.headers.get("Content-Type", "")
                        if "json" in content_type:
                            content = await res.json()
                        else:
                            content = await res.text()
                    except Exception as e:
                        content = await res.text()  # always fallback
                        log.warning(f"{self}: Bad response decode → {e} | Fallback body: {content}")

                    resp = Response(
                        status=res.status,
                        method=method,
                        headers=dict(res.headers),
                        body=content,
                    )
                    if self.app.verbose: log.debug(
                        f"{self.app}:\n  - req={res.url} - args={args}\n  - kwargs={kwargs}\n  - resp={resp}")
                    return resp

        return api_call


async def debug():
    server = Microservice(alias="foobar")
    server.cache = {}
    server.thread.start()

    @server.get("/users/{user_id}")
    async def get_user(user_id: str):
        return {"user_id": user_id, "name": "John"}

    @server.post("/cache/{key}")
    async def set_cache(key: str, value: str):
        server.cache[key] = value
        return {"status": "stored"}

    @server.get("/cache/{key}")
    async def get_cache(key: str):
        return {"value": server.cache.get(key, "not found")}

    # Test initial API methods (using function names)
    user_data = await server.api.get_user("123")
    cache_value = await server.api.get_cache("mykey")
    set_result = await server.api.set_cache("mykey", json={"value": "myvalue"})
    # Verify cache was set
    updated_cache = await server.api.get_cache("mykey")

    # Add new route
    @server.get("/health")
    async def health_check():
        return {"status": "healthy", "cache_size": len(server.cache)}

    @server.post("/reset")
    async def reset_cache():
        server.cache.clear()
        return {"status": "cache cleared"}

    # Test new methods
    health = await server.api.health_check()
    reset = await server.api.reset_cache()
    # Verify cache was cleared
    final_cache = await server.api.get_cache("mykey")
    reset = await Macroservice.foobar.reset_cache()

    time.sleep(100)


if __name__ == "__main__":
    asyncio.run(debug())
