import syft as sy
from syft.workers.websocket_client import WebsocketClientWorker
from syft.workers.websocket_server import WebsocketServerWorker
import torch
import asyncio
import binascii
import websocket
import websockets
from typing import Union, List, Tuple
from syft.generic.pointers.pointer_tensor import PointerTensor
from syft.generic.object import AbstractObject
from syft.generic.frameworks.types import FrameworkTensor
from syft.generic.tensor import AbstractTensor
from syft.workers.base import BaseWorker
from syft.federated.federated_client import FederatedClient
import time
import logging

# hook = sy.TorchHook(torch)

TIMEOUT_INTERVAL = 999_999

class DataownerWorker(WebsocketServerWorker):
    def __init__(
        self,
        hook,
        host: str,
        port: int,
        secure: bool = False,
        id: Union[int, str] = 0,
        log_msgs: bool = False,
        verbose: bool = False,
        data: List[Union[torch.Tensor, AbstractTensor]] = None,
        loop=None,
        cert_path: str = None,
        key_path: str = None,
        set_local_worker = True
    ):
        super().__init__(hook, host, port, id, log_msgs, verbose, data, loop, cert_path, key_path)

        self.secure = secure

        self.connect()

        if set_local_worker:
            hook.local_worker = self

    @property
    def url(self):
        return f"wss://{self.host}:{self.port}/share" if self.secure else f"ws://{self.host}:{self.port}/share"

    def connect(self):
        args = {"max_size": None, "timeout": TIMEOUT_INTERVAL, "url": self.url, "cookie": f"320984,{self.id}"}

        if self.secure:
            args["sslopt"] = {"cert_reqs": ssl.CERT_NONE}

        print(args)

        self.ws = websocket.create_connection(**args)

    def close(self):
        self.ws.shutdown()

    def start(self):
        while True:
            message = self.ws.recv()
            message = binascii.unhexlify(message[2:-1])
            response = self._recv_msg(message)
            response = str(binascii.hexlify(response))
            self.ws.send(response)

    def search(self, key):
        print("GOT A SEARCH REQUEST")
        print(key)
        # print(kwargs)
        print(self._objects)
        obj = self._objects[key]
        ptr = obj.create_pointer(garbage_collect_data=False, owner=sy.local_worker).wrap()
        # print(obj)
        return ptr
    #     # return super().search(*args, **kwargs)

    def test_hello_world(self):
        print("hello world")
        return True

    # def get_dataset(self):


    # def execute_command(self, message):
    #     message_list = list(message)
    #     message_list[1] = "self"
    #     message = tuple(message_list)
    #     return super().execute_command(message)

    def __getitem__(self, *args, **kwargs):
        print("GOT A __GETITEM__ REQUEST")
        print(args)
        print(kwargs)
        return super().__getitem__(*args, **kwargs)


    # async def _consumer_handler(self):
    #     print("got here")
    #     try:
    #         while True:
    #             msg = await self.ws.recv()
    #             await self.broadcast_queue.put(msg)
    #     except websockets.exceptions.ConnectionClosed:
    #         self._consumer_handler()

    # def start(self):
    #     """Start the server"""
    #     # Secure behavior: adds a secure layer applying cryptography and authentication
    #     if not (self.cert_path is None) and not (self.key_path is None):
    #         ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    #         ssl_context.load_cert_chain(self.cert_path, self.key_path)
    #         start_server = websockets.serve(
    #             self._handler,
    #             'localhost',
    #             self.port,
    #             ssl=ssl_context,
    #             max_size=None,
    #             ping_timeout=None,
    #             close_timeout=None,
    #         )
    #     else:
    #         # Insecure
    #         start_server = websockets.serve(
    #             self._handler,
    #             'localhost',
    #             self.port,
    #             max_size=None,
    #             ping_timeout=None,
    #             close_timeout=None,
    #         )

    #     asyncio.get_event_loop().run_until_complete(start_server)
    #     print("Serving. Press CTRL-C to stop.")
    #     try:
    #         asyncio.get_event_loop().run_forever()
    #     except KeyboardInterrupt:
    #         logging.info("Websocket server stopped.")


