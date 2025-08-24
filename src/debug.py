import time

from loguru import logger as log
from starlette.requests import Request
from starlette.responses import HTMLResponse
from toomanysessions import SessionedServer
from toomanythreads import ThreadedServer

from fastmicroservices import Macroservice
from fastmicroservices import Microservice


class MyServer(Macroservice, ThreadedServer):
    def __init__(self):
        print(f"MyServer: Before ThreadedServer.__init__")
        ThreadedServer.__init__(self)
        print(f"MyServer: After ThreadedServer.__init__ - port: {self.port}")
        log.warning(f"MyServer URL: {self.url}")
        Macroservice.__init__(self)


class MyMicroservice(Microservice, ThreadedServer):
    def __init__(self, macroservice: Macroservice):
        print(f"MyMicroservice: Before ThreadedServer.__init__")
        print(f"MyMicroservice: macroservice.port = {macroservice.port}")

        ThreadedServer.__init__(self)
        print(f"MyMicroservice: After ThreadedServer.__init__ - port: {self.port}")
        print(f"MyMicroservice: macroservice.port = {macroservice.port}")

        log.warning(f"MyMicroservice URL: {self.url}")
        Microservice.__init__(self, macroservice)
        print(f"MyMicroservice: After Microservice.__init__ - port: {self.port}")

        @self.get("/")
        def foobar(request: Request):
            html = """
           <!DOCTYPE html>
           <html lang="en">
           <head>
               <meta charset="UTF-8">
               <meta name="viewport" content="width=device-width, initial-scale=1.0">
               <title>My Microservice</title>
               <style>
                   * { margin: 0; padding: 0; box-sizing: border-box; }
                   body { 
                       font-family: Arial, sans-serif; 
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       min-height: 100vh; 
                       padding: 20px;
                   }
                   .container { max-width: 800px; margin: 0 auto; }
                   .card { 
                       background: white; 
                       border-radius: 10px; 
                       padding: 20px; 
                       margin: 20px 0; 
                       box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                   }
                   h1 { color: #333; margin-bottom: 20px; }
                   h2 { color: #667eea; margin: 20px 0 10px 0; }
                   .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
                   .stat { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
                   .stat-number { font-size: 24px; font-weight: bold; color: #764ba2; }
                   .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
                   .chart { height: 200px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666; }
                   .nav { background: #333; border-radius: 8px; padding: 10px; margin-bottom: 20px; }
                   .nav a { color: white; text-decoration: none; padding: 8px 15px; margin: 0 5px; border-radius: 4px; display: inline-block; }
                   .nav a:hover { background: #667eea; }
                   .table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                   .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                   .table th { background: #f8f9fa; color: #333; }
                   .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
                   .status.active { background: #d4edda; color: #155724; }
                   .status.pending { background: #fff3cd; color: #856404; }
                   .status.inactive { background: #f8d7da; color: #721c24; }
               </style>
           </head>
           <body>
               <div class="container">
                   <div class="card">
                       <h1>🚀 MyMicroservice Dashboard</h1>
                       <p>This is a complex microservice running independently with its own styling and functionality.</p>

                       <nav class="nav">
                           <a href="#dashboard">Dashboard</a>
                           <a href="#analytics">Analytics</a>
                           <a href="#settings">Settings</a>
                           <a href="#users">Users</a>
                       </nav>
                   </div>

                   <div class="card">
                       <h2>📊 Quick Stats</h2>
                       <div class="stats">
                           <div class="stat">
                               <div class="stat-number">1,247</div>
                               <div class="stat-label">Total Users</div>
                           </div>
                           <div class="stat">
                               <div class="stat-number">89.3%</div>
                               <div class="stat-label">Uptime</div>
                           </div>
                           <div class="stat">
                               <div class="stat-number">$12.4K</div>
                               <div class="stat-label">Revenue</div>
                           </div>
                           <div class="stat">
                               <div class="stat-number">23</div>
                               <div class="stat-label">Active Tasks</div>
                           </div>
                       </div>
                   </div>

                   <div class="card">
                       <h2>📈 Performance Chart</h2>
                       <div class="chart">
                           [Chart would render here - API requests over time]
                       </div>
                   </div>

                   <div class="card">
                       <h2>👥 Recent Users</h2>
                       <table class="table">
                           <thead>
                               <tr>
                                   <th>Name</th>
                                   <th>Email</th>
                                   <th>Status</th>
                                   <th>Last Seen</th>
                               </tr>
                           </thead>
                           <tbody>
                               <tr>
                                   <td>John Doe</td>
                                   <td>john@example.com</td>
                                   <td><span class="status active">Active</span></td>
                                   <td>2 minutes ago</td>
                               </tr>
                               <tr>
                                   <td>Jane Smith</td>
                                   <td>jane@example.com</td>
                                   <td><span class="status pending">Pending</span></td>
                                   <td>1 hour ago</td>
                               </tr>
                               <tr>
                                   <td>Bob Wilson</td>
                                   <td>bob@example.com</td>
                                   <td><span class="status inactive">Inactive</span></td>
                                   <td>3 days ago</td>
                               </tr>
                           </tbody>
                       </table>
                   </div>
               </div>
           </body>
           </html>
           """
            return HTMLResponse(html)


if __name__ == "__main__":
    mac = MyServer()
    print(f"mac id: {id(mac)}")

    mic = MyMicroservice(mac)
    print(f"mic id: {id(mic)}")
    print(f"Are mac and mic the same? {mac is mic}")

    mac.thread.start()
    mic.thread.start()
    log.debug(mac.app_metadata)
    log.debug(mic.app_metadata)
    time.sleep(100)
