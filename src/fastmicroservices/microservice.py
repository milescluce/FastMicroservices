from pyzurecli import PyzureServer
from toomanysessions import SessionedServer
from toomanythreads import ThreadedServer

from .macroservice import Macroservice


# @dataclass
# class Response:
#     status: int
#     method: str
#     headers: dict
#     body: Any

class Microservice:
    def __init__(self, macroservice: Macroservice):
        self.macro = macroservice
        self.macro[self.__class__.__name__] = self
        accepted_types = [ThreadedServer, PyzureServer, SessionedServer]
        type_matches = 0
        for typ in accepted_types:
            if not isinstance(self, typ): continue
            type_matches = type_matches + 1
        if type_matches == 0: raise TypeError(f"Inheriting class is not one of the following: {accepted_types}")
        # if not self.routes: raise AttributeError("Microservices must have a routes attribute!")
        super().__init__()

    # @property
    # def api(self):
    #     ns = SimpleNamespace()
    #     for route in self.routes:
    #         if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__name__'):
    #             method_name = route.endpoint.__name__  # Use function name!
    #             setattr(ns, method_name, self._make_method(route))
    #     return ns
    #
    # def _make_method(self, route):
    #     """Create a simple async method for each route"""
    #
    #     async def api_call(*args, **kwargs):
    #         if not self.thread.is_alive(): raise RuntimeError(f"{self.url} isn't running!")
    #         method = list(route.methods)[0] if route.methods else 'GET'
    #         path = route.path
    #
    #         # Simple path parameter substitution
    #         for i, arg in enumerate(args):
    #             path = path.replace(f'{{{list(route.path_regex.groupindex.keys())[i]}}}', str(arg), 1)
    #
    #         async with aiohttp.ClientSession() as session:
    #             async with session.request(method, f"{self.url}{path}", **kwargs) as res:
    #                 try:
    #                     content_type = res.headers.get("Content-Type", "")
    #                     if "json" in content_type:
    #                         content = await res.json()
    #                     else:
    #                         content = await res.text()
    #                 except Exception as e:
    #                     content = await res.text()  # always fallback
    #                     log.warning(f"{self}: Bad response decode → {e} | Fallback body: {content}")
    #
    #                 resp = Response(
    #                     status=res.status,
    #                     method=method,
    #                     headers=dict(res.headers),
    #                     body=content,
    #                 )
    #                 log.debug(
    #                     f"{self}:\n  - req={res.url} - args={args}\n  - kwargs={kwargs}\n  - resp={resp}"
    #                 )
    #                 return resp
    #
    #     return api_call
