from typing import Optional, Tuple, Any
from utils import MsgType


class Node:
    def __init__(self):
        self.id:    Optional[str]  = None
        self.left:  Optional[Node] = None
        self.right: Optional[Node] = None

    def perform_key_exchange(self, port) -> bool:
        pass

    def send(self, port: int, header: Optional[MsgType] = "", msg: Optional[str] = "") -> None:
        pass

    def ping(self, port: int):
        pass

    def find_node(self, target: str, port: int) -> Optional[Tuple[str, str, str]]:
        pass

    def find_value(self, target: str, port: int) -> Optional[Tuple[str, str, str]]:
        pass

    def get_value(self, filename: str, port: int) -> Optional[Tuple[str, str, str]]:
        pass

    def store(self, file: Any, port: int) -> Optional[Tuple[str, str, str]]:
        pass

    def copy(self):
        pass

    def as_tuple(self):
        pass

    def is_older_than(self, n_seconds: int):
        pass
