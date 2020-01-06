import syft as sy
from syft.workers.websocket_client import WebsocketClientWorker
import torch

from dataowner_worker import DataownerWorker

PROXY_URL = "13.57.48.147"
PROXY_PORT = 8888
VERBOSE = True

hook = sy.TorchHook(torch)

features = torch.Tensor([[0, 0], [0, 1], [1, 0], [1, 1]])
labels = torch.Tensor([0, 1, 1, 0])

dataowner = DataownerWorker(hook, PROXY_URL, PROXY_PORT, verbose = VERBOSE, id = 125, data = [features, labels])
dataowner.start()
