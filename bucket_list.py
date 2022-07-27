from typing import Optional, List, Tuple
from utils import quick_sort, Config
from kbucket import KBucket
from node import Node
import random


class BucketList:
    def __init__(self):
        self.head:      Optional[KBucket] = None
        self.k_nodes:   int = Config.KNodes.value

    def __len__(self) -> int:
        length = 0
        current = self.head
        while current:
            length += 1
            current = current.next
            if current == self.head:
                return length

    def append(self, new_bucket: KBucket) -> None:
        if not self.head:
            self.head = new_bucket
            self.head.next = self.head
            self.head.prev = self.head
        else:
            prev = self.head.prev
            self.head.prev = new_bucket
            new_bucket.next = self.head
            new_bucket.prev = prev
            prev.next = new_bucket

    def prepend(self, new_bucket: KBucket) -> None:
        if not self.head:
            new_bucket.next = new_bucket
            new_bucket.prev = new_bucket
        else:
            prev = self.head.prev
            self.head.prev = new_bucket
            new_bucket.next = self.head
            new_bucket.prev = prev
            prev.next = new_bucket
        self.head = new_bucket

    def add_node(self, port: int, new_node: Node) -> None:
        bucket = self.find_closest(new_node.id)
        if not bucket:
            bucket = KBucket()
            bucket.add(new_node)
            self.insert(bucket)
        elif bucket.size() < bucket.k_nodes:
            bucket.add(new_node)
        else:
            oldest_peer = bucket.oldest()
            if oldest_peer.is_older_than(3600):
                response = oldest_peer.ping(port)
                if not response:
                    bucket.delete(oldest_peer)
                    bucket.add(new_node)
                    return
            k1, k2 = bucket.split()

            self.delete_bucket(bucket)
            left_distance = int(k1.root.id, 16) ^ int(new_node.id, 16)
            right_distance = int(k2.root.id, 16) ^ int(new_node.id, 16)
            k1.add(new_node) if left_distance < right_distance else k2.add(new_node)
            self.insert(k1)
            self.insert(k2)

    def find_node(self, key: str) -> Optional[Node]:
        bucket = self.find_closest(key)
        if bucket:
            node = bucket.find_node(key)
            if not node:
                node = bucket.prev.find_node(key)

            if not node:
                node = bucket.next.find_node(key)

            return node

    def insert(self, new_bucket: KBucket) -> None:
        buckets = self.list()
        if not buckets:
            self.append(new_bucket)
            return

        if new_bucket.root.id > buckets[-1].root.id:
            self.append(new_bucket)
            return

        if new_bucket.root.id < buckets[0].root.id:
            self.prepend(new_bucket)
            return

        for i in range(len(buckets)-1):
            if buckets[i].root.id < new_bucket.root.id < buckets[i + 1].root.id:
                self.add_after_node(buckets[i].root.id, new_bucket)
                return

    def add_after_node(self, key: str, new_bucket: KBucket) -> None:
        current = self.head
        while current:
            if current.next == self.head and current.root.id == key:
                self.append(new_bucket)
                return
            elif current.root.id == key:
                nxt = current.next
                current.next = new_bucket
                new_bucket.next = nxt
                new_bucket.prev = current
                nxt.prev = new_bucket
                return
            current = current.next

    def add_before_node(self, key: str, new_bucket: KBucket) -> None:
        current = self.head
        while current:
            if current.prev == self.head and current.root.id == key:
                self.prepend(new_bucket)
                return
            elif current.root.id == key:
                prev = current.prev
                prev.next = new_bucket
                current.prev = new_bucket
                new_bucket.next = current
                new_bucket.prev = prev
                return
            current = current.next

    def delete_bucket(self, bucket: KBucket) -> None:
        current = self.head
        while current:
            if current == bucket and current == self.head:
                if current.next == current:
                    self.head = None
                else:
                    nxt = current.next
                    prev = current.prev
                    prev.next = nxt
                    nxt.prev = prev
                    self.head = nxt
                current = None
                return
            elif current == bucket:
                nxt = current.next
                prev = current.prev
                prev.next = nxt
                nxt.prev = prev
                current = None
                return
            current = current.next
            if current == self.head:
                return

    def find_bucket(self, target: str) -> Optional[KBucket]:
        current = self.head
        if current.root.id == target:
            return current

        left_distance = int(current.prev.root.id, 16) ^ int(target, 16)
        right_distance = int(current.next.root.id, 16) ^ int(target, 16)
        if left_distance < right_distance:
            while current:
                if current.root.id == target:
                    return current
                current = current.prev
                if current == self.head:
                    break
        else:
            while current:
                if current.root.id == target:
                    return current
                current = current.next
                if current == self.head:
                    break
        return

    def find_closest(self, target: str) -> Optional[KBucket]:
        current = self.head
        while current:
            left_distance = int(current.root.id, 16) ^ int(target, 16)
            right_distance = int(current.next.root.id, 16) ^ int(target, 16)
            if int(current.root.id, 16) < int(target, 16) < int(current.next.root.id, 16):
                if left_distance < right_distance:
                    return current
                return current.next

            if current.next == self.head:
                if left_distance <= right_distance:
                    return current
                return current.next

            current = current.next

    def reverse(self) -> None:
        tmp = None
        current = self.head
        while current:
            tmp = current.prev
            current.prev = current.next
            current.next = tmp
            current = current.prev
            if current == self.head:
                break
        if tmp:
            self.head = tmp.prev

    def remove_duplicates(self) -> None:
        current = self.head
        seen = dict()
        while current:
            if current.root.id not in seen:
                seen[current.root.id] = 1
                current = current.next
            else:
                nxt = current.next
                self.delete_bucket(current)
                current = nxt
            if current == self.head:
                return

    def split_list(self):
        size = len(self)
        if size == 0:
            return None
        if size == 1:
            return self.head
        mid = size // 2
        count = 0
        prev = None
        current = self.head
        while current and count < mid:
            count += 1
            prev = current
            current = current.next

        prev.next = self.head
        split_cll = BucketList()
        while current.next != self.head:
            split_cll.append(current)
            current = current.next
        split_cll.append(current)
        return split_cll

    def sort(self):
        nodes = []
        current = self.head
        while current:
            for node in current.inorder():
                nodes.append(node)
            current = current.next
            if current == self.head:
                break
        nodes = quick_sort(nodes)

        bucketlist = BucketList()
        for i in range(0, len(nodes), self.k_nodes):
            chunk = nodes[i:i+self.k_nodes]
            random.shuffle(chunk)
            bucket = KBucket()
            for node in chunk:
                bucket.add(node.copy())
            bucketlist.append(bucket)
        return bucketlist

    def list(self) -> List[KBucket]:
        buckets = []
        current = self.head
        while current:
            buckets.append(current)
            current = current.next
            if current == self.head:
                return buckets

    def list_nodes(self) -> List[Node]:
        nodes = []
        current = self.head
        while current:
            for node in current.inorder():
                nodes.append(node)
            current = current.next
            if current == self.head:
                break
        return nodes

    def as_tuples(self) -> List[Tuple[str, int]]:
        current = self.head
        tuples = []
        while current:
            tuples += [node.as_tuple() for node in current.preorder()]
            current = current.next
            if current == self.head:
                break

        return tuples

    def print_list(self) -> None:
        current = self.head
        while current:
            print(current.root.id)
            current = current.next
            if current == self.head:
                break
