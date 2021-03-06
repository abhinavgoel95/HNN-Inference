import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from torchvision import datasets, transforms
from torchvision import models
from torch.autograd import Variable
from torch.utils.data.sampler import SubsetRandomSampler
import time
import numpy as np
import shutil
import os
import argparse
import vgg
from utils import progress_bar
import pdb
from collections import OrderedDict

cfg = {
    '1': [128, 'M'], #65
    '2': [64, 32, 'D'], #68
    '3': [32, 32, 32, 'M', 32, 64, 64, 'M'],
    '4': [16, 32, 32, 32, 'M', 'D'],
    '5': [16, 32, 'M', 32, 32, 'M', 64,'D'],
    '6': [16, 32, 32, 'M', 64, 64, 128, 'M', 'D'],
}

cfg_down = {
    '2': [64, 128, 'M'],
    '3': [64, 64, 64, 128, 'M'],
}

class model(nn.Module):
    def __init__(self, size):
        super(model, self).__init__()
        self.features = self._make_layers(cfg[size], channels = 32)
        self.features_down = self._make_layers(cfg_down[size], channels = 64)
        self.classifier = nn.Sequential(
                        nn.Linear(128*7*7, 2),
                )

    def forward(self, x):
        y = self.features(x)
        x = self.features_down(y)
        x = x.view(x.size(0), -1)
        out = self.classifier(x)
        return y, out

    def _make_layers(self, cfg, channels = 32):
        layers = []
        in_channels = channels
        for x in cfg:
            if x == 'D':
                layers += [nn.Dropout()]
            elif x == 'M':
                layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
            else:
                layers += [nn.Conv2d(in_channels, x, kernel_size=3, padding=1), nn.BatchNorm2d(x), nn.ReLU(inplace=True)]
                in_channels = x
        layers += [nn.AvgPool2d(kernel_size=1, stride=1)]
        return nn.Sequential(*layers)

    def evaluate(self, data, target, device):
        self.eval()
        data = data.to(device)
        target = target[0]
        target = target.to(device)
        y, net_out = self(data)
        return y, net_out

def get_SG2(size):
    return model(size)


def average_softmax(model, trainloader, valloader, device):
    nb_classes = 10
    out_classes = 10
    counts = [0 for i in range(nb_classes)]
    soft_out = torch.zeros((nb_classes, 1, nb_classes)).cuda()
    with torch.no_grad():
        for i, (inputs, classes) in enumerate(valloader):
            inputs = inputs.to(device)
            classes = classes[0].to(device)
            outputs = model(inputs)
            outputs = m(outputs)
            for categ in range(nb_classes):
                indices = (classes == categ).nonzero()[:,0]
                hold = outputs[indices]
                soft_out[categ] += hold.sum(dim=0)
                counts[categ]+= hold.shape[0]
    for i in range(nb_classes):
        soft_out[i] = soft_out[i]/counts[i]
    return soft_out
            