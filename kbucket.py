from typing import Union, Optional, List, Tuple
from utils import Stack, Config
from node import Node
import random
import math


class KBucket:
    def __init__(self):
        self.root:      Optional[Node] = None
        self.next:      Optional[KBucket] = None
        self.prev:      Optional[KBucket] = None
        self.k_nodes:   int = Config.KNodes.value
        self.alpha:     int = Config.Alpha.value

    def add(self, new_node: Node, current: Optional[Node] = None) -> None:
        if not self.root:
            self.root = new_node

        else:
            if not current:
                current = self.root

            if new_node.id < current.id:
                if not current.left:
                    current.left = new_node
                else:
                    self.add(new_node, current.left)

            elif new_node.id > current.id:
                if not current.right:
                    current.right = new_node
                else:
                    self.add(new_node, current.right)
            else:
                return

    def delete(self, node: Node, current: Optional[Node] = None) -> Node:
        if not current:
            current = self.root

        if node.id < current.id:
            current.left = self.delete(node, current.left)

        elif node.id > current.id:
            current.right = self.delete(node, current.right)

        else:
            if not current.left:
                temp = current.right
                return temp

            elif not current.right:
                temp = current.left
                return temp

            temp = self.min(current.right)
            current.id = temp.id
            current.right = self.delete(temp, current.right)

        return current

    def find_node(self, node_id: str, current: Optional[Node] = None) -> Optional[Node]:

        if not current:
            current = self.root

        if not current:
            return None

        if node_id < current.id:
            if current.left:
                return self.find_node(node_id, current.left)
            return None

        elif node_id > current.id:
            if current.right:
                return self.find_node(node_id, current.right)
            return None

        else:
            return current

    def find_closest(self, node_id: str, distance: Optional[Union[float, int]] = math.inf, closest: Optional[Node] = None, current: Optional[Node] = None) -> Node:
        if not current:
            current = self.root

        if distance > int(current.id, 16) ^ int(node_id, 16):
            distance = int(current.id, 16) ^ int(node_id, 16)
            closest = current

        if current.left:
            return self.find_closest(node_id, distance, closest, current.left)

        if current.right:
            return self.find_closest(node_id, distance, closest, current.right)

        return closest

    def find_a_closest(self, node_id: str) -> List[Node]:
        node_ids = [node.id for node in self.inorder()]
        a_closest = []
        for i in range(self.alpha):
            if len(node_ids) > 0:
                closest_index = 0
                closest_distance = math.inf
                for j, nid in enumerate(node_ids):
                    distance = int(nid, 16) ^ int(node_id, 16)
                    if distance < closest_distance:
                        closest_index = j
                        closest_distance = distance

                a_closest.append(self.find_node(node_ids.pop(closest_index)))

        return a_closest

    def min(self, current: Optional[Node] = None) -> Optional[Node]:
        if not current:
            current = self.root
        if current.left:
            return self.min(current.left)
        return current

    def max(self, current: Node = None) -> Optional[Node]:
        if not current:
            current = self.root
        if current.right:
            return self.max(current.right)
        return current

    def height(self) -> int:
        return self._height(self.root)

    def _height(self, current: Optional[Node] = None) -> int:
        if not current:
            return -1

        left_height = self._height(current.left)
        right_height = self._height(current.right)

        return 1 + max(left_height, right_height)

    def size(self, root: Optional[Node] = None) -> int:
        if root:
            return 1 + self.size(root.left) + self.size(root.right) if root else 0

        if not self.root:
            return 0

        stack = Stack()
        stack.push(self.root)
        size = 1
        while stack:
            node = stack.pop()
            if node.left:
                size += 1
                stack.push(node.left)

            if node.right:
                size += 1
                stack.push(node.right)

        return size

    def split(self):
        if not self.root:
            return None
        in_order = self.inorder()
        k1_arr = [peer.copy() for i, peer in enumerate(in_order) if i < len(in_order) // 2]
        k2_arr = [peer.copy() for i, peer in enumerate(in_order) if i >= len(in_order) // 2]
        k1_head = k1_arr.pop(len(k1_arr)//2)
        k2_head = k2_arr.pop(len(k2_arr)//2)
        random.shuffle(k1_arr)
        random.shuffle(k2_arr)
        k1_arr = [k1_head] + k1_arr
        k2_arr = [k2_head] + k2_arr
        k1 = KBucket()
        k2 = KBucket()
        [k1.add(peer) for peer in k1_arr]
        [k2.add(peer) for peer in k2_arr]
        return k1, k2

    def time_heap(self, heap, n, i) -> None:
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2

        if left < n and heap[i].last_seen < heap[left].last_seen:
            largest = left

        if right < n and heap[largest].last_seen < heap[right].last_seen:
            largest = right

        if largest != i:
            heap[i], heap[largest] = heap[largest], heap[i]
            self.time_heap(heap, n, largest)

    def time_sort(self) -> List[Node]:
        heap = self.inorder()
        n = self.size()

        for i in range(n // 2, -1, -1):
            self.time_heap(heap, n, i)

        for i in range(n - 1, 0, -1):
            heap[i], heap[0] = heap[0], heap[i]
            self.time_heap(heap, i, 0)

        return heap

    def oldest(self) -> Node:
        return self.time_sort()[0]

    def preorder(self) -> List[Node]:
        nodes = []
        self._preorder(nodes)
        return nodes

    def _preorder(self, node_list: List[Node], current: Optional[Node] = None) -> None:
        if not current:
            current = self.root
        node_list.append(current)
        if current.left:
            self._preorder(node_list, current.left)
        if current.right:
            self._preorder(node_list, current.right)

    def inorder(self) -> List[Node]:
        nodes = []
        self._inorder(nodes)
        return nodes

    def _inorder(self, node_list: List[Node], current: Optional[Node] = None) -> None:
        if not current:
            current = self.root
        if not current:
            return
        if current.left:
            self._inorder(node_list, current.left)
        node_list.append(current)
        if current.right:
            self._inorder(node_list, current.right)

    def postorder(self) -> List[Node]:
        nodes = []
        self._postorder(nodes)
        return nodes

    def _postorder(self, node_list: List[Node], current: Optional[Node] = None) -> None:
        if not current:
            current = self.root
        if current.left:
            self._postorder(node_list, current.left)
        if current.right:
            self._postorder(node_list, current.right)
        node_list.append(current)

    def as_tuples(self) -> List[Tuple[str, int]]:
        tuples = [node.as_tuple() for node in self.preorder()]
        return tuples
