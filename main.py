from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA512
from base64 import b64encode
from beacon import Beacon
from event import Event
import argparse
import hashlib
import gzip
import json

if __name__ == '__main__':

    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('bootaddr', nargs='?', type=str)
    args = parser.parse_args()
    server = Server(args.bootaddr)
    Thread(target=server.run, daemon=True).start()
    while True:
        msg = input(">> ")
        server.broadcast(msg)
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    parser.add_argument('boot_port', nargs='?', type=int)
    args = parser.parse_args()
    beacon = Beacon(args.port, args.boot_port)
    beacon.start()

    key_path = "../assets/private_key.pem"

    with open(key_path, 'rt') as f:
        private_key = ECC.import_key(f.read())

    while True:
        msg = input(">> ")

        if msg.startswith("upload"):
            filename = msg.replace("upload ", "")
            beacon.store(filename)

        if msg.startswith("download"):
            key = msg.replace("download ", "")
            beacon.find_value(key)

        h = SHA512.new(msg.encode())
        signer = DSS.new(private_key, 'fips-186-3')
        signature = signer.sign(h)
        event = Event(msg, signature)
        beacon.events.add(event)
        beacon.broadcast(event)
