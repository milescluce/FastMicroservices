import time

from loguru import logger as log
from p2d2 import Database
from toomanysessions import SessionedServer

from fastmicroservices import Macroservice
from fastmicroservices import Microservice


class MyTable:
    foo: str


class MyDatabase(Database):
    my_table: MyTable


class MyServer(SessionedServer, Macroservice):
    def __init__(self):
        SessionedServer.__init__(self, authentication_model=None)
        Macroservice.__init__(self, database=MyDatabase())


class MyMicroservice(SessionedServer, Microservice):
    def __init__(self, macroservice: Macroservice):
        SessionedServer.__init__(self, authentication_model=None)
        Microservice.__init__(self, macroservice)

        @self.get("/")
        def foobar():
            return "foobar"


if __name__ == "__main__":
    mac = MyServer()
    mic = MyMicroservice(mac)
    mac.thread.start()
    log.debug(mac.app_metadata)
    log.debug(mic.app_metadata)
    time.sleep(100)
