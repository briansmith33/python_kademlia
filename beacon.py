from utils import hexify_ip, unhexify_ip, MsgType, Config
from typing import Optional, List, Tuple
from base64 import b64encode, b64decode
from bucket_list import BucketList
from event_chain import EventChain
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA512
from Crypto.Cipher import AES
from threading import Thread
from kbucket import KBucket
from event import Event
from peer import Peer
from file import File
import tempfile
import hashlib
import socket
import random
import struct
import gzip
import json
import uuid
import time
import ssl
import os


class Beacon(Thread):
    def __init__(self, port: int, boot_port: int):
        super().__init__()
        self.addr:          str = socket.gethostbyname(socket.gethostname())
        self.port:          int = port
        self.id:            str = hashlib.sha1(self.addr.encode() + bytes(self.port)).hexdigest()
        self.boot_port:     int = boot_port
        self.sock:          socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.routing_table: BucketList = BucketList()
        self.storage:       BucketList = BucketList()
        self.events:        EventChain = EventChain()
        self.buffer_size:   int = Config.BufferSize.value
        self.alpha:         int = Config.Alpha.value
        self.last_update:   Optional[float] = None
        self.key_length:    int = Config.KeyLength.value
        self.generator:     int = Config.Generator.value
        self.prime:         Optional[int] = None
        self.pub_key:       str = Config.PubKey.value
        self.backup_hosts:  List[str] = Config.BackupHosts.value

    @staticmethod
    def get_mac_address() -> str:
        return ':'.join(['{:02x}'.format((uuid.getnode() >> el) & 0xff) for el in range(0, 8 * 6, 8)][::-1])

    def generate_private_key(self) -> int:
        return int.from_bytes(ssl.RAND_bytes(self.key_length), byteorder='big')

    def generate_public_key(self, private_key: int) -> int:
        return pow(self.generator, private_key, self.prime)

    def get_key(self, remote_pub_key: int, private_key: int) -> bytes:
        shared_secret = pow(remote_pub_key, private_key, self.prime)
        shared_secret_bytes = shared_secret.to_bytes(shared_secret.bit_length() // 8 + 1, byteorder="big")
        return hashlib.sha256(shared_secret_bytes).digest()

    def perform_key_exchange(self) -> Optional[bytes]:
        response = b""
        msg_size = struct.calcsize(">L")
        while len(response) < msg_size:
            data, _ = self.sock.recvfrom(self.buffer_size)
            response += data

        packed_msg_size = response[:msg_size]
        response = response[msg_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        addr = None
        while len(response) < msg_size:
            data, addr = self.sock.recvfrom(self.buffer_size)
            response += data

        response = json.loads(b64decode(response))

        try:
            prime = int(response['prime'])
            remote_pub_key = int(response['pub_key'])
        except (KeyError, ValueError):
            return

        if prime.bit_length() == 1024:
            self.prime = prime
            private_key = self.generate_private_key()
            pub_key = self.generate_public_key(private_key)
            response = pub_key.to_bytes(pub_key.bit_length() // 8 + 1, byteorder="big")

            msg_size = struct.pack(">L", len(response))
            self.sock.sendto(msg_size, addr)

            while response:
                self.sock.sendto(response[:self.buffer_size], addr)
                response = response[self.buffer_size:]

            return self.get_key(remote_pub_key, private_key)

    def send(self, addr: Tuple[str, int], key: bytes, header: Optional[MsgType] = "", msg: Optional[str] = "") -> None:
        cipher = AES.new(key, AES.MODE_GCM)
        cipher.update(header.encode())
        ciphertext, tag = cipher.encrypt_and_digest(msg.encode())
        json_k = ['nonce', 'header', 'ciphertext', 'tag']
        json_v = [b64encode(x).decode('utf-8') for x in [cipher.nonce, header.encode(), ciphertext, tag]]

        encoded_msg = b64encode(json.dumps(dict(zip(json_k, json_v))).encode())
        msg_size = struct.pack(">L", len(encoded_msg))
        self.sock.sendto(msg_size, addr)

        while encoded_msg:
            self.sock.sendto(encoded_msg[:self.buffer_size], addr)
            encoded_msg = encoded_msg[self.buffer_size:]

    def receive(self, key: bytes) -> Tuple[str, str, str, Tuple[str, int]]:
        response = b""
        msg_size = struct.calcsize(">L")
        while len(response) < msg_size:
            data, _ = self.sock.recvfrom(self.buffer_size)
            response += data

        packed_msg_size = response[:msg_size]
        response = response[msg_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        addr = None
        while len(response) < msg_size:
            data, addr = self.sock.recvfrom(self.buffer_size)
            response += data

        b64 = json.loads(b64decode(response))
        json_k = ['nonce', 'header', 'ciphertext', 'tag']
        jv = {k: b64decode(b64[k]) for k in json_k}
        cipher = AES.new(key, AES.MODE_GCM, nonce=jv['nonce'])
        cipher.update(jv['header'])

        header = jv['header'].decode()
        data = json.loads(cipher.decrypt_and_verify(jv['ciphertext'], jv['tag']).decode())
        msg = data['msg']
        port = data['port']
        return header, msg, port, addr

    def bootstrap(self) -> Optional[KBucket]:
        return self.find_node(self.id, Peer(self.boot_port))

    def find_node(self, peer_id: str, boot_peer: Optional[Peer] = None, nearest_bucket: Optional[KBucket] = None) -> Optional[KBucket]:
        if not boot_peer:
            closest_bucket = self.routing_table.find_closest(peer_id)
            boot_peer = closest_bucket.find_closest(peer_id)

        if not nearest_bucket:
            response = boot_peer.find_node(peer_id, self.port)
            if not response:
                return None

            header, data, addr = response
            if header == MsgType.Found:
                data = json.loads(data)
                bucket = KBucket()
                for peer in data:
                    peer = Peer(int(peer[1]))
                    if peer.id != boot_peer.id:
                        response = peer.ping(self.port)
                        if response:
                            bucket.add(peer)
                    else:
                        bucket.add(peer)
                self.routing_table.append(bucket)
                return self.find_node(peer_id, boot_peer, bucket)
        else:
            nearest = nearest_bucket.find_closest(peer_id).id
            if nearest == boot_peer.id:
                return nearest_bucket
            original = nearest
            ordered = nearest_bucket.find_a_closest(peer_id)
            for p in ordered:
                if p.id != boot_peer.id:
                    header, data, addr = p.find_node(peer_id, self.port)
                    if header == MsgType.Found:
                        data = json.loads(data)
                        bucket = KBucket()
                        for peer in data:
                            peer = Peer(int(peer[1]))
                            if not self.routing_table.find_node(peer.id) and peer.id != self.id:
                                response = peer.ping(self.port)
                                if response:
                                    self.routing_table.add_node(self.port, peer)
                                    bucket.add(peer)

                        if bucket.size() > 0:
                            closest = bucket.find_closest(peer_id).id
                            if closest < nearest:
                                nearest = closest
                                nearest_bucket = bucket

            if nearest < original:
                return self.find_node(peer_id, boot_peer, nearest_bucket)

        return nearest_bucket

    def find_value(self, key: str) -> None:
        closest_bucket = self.find_node(key)
        kv_pair = None
        for peer in closest_bucket.preorder():
            header, data, addr = peer.find_value(key, self.port)
            if header == MsgType.Found:
                kv_pair = json.loads(data)
                break

        if kv_pair:
            file = File()
            file.from_tuple(kv_pair)
            self.storage.add_node(self.port, file)
            closest_bucket = self.find_node(file.owner)
            owner = closest_bucket.find_node(file.owner)

            header, file_contents, addr = owner.get_value(file.filename, self.port)
            if header == MsgType.Found:
                file_contents = gzip.decompress(b64decode(file_contents.encode()))
                if hashlib.sha1(file_contents).hexdigest() == file.id:
                    print(file_contents.decode())
                    '''
                    with open(file.filename, 'wb') as f:
                        f.write(b64decode(file_contents.encode()))
                    '''
            else:
                print(header)

    def store(self, filename: str) -> None:
        with open(filename, 'rb') as f:
            file = File(self.id, f)

        closest_bucket = self.find_node(file.id)
        for peer in closest_bucket.preorder():
            peer.store(file, self.port)

    def save_state(self) -> None:
        while True:
            if not self.last_update or time.time() - self.last_update > 600:
                table = ""
                for peer in self.routing_table.as_tuples():
                    table += hexify_ip(peer[0]) + "\n"

                if not os.path.isdir(os.path.join(tempfile.gettempdir(), self.id)):
                    os.mkdir(os.path.join(tempfile.gettempdir(), self.id))

                with open(os.path.join(tempfile.gettempdir(), self.id, socket.gethostname() + ".log"), 'w') as f:
                    f.write(table)

                self.last_update = time.time()
            time.sleep(10)

    def broadcast(self, event: Event) -> None:
        all_peers = self.routing_table.list_nodes()
        a_peers = random.choices(all_peers, k=self.alpha)
        for peer in a_peers:
            peer.send(self.port, MsgType.Event, json.dumps({"msg": event.data, "sig": b64encode(event.signature).decode()}))

    def run(self) -> None:
        self.sock.bind((self.addr, self.port))
        if self.boot_port:
            self.bootstrap()
            print(self.routing_table.as_tuples())
        '''
            if err:
                for host in self.backup_hosts:
                    self.bootport = host
                    err = self.bootstrap()
                    if not err:
                        break

        else:
            try:
                with open(os.path.join(tempfile.gettempdir(), self.id, socket.gethostname()+".log"), 'r') as f:
                    hexaddrs = f.readlines()

                for hexaddr in hexaddrs:
                    self.bootport = unhexify_ip(hexaddr.replace("\n", ""))
                    err = self.bootstrap()
                    if not err:
                        break

            except FileNotFoundError:
                for host in self.backup_hosts:
                    self.bootport = host
                    err = self.bootstrap()
                    if not err:
                        break
        '''
        # Thread(target=self.store_table).start()

        while True:
            key = self.perform_key_exchange()
            if not key:
                continue

            header, data, port, addr = self.receive(key)

            if header == MsgType.Ping:
                peer_id = hashlib.sha1(addr[0].encode() + bytes(int(port))).hexdigest()
                found = self.routing_table.find_node(peer_id)
                if not found:
                    self.routing_table.add_node(self.port, Peer(int(port)))
                self.send(addr, key, MsgType.Pong)

            if header == MsgType.FindNode:
                peer_id = data
                bucket = self.routing_table.find_closest(peer_id)
                if bucket:
                    self.send(addr, key, MsgType.Found, json.dumps(bucket.as_tuples()+[(self.addr, self.port)]))
                else:
                    self.send(addr, key, MsgType.Found, json.dumps([(self.addr, self.port)]))

                peer_id = hashlib.sha1(addr[0].encode() + bytes(int(port))).hexdigest()
                found = self.routing_table.find_node(peer_id)
                if not found:
                    self.routing_table.add_node(self.port, Peer(int(port)))

            if header == MsgType.FindValue:
                node_id = data
                file = self.storage.find_node(node_id)
                if file:
                    self.send(addr, key, MsgType.Found, json.dumps(file.as_tuple()))
                else:
                    self.send(addr, key, MsgType.NotFound)

            if header == MsgType.GetValue:
                filename = data
                try:
                    with open(filename, 'rb') as f:
                        data = b64encode(gzip.compress(f.read())).decode()
                        self.send(addr, key, MsgType.Found, data)

                except FileNotFoundError:
                    self.send(addr, key, MsgType.NotFound)

            if header == MsgType.Store:
                data = json.loads(data)
                file = File()
                file.from_tuple(data)
                self.storage.add_node(self.port, file)
                print(self.storage.as_tuples())
                self.send(addr, key, MsgType.Stored)

            if header == MsgType.Event:
                data = json.loads(data)
                msg = data['msg']
                signature = b64decode(data['sig'].encode())
                latest_event = self.events.last()
                if latest_event and latest_event.signature != signature or not latest_event:

                    pub_key = ECC.import_key(self.pub_key)
                    h = SHA512.new(msg.encode())
                    verifier = DSS.new(pub_key, 'fips-186-3')
                    try:
                        verifier.verify(h, signature)
                        print(f"\n{hashlib.sha1(addr[0].encode()+bytes(int(port))).hexdigest()} {msg}", end="\n>> ")
                        event = Event(msg, signature)
                        self.broadcast(event)
                        Thread(target=self.events.add, args=(event,)).start()
                    except ValueError as e:
                        print(e)
                        print("The message is not authentic.")
