from base64 import b64encode, b64decode
from typing import Optional, Tuple
from utils import MsgType, Config
from node import Node
from file import File
import hashlib
import socket
import struct
import time
import json


class Peer(Node):
    def __init__(self, port: int):
        super().__init__()
        self.addr:          str = socket.gethostbyname(socket.gethostname())
        self.port:          int = port
        self.id:            str = hashlib.sha1(self.addr.encode()+bytes(self.port)).hexdigest()
        self.buffer:        int = Config.BufferSize.value
        self.sock:          socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        now = time.time()
        self.joined:        float = now
        self.last_seen:     float = now
        self.sock.settimeout(5)

    def copy(self):
        return Peer(self.port)

    def address(self) -> Tuple[str, int]:
        return self.addr, self.port

    def as_tuple(self) -> Tuple[str, int, float]:
        return self.addr, self.port, self.last_seen

    def send(self, port: int, header: Optional[MsgType] = "", msg: Optional[str] = "") -> None:
        encoded_msg = b64encode(json.dumps({"header": header, "msg": msg, "port": str(port)}).encode())
        msg_size = struct.pack(">L", len(encoded_msg))
        self.sock.sendto(msg_size, self.address())

        while encoded_msg:
            self.sock.sendto(encoded_msg[:self.buffer], self.address())
            encoded_msg = encoded_msg[self.buffer:]

    def receive(self) -> Optional[Tuple[str, str, str]]:
        try:
            response = b""
            msg_size = struct.calcsize(">L")
            while len(response) < msg_size:
                data, _ = self.sock.recvfrom(self.buffer)
                response += data

            packed_msg_size = response[:msg_size]
            response = response[msg_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            addr = None
            while len(response) < msg_size:
                data, addr = self.sock.recvfrom(self.buffer)
                response += data
            response = json.loads(b64decode(response))

        except socket.error as e:
            print(e)
            return None
        return response['header'], response['msg'], addr

    def send_recv(self, port: int, header: Optional[MsgType] = "", plaintext: Optional[str] = "") -> Optional[Tuple[str, str, str]]:
        self.send(port, header, plaintext)
        return self.receive()

    def ping(self, port: int) -> bool:
        self.send(port, MsgType.Ping)
        try:
            response = self.receive()
            if response and response[0] == MsgType.Pong:
                return True
        except (TimeoutError, socket.timeout, socket.error):
            return False
        return False

    def find_node(self, target: str, port: int) -> Optional[Tuple[str, str, str]]:
        return self.send_recv(port, MsgType.FindNode, target)

    def store(self, file: File, port: int) -> Optional[Tuple[str, str, str]]:
        return self.send_recv(port, MsgType.Store, json.dumps(file.as_tuple()))

    def find_value(self, target: str, port: int) -> Optional[Tuple[str, str, str]]:
        return self.send_recv(port, MsgType.FindValue, target)

    def get_value(self, filename: str, port: int) -> Optional[Tuple[str, str, str]]:
        return self.send_recv(port, MsgType.GetValue, filename)

    def is_older_than(self, n_seconds: int):
        return time.time() - self.last_seen > n_seconds and self.last_seen > 0
