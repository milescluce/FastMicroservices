from typing import Any

from singleton_decorator import singleton


@singleton
class Macroservice:
    microservices = {}

    def __getattr__(self, name: str):
        if name in self.microservices:
            return self.microservices[name].api
        raise AttributeError(f"'{type(self).__name__}' has no microservice named '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        from .microservice import Microservice
        if name.startswith('_') or name in ['__annotations__']:
            super().__setattr__(name, value)
        else:
            self[name]: Microservice


Macroservice = Macroservice()
