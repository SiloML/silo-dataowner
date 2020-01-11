import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import syft as sy
from syft.workers.websocket_client import WebsocketClientWorker
import torch
import sys
import numpy as np
from torchvision import datasets, transforms
import requests
import websocket

from dataowner_worker import DataownerWorker

FIREBASE_URL = "https://us-central1-silo-ml.cloudfunctions.net/"
PROXY_URL = "127.0.0.1"
PROXY_PORT = 8888
VERBOSE = True
DATASET_ID = sys.argv[-1]
print(f"requesting dataset ID {DATASET_ID}")

hook = sy.TorchHook(torch)

resp = requests.get(FIREBASE_URL + f"registerDevice?dataset_id={DATASET_ID}")
if resp.status_code == 400:
	sys.exit("dataset ID does not exist")
elif resp.status_code != 200:
	sys.exit(f"something went wrong and we don't know what, {resp}")

otp = input("Get OTP from GUI and enter here: ")

resp = requests.get(FIREBASE_URL + f"verifyOwnerOTP?otp={otp}&dataset_id={DATASET_ID}")
if resp.status_code == 400:
	sys.exit("wrong OTP")
elif resp.status_code == 200:
	print("got it!")
else:
	sys.exit(f"something went wrong and we don't know what, {resp}")

connection_token = resp.text
# print(connection_token)


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

dataowner = DataownerWorker(hook, PROXY_URL, PROXY_PORT, connection_token, verbose = VERBOSE, id = "researcher" if len(sys.argv) == 1 else sys.argv[-1])
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

try:
	dataowner.start()
except websocket._exceptions.WebSocketConnectionClosedException:
	requests.get(FIREBASE_URL + f"disconnectDevice?dataset_id={DATASET_ID}")
	print("Something went wrong with the proxy server, exiting")