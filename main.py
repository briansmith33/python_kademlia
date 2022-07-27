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
import sys
import os


def interact(node):
    key_path = os.path.join(os.getcwd(), sys.argv[0], 'assets/private_key.pem')
    with open(key_path, 'rt') as f:
        private_key = ECC.import_key(f.read())

    while True:
        msg = input(">> ")

        if msg.startswith("upload"):
            filename = msg.replace("upload ", "")
            node.store(filename)

        if msg.startswith("download"):
            key = msg.replace("download ", "")
            node.find_value(key)

        h = SHA512.new(msg.encode())
        signer = DSS.new(private_key, 'fips-186-3')
        signature = signer.sign(h)
        event = Event(msg, signature)
        node.events.add(event)
        node.broadcast(event)


if __name__ == '__main__':

    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('bootaddr', nargs='?', type=str)
    args = parser.parse_args()
    server = Server(args.bootaddr)
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    parser.add_argument('boot_port', nargs='?', type=int)
    args = parser.parse_args()
    beacon = Beacon(args.port, args.boot_port)
    beacon.start()
    interact(beacon)

