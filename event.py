from typing import Optional


class Event:
    def __init__(self, data: str, signature: bytes):
        self.data:      str = data
        self.signature: bytes = signature
        self.hash:      Optional[str] = None
        self.prev_hash:  Optional[str] = None
        self.nonce:     Optional[int] = None
        self.next:      Optional[Event] = None
