import time

from fastapi import FastAPI
from toomanythreads import ThreadedServer

from fastmicroservices import Macroservice
from fastmicroservices import Microservice
from loguru import logger as log


class Dummy(ThreadedServer, Microservice):
    def __init__(self, macroservice: Macroservice):
        ThreadedServer.__init__(self)
        Microservice.__init__(self, macroservice)

if __name__ == "__main__":
    # asyncio.run(debug())
    # PublicApp().thread.start()
    m = Macroservice()
    serv = Dummy(m)
    log.debug(serv.api.openapi)
    time.sleep(100)