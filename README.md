## Install

```bash
pip install fastmicroservices
```

## Usage

```python
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
```

## How it works

The core routing engine uses `/page/{page_name}/{path:path}`:

- **Automatic Directory Construction**: The backend uses TooManyConfigs and FastJ2 to automatically provision a templates folder and render from it.
- **Service Discovery**: Macroservice finds your service by `page_name`, which is the lowercase class' name. In the above instance, it would be http://localhost:{port}/page/dummy
- **Internal Routing**: Your service handles its own routes via the `forward()` method. You can code your own forwarding method, but ThreadedServer already provides this. See https://pypi.org/project/toomanythreads/

Example: `/page/dummy/api/users` → finds "dummy" service → calls `dummy.forward("/api/users")`
Static HTML files in `templates/static_pages/` work the same way but just render templates.

Licensed under MIT.