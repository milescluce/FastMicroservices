import time

from toomanythreads import ThreadedServer

from fastmicroservices import Macroservice
from fastmicroservices import Microservice


class Dummy(ThreadedServer, Microservice):
    def __init__(self, macroservice: Macroservice):
        ThreadedServer.__init__(self)
        Microservice.__init__(self, macroservice)

        @self.get("/")
        def foobar():
            return "foobar"


if __name__ == "__main__":
    m = Macroservice()
    serv = Dummy(m)
    m.thread.start()
    time.sleep(100)
