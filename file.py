from typing import BinaryIO, TextIO, Union, Optional, Tuple
from node import Node
import hashlib
import time


class File(Node):
    def __init__(self, peer_id: Optional[str] = None, file: Optional[Union[BinaryIO, TextIO]] = None):
        super().__init__()
        self.owner:         Optional[str]   = peer_id
        self.filename:      Optional[str]   = file.name if file else None
        self.size:          Optional[int]   = file.__sizeof__() if file else None
        self.published_on:  Optional[float] = time.time()
        if file:
            contents = file.read()
            if isinstance(contents, bytes):
                self.id = hashlib.sha1(contents).hexdigest()
            elif isinstance(contents, str):
                self.id = hashlib.sha1(contents.encode()).hexdigest()

    def as_tuple(self) -> Tuple[str, str, str, int, float]:
        return self.id, self.owner, self.filename, self.size, self.published_on

    def from_tuple(self, file_tuple: Tuple[str, str, str, int, float]) -> None:
        self.id, self.owner, self.filename, self.size, self.published_on = file_tuple

    def copy(self):
        file = File()
        file.from_tuple(self.as_tuple())
        return file
