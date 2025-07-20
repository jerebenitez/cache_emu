import struct
import numpy
import math
from enum import Enum
from abc import ABC, abstractmethod

# TODO: Move things from Memory to memory.py
# TODO: Write tests for caches
# TODO: Implement write back
# TODO: Implement fully associative
# TODO: Implement set-associative
# TODO: Implement coherency, test from multiple threads
# TODO: Write examples to show how it works
# TODO: emit events or smth when hit or misses occur


class AddressViolationError(Exception):
    pass


class Memory(ABC):
    @abstractmethod
    def read(self, address):
        pass

    @abstractmethod
    def write(self, data, address):
        pass


class FileMainMemory(Memory):
    def __init__(self, file_name, size):
        self._file_name = file_name
        self._size = size

        try:
            with open(file_name, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            data = b""

        if len(data) < size:
            data += bytes(size - len(data))
        elif len(data) > size:
            data = data[:size]

        self.storage = bytearray(data)

        with open(file_name, "wb") as f:
            f.write(self.storage)

    def read(self, address):
        if address % 8 != 0 or address + 8 > self._size:
            raise AddressViolationError(f"invalid address {address}")

        return struct.unpack_from("<Q", self.storage, address)[0]

    def write(self, data, address):
        if address % 8 != 0 or address + 8 > self._size:
            raise AddressViolationError(f"invalid address {address}")

        struct.pack_into("<Q", self.storage, address, data)
        with open(self._file_name, "wb") as f:
            f.write(self.storage)


class CacheLineType(Enum):
    DATA = 1
    INSTRUCTION = 2


class CacheLine:
    def __init__(self, block_size):
        self.flags = {
            "valid": False,
            "type": CacheLineType.DATA,
            "dirty": False,
            "lock": False
        }
        self.tag = None
        self.blocks = numpy.empty(block_size, numpy.uint64)


class DirectMappedCache(Memory):
    def __init__(self, lower_level: Memory, num_lines: int, block_size: int):
        self.lower_level = lower_level
        self.block_size = block_size
        self.num_lines = num_lines

        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(num_lines))
        self.tag_bits = 64 - self.offset_bits - self.index_bits

        self.memory = [CacheLine(block_size) for _ in range(num_lines)]

    def read(self, address):
        tag, line_id, block_id = self._unpack_address(address)
        line = self.memory[line_id]

        if line.flags["valid"] and line.tag == tag:
            # Hit!
            return line.blocks[block_id]
        else:
            # Miss!
            block_address = address - block_id
            line.blocks = [
                self.lower_level.read(block_address + i * 8)
                for i in range(self.block_size)
            ]
            line.tag = tag
            line.flags["valid"] = True

            return line.blocks[block_id]

    def write(self, data: int, address: int):
        tag, line_id, block_id = self._unpack_address(address)
        line = self.memory[line_id]

        if not (line.flags["valid"] and line.tag == tag):
            # Miss
            # TODO: refactor this, it's the same when a miss occurs on read
            block_address = address - block_id
            line.blocks = [
                self.lower_level.read(block_address + i * 8)
                for i in range(self.block_size)
            ]
            line.tag = tag
            line.flags["valid"] = True

        line.blocks[block_id] = data

        # Write through
        self.lower_level.write(data, address)

    def _unpack_address(self, address: int):
        block_offset = address & ((1 << self.offset_bits) - 1)
        line = (address >> self.offset_bits) & ((1 << self.index_bit) - 1)
        tag = address >> (self.offset_bits + self.index_bits)

        return tag, line, block_offset
