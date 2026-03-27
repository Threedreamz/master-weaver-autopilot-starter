from network_lib.client.auto_connect_h import auto_connect_h

import asyncio

class auto_connect:
    def autoFindServer(self):
        #connect, get port and get/check hash
        res =  asyncio.run(auto_connect_h().run_auto_connect())

        #establish connection to server tcp socket with ip and port

        # ('192.168.2.34', ('1797', 'null'))
        print(f"final res_: {res}")
        return res

    def getServer(self):
        getServer = auto_connect_h().getServer()
        return getServer
    
    def connect_client(self):
        self.res = self.autoFindServer()
        #"192.168.2.31" 
        if self.res == None:
            raise Exception("Kein Server gefunden.")
        return (self.res[0], self.res[2])



