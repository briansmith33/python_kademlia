from typing import Optional, Any, List, Tuple, Union
from dotenv import dotenv_values
from enum import Enum
import random

config = dotenv_values(".env")

class MsgType(str, Enum):
    Found = '0'
    NotFound = '1'
    Ping = '2'
    Pong = '3'
    FindNode = '4'
    FindValue = '5'
    GetValue = '6'
    Store = '7'
    Stored = '8'
    Event = '9'


class Config(Enum):
    BufferSize = 4096
    KeyLength = 540
    Generator = 3
    KNodes = 20
    Alpha = 3
    PubKey = config['PUB_KEY']
    BackupHosts = [
            "www.host.com",
            "www.host.net"
        ]


class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()

    def is_empty(self):
        return len(self.items) == 0

    def peek(self):
        if not self.is_empty():
            return self.items[-1]

    def __len__(self):
        return len(self.items)


class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.insert(0, item)

    def dequeue(self):
        if not self.is_empty():
            return self.items.pop()

    def is_empty(self):
        return len(self.items) == 0

    def peek(self):
        if not self.is_empty():
            return self.items[-1]

    def __len__(self):
        return len(self.items)


def is_nth_bit_set(x: int, n: int) -> bool:
    if x & (1 << n):
        return True
    return False


def unset_nth_bit(x: int, n: int) -> int:
    return x & ~(1 << n)


def set_nth_bit(x: int, n: int) -> int:
    return x | 1 << n


def toggle_nth_bit(x: int, n: int) -> int:
    return x ^ (1 << n)


def partition(array: List[Any], start: int, end: int) -> int:
    i = start + 1
    piv = array[start]
    j = start + 1
    while j <= end:
        if array[j].id < piv.id:
            array[i], array[j] = array[j], array[i]
            i += 1
        j += 1

    array[start], array[i - 1] = array[i - 1], array[start]
    return i - 1


def quick_sort(array: List[Any], start: Optional[int] = None, end: Optional[int] = None) -> List[Any]:

    if start is None and end is None:
        start = 0
        end = len(array) - 1

    if start < end:
        piv = partition(array, start, end)
        quick_sort(array, start, piv - 1)
        quick_sort(array, piv + 1, end)

    return array


def get_target_range(difficulty: int, n_bytes: int) -> Tuple[int, int]:
    max_target = int((str(difficulty) * difficulty) + ("f" * (n_bytes - difficulty)), 16)
    min_target = int((str(difficulty) * difficulty) + (str(hex(difficulty + 1)[2:]) * (n_bytes - difficulty)), 16)
    return min_target, max_target


def hexify_ip(addr: str) -> str:
    hexaddr = ""
    for octet in addr.split("."):
        hexaddr += '{:02x}'.format(int(octet))
    return hexaddr


def unhexify_ip(hexaddr: str) -> str:
    addr = []
    for i in range(0, len(hexaddr), 2):
        addr.append(str(int(hexaddr[i:i + 2], 16)))
    return ".".join(addr)
