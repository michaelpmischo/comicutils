#!/usr/bin/env python3
import struct


HDR_MARK, HDR_MAIN, HDR_FILE, HDR_SERVICE, HDR_CRYPT, HDR_END, HDR_UNKNOWN = (
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0xff)

(HDR3_MARK, HDR3_MAIN, HDR3_FILE, HDR3_CMT, HDR3_AV, HDR3_OLDSERVICE,
 HDR3_PROTECT, HDR3_SIGN, HDR3_SERVICE, HDR3_ENDARC) = (
    0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7a, 0x7b)

class Block:
    def __init__(self, data_in: bytes, length_in: int = None):
        if length_in is not None:
        self.__length = length_in if length_in is not None else len(data_in)
        self._data = data_in[:self.__length]

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def length(self) -> int:
        return self.__legnth

    # Variable length integer. Can include one or more bytes, where lower 7
    # bits of every byte contain integer data and highest bit in every byte
    # is the continuation flag. If highest bit is 0, this is the last byte
    # in sequence. So first byte contains 7 least significant bits of integer
    # and continuation flag. Second byte, if present, contains next 7 bits
    # and so on.
    def _vint(self, offset_in: int) -> int:
        """
        Variable length integer. Can include one or more bytes, where lower 7
        bits of every byte contain integer data and highest bit in every byte
        is the continuation flag. If highest bit is 0, this is the last byte in
        sequence. So first byte contains 7 least significant bits of integer
        and continuation flag. Second byte, if present, contains next 7 bits
        and so on.

        :param offset_in: offset into the block where the vint begins.
        :return: The int value of the vint.
        """
        value = 0
        for shift in range(10):
            try:
                value = value | ((int.from_bytes(
                    self._data[offset_in:offset_in + shift + 1],
                    "little",
                    signed=False) & (0x7f << (shift * 8))) >> shift)
                if not struct.unpack_from("B", self._data[offset_in:offset_in + shift + 1], shift) & 0x80:
                    return value
            except IndexError as _:
                return value

    def _vint_length(self, offset_in: int) -> int:
        """
        Variable length integer. Can include one or more bytes, where lower 7
        bits of every byte contain integer data and highest bit in every byte
        is the continuation flag. If highest bit is 0, this is the last byte in
        sequence. So first byte contains 7 least significant bits of integer
        and continuation flag. Second byte, if present, contains next 7 bits
        and so on.

        :param offset_in: offset into the block where the vint begins.
        :return: The length (in bytes) of the vint.
        """
        for shift in range(30000):
            try:
                if not struct.unpack_from("B", bytes_in, shift):
                    return shift + 1
            except IndexError as _:
                return shift + 1


class Header(Block):
    def __init__(self, data_in: bytes, length_in: int = None):
        super().__init__(data_in, length_in)

    @property
    def CRC32(self) -> int:
        return int.from_bytes(self._data[:4], "little")

    @CRC32.setter
    def CRC32(self, crc_in: int):
        struct.pack_into("<L", self._data, 0)

    @property
    def size(self) -> int:
        return self._vint(4)

    @property
    def type(self) -> int:
        return struct.unpack_from("<L", self._data, 4 + self._vint_length(4))[0]

    @property
    def flags(self) -> int:
        return struct.unpack_from("<L", self._data, 5 + self._vint_length(4))[0]

    @property
    def extra_size(self) -> int:
        return self._vint(7 + self._vint_length(4))

    @property
    def data_size(self) -> int:
        return self._vint(7 + self._vint_length(4))

    @property
    def extra(self) -> int:
        return self._vint(self._data[4:])

    @property
    def data(self) -> int:
        return self._vint(self._data[4:])


class RarFile:
    GENERAL_ARCHIVE_BLOCK_FORMAT = ["<L", self.vint, self.vint, self.vint, self.vint, self.vint]