class DataownerWorkerFromClient(WebsocketClientWorker):
    def start(self):
        print("listening")
        while True:
            message = self.ws.recv()
            # print(message)
            # print("GOT A MESSAGE")
            message = binascii.unhexlify(message[2:-1])
            # print(message)

            resp = self._recv_msg(message)
            resp = str(binascii.hexlify(resp))
            # print(resp)

            self.ws.send(resp)

    def _recv_msg(self, message: bin) -> bin:
        print(message)
        return self.recv_msg(message)

    def _send_msg(self, message: bin, location: BaseWorker) -> bin:
        print("THIS IS WHERE I AM SENDING THE THING: ")
        print(location)
        print("WHEREAS I AM:")
        print(self)
        return location._recv_msg(message)

    @property
    def url(self):
        return f"wss://{self.host}:{self.port}/share" if self.secure else f"ws://{self.host}:{self.port}/share"

    def connect(self):
        args = {"max_size": None, "timeout": TIMEOUT_INTERVAL, "url": self.url, "cookie": f"320984,{self.id}"}

        if self.secure:
            args["sslopt"] = {"cert_reqs": ssl.CERT_NONE}

        print(args)

        self.ws = websocket.create_connection(**args)

    # def list_objects_remote(self, *args):
    #     return str(self._objects)

    # def objects_count_remote(self, *args):
    #     return len(self._objects)

    def list_objects(self, *args):
        return str(self._objects)

    def objects_count(self, *args):
        return len(self._objects)

    def __str__(self):
        """Returns the string representation of a Websocket worker.
        A to-string method for websocket workers that includes information from the websocket server
        Returns:
            The Type and ID of the worker
        """
        out = "<"
        out += str(type(self)).split("'")[1].split(".")[-1]
        out += " id:" + str(self.id)
        out += " #objects: " + str(self.objects_count())
        out += ">"
        return out


    # this is the search function from BaseWorker
    def search(self, query: Union[List[Union[str, int]], str, int]) -> List[PointerTensor]:
        """Search for a match between the query terms and a tensor's Id, Tag, or Description.
        Note that the query is an AND query meaning that every item in the list of strings (query*)
        must be found somewhere on the tensor in order for it to be included in the results.
        Args:
            query: A list of strings to match against.
            me: A reference to the worker calling the search.
        Returns:
            A list of PointerTensors.
        """
        if isinstance(query, (str, int)):
            query = [query]

        results = list()
        for key, obj in self._objects.items():
            print(key)
            found_something = True
            for query_item in query:
                print(query_item)
                # If deserialization produced a bytes object instead of a string,
                # make sure it's turned back to a string or a fair comparison.
                if isinstance(query_item, bytes):
                    query_item = query_item.decode("ascii")
                query_item = str(query_item)

                match = False
                if query_item == str(key):
                    # print("found match")
                    match = True

                if isinstance(obj, (AbstractObject, FrameworkTensor)):
                    if obj.tags is not None:
                        if query_item in obj.tags:
                            match = True

                    if obj.description is not None:
                        if query_item in obj.description:
                            match = True

                if not match:
                    found_something = False

            if found_something:
                # print("got here")
                # set garbage_collect_data to False because if we're searching
                # for a tensor we don't own, then it's probably someone else's
                # decision to decide when to delete the tensor.
                ptr = obj.create_pointer(garbage_collect_data=True, owner=sy.local_worker).wrap()
                results.append(ptr)

        return results

    def __getitem__(self, idx):
        # NOTE: THIS IS NEVER CALLED
        print(f"I AM ATTEMPTING TO GET AN ITEM AT {idx}")
        time.sleep(5)
        return self._objects.get(idx, None)

    # def _send_msg





