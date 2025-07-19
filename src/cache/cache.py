from abc import ABC, abstractmethod
import struct


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


class DirectMappedCache(Memory):
    def __init__(self, block_id_bits):
        self.blocks_no = pow(2, block_id_bits)
