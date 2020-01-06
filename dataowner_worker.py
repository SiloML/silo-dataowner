import syft as sy
from syft.workers.websocket_client import WebsocketClientWorker
from syft.workers.websocket_server import WebsocketServerWorker
import torch
import asyncio
import binascii
import websocket

# hook = sy.TorchHook(torch)

TIMEOUT_INTERVAL = 999_999

class DataownerWorker(WebsocketClientWorker):
    def start(self):
        print("listening")
        while True:
            message = self.ws.recv()
            print(message)
            print("GOT A MESSAGE")
            message = binascii.unhexlify(message[2:-1])
            print(message)

            resp = self._recv_msg(message)
            resp = str(binascii.hexlify(resp))
            print(resp)

            self.ws.send(resp)

    def _recv_msg(self, message: bin) -> bin:
        return self.recv_msg(message)

    @property
    def url(self):
        return f"wss://{self.host}:{self.port}/share" if self.secure else f"ws://{self.host}:{self.port}/share"

    def connect(self):
        args = {"max_size": None, "timeout": TIMEOUT_INTERVAL, "url": self.url, "cookie": "320984", "id": self.id}

        if self.secure:
            args["sslopt"] = {"cert_reqs": ssl.CERT_NONE}

        self.ws = websocket.create_connection(**args)

    def list_objects_remote(self, *args):
        return str(self._objects)

    def objects_count_remote(self, *args):
        return len(self._objects)

    # def _send_msg





