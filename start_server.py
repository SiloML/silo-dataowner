import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import syft as sy
from syft.workers.websocket_client import WebsocketClientWorker
import torch
import sys
import numpy as np
from torchvision import datasets, transforms

from dataowner_worker import DataownerWorker

PROXY_URL = "127.0.0.1"
PROXY_PORT = 8888
VERBOSE = False

hook = sy.TorchHook(torch)

# features = torch.Tensor(np.loadtxt("features.csv", delimiter = ","))
# labels = torch.Tensor(np.loadtxt("labels.csv", delimiter = ","))
# features = np.random.rand(100, 3)
# labels = features.sum(axis = -1)
# features = torch.Tensor(features)
# labels = torch.Tensor(labels)
dataset = datasets.MNIST('../data', train=True, download=True,
                   transform=transforms.Compose([
                       transforms.ToTensor(),
                       transforms.Normalize((0.1307,), (0.3081,))
                   ]))
inds = np.random.choice(len(dataset.data), len(dataset.data) // 100)
features = dataset.data[inds]
labels = dataset.targets[inds]
print(features.shape)
# features = torch.Tensor([[0, 0], [0, 1], [1, 0], [1, 1]])
# labels = torch.Tensor([0, 1, 1, 0])
dataset = sy.BaseDataset(features, labels)

dataowner = DataownerWorker(hook, PROXY_URL, PROXY_PORT, verbose = VERBOSE, id = "researcher" if len(sys.argv) == 1 else sys.argv[-1])
# hook.local_worker = dataowner
print(hook.local_worker)
dataowner.register_obj(features, b"data")
dataowner.register_obj(labels, b"targets")
features.owner = dataowner
labels.owner = dataowner
# dataowner.add_dataset(dataset, "dataset")
# dataowner.load_data([features, labels], obj_id = ["features", "labels"])
print(dataowner)
# dataowner.id = 'me'
dataowner.start()
