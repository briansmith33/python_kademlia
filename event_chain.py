from utils import get_target_range
from typing import Optional
from event import Event
import hashlib


class EventChain:
    def __init__(self):
        self.head:          Optional[Event] = None
        self.difficulty:    int = 3

    def mine(self, event: Event) -> None:
        min_target, max_target = get_target_range(self.difficulty, 40)
        hash_data = event.data.encode()
        hash_data += event.signature
        if event.prev_hash:
            hash_data += event.prev_hash.encode()
        else:
            hash_data += b"0"*40

        nonce = 0
        while True:
            h = int.from_bytes(hashlib.sha1(hash_data + bytes(nonce)).digest(), byteorder='big')
            if min_target < h < max_target:
                event.hash = hex(h)[2:]
                event.nonce = nonce
                return
            nonce += 1

    def add(self, event: Event) -> None:
        if not self.head:
            self.head = event
            self.mine(event)
        else:
            current = self.head
            while True:
                if not current.next:
                    event.prev_hash = current.hash
                    current.next = event
                    self.mine(event)
                    break
                current = current.next

    def last(self) -> Optional[Event]:
        if not self.head:
            return None
        current = self.head
        while True:
            if not current.next:
                return current
            current = current.next

    def print(self) -> None:
        if not self.head:
            return
        current = self.head
        while True:
            print(current.hash)
            if not current.next:
                break
            current = current.next
