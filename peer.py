from base64 import b64encode, b64decode
from typing import Optional, Tuple
from utils import MsgType, Config
from Crypto.Util import number
from Crypto.Cipher import AES
from node import Node
from file import File
import hashlib
import socket
import struct
import time
import json
import ssl


class Peer(Node):
    def __init__(self, port: int):
        super().__init__()
        self.addr:          str = socket.gethostbyname(socket.gethostname())
        self.port:          int = port
        self.id:            str = hashlib.sha1(self.addr.encode()+bytes(self.port)).hexdigest()
        self.buffer:        int = Config.BufferSize.value
        self.aes_key:       Optional[bytes] = None
        self.key_length:    int = Config.KeyLength.value
        self.generator:     int = Config.Generator.value
        self.priv_key:      Optional[int] = None
        self.pub_key:       Optional[int] = None
        self.prime:         Optional[int] = None
        now = time.time()
        self.joined:        float = now
        self.last_seen:     float = now
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)

    def generate_private_key(self) -> int:
        return int.from_bytes(ssl.RAND_bytes(self.key_length), byteorder='big')

    def generate_public_key(self) -> int:
        return pow(self.generator, self.priv_key, self.prime)

    def get_key(self, remote_pub_key: int) -> bytes:
        shared_secret = pow(remote_pub_key, self.priv_key, self.prime)
        shared_secret_bytes = shared_secret.to_bytes(shared_secret.bit_length() // 8 + 1, byteorder="big")
        return hashlib.sha256(shared_secret_bytes).digest()

    def perform_key_exchange(self) -> bool:
        try:
            if not self.prime:
                self.prime = number.getPrime(1024, ssl.RAND_bytes)
            self.priv_key = self.generate_private_key()
            self.pub_key = self.generate_public_key()
            msg = {
                "prime": self.prime,
                "pub_key": self.pub_key
            }
            encoded_msg = b64encode(json.dumps(msg).encode())
            msg_size = struct.pack(">L", len(encoded_msg))
            self.sock.sendto(msg_size, self.address())

            while encoded_msg:
                self.sock.sendto(encoded_msg[:self.buffer], self.address())
                encoded_msg = encoded_msg[self.buffer:]

            response = b""
            msg_size = struct.calcsize(">L")
            while len(response) < msg_size:
                data, _ = self.sock.recvfrom(self.buffer)
                response += data

            packed_msg_size = response[:msg_size]
            response = response[msg_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            while len(response) < msg_size:
                data, _ = self.sock.recvfrom(self.buffer)
                response += data

            remote_pub_key = int.from_bytes(response, byteorder='big')
            self.aes_key = self.get_key(remote_pub_key)
            return True
        except (TimeoutError, socket.timeout, socket.error):
            return False

    def copy(self):
        return Peer(self.port)

    def address(self) -> Tuple[str, int]:
        return self.addr, self.port

    def as_tuple(self) -> Tuple[str, int, float]:
        return self.addr, self.port, self.last_seen

    def send(self, port: int, header: Optional[MsgType] = "", msg: Optional[str] = "") -> bool:
        response = self.perform_key_exchange()
        if response:
            cipher = AES.new(self.aes_key, AES.MODE_GCM)
            cipher.update(header.encode())
            msg = json.dumps({"msg": msg, "port": str(port)})
            ciphertext, tag = cipher.encrypt_and_digest(msg.encode())
            json_k = ['nonce', 'header', 'ciphertext', 'tag']
            json_v = [b64encode(x).decode('utf-8') for x in [cipher.nonce, header.encode(), ciphertext, tag]]
            encoded_msg = b64encode(json.dumps(dict(zip(json_k, json_v))).encode())
            msg_size = struct.pack(">L", len(encoded_msg))
            self.sock.sendto(msg_size, self.address())

            while encoded_msg:
                self.sock.sendto(encoded_msg[:self.buffer], self.address())
                encoded_msg = encoded_msg[self.buffer:]
            return True
        return False

    def receive(self) -> Optional[Tuple[str, str, Tuple[str, int]]]:
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

            b64 = json.loads(b64decode(response))
            json_k = ['nonce', 'header', 'ciphertext', 'tag']
            jv = {k: b64decode(b64[k]) for k in json_k}
            cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=jv['nonce'])
            cipher.update(jv['header'])

            header = jv['header'].decode()
            msg = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag']).decode()

        except socket.error as e:
            print(e)
            return None
        return header, msg, addr

    def send_recv(self, port: int, header: Optional[MsgType] = "", msg: Optional[str] = "") -> Optional[Tuple[str, str, Tuple[str, int]]]:
        self.send(port, header, msg)
        return self.receive()

    def ping(self, port: int) -> bool:
        try:
            response = self.send_recv(port, MsgType.Ping)
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
