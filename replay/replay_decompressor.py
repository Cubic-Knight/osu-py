import lzma
import struct
from .replay_classes import *
from my_tools import complete_path
from ..globals import osu_fp

file_bytes = []  # This var is global because it is used in all functions

TYPE_LENGTH = {
    "byte": 1,
    "short": 2,
    "int": 4,
    "long": 8
}


def get_int(offset, length):
    result = 0
    for byte in file_bytes[offset + length - 1:offset - 1:-1]:
        result <<= 8
        result += byte
    return result, length


def get_length(offset):
    if file_bytes[offset] > 0x7f:
        tmp_length, tmp_str_offset = get_length(offset + 1)
        return (tmp_length << 7) + file_bytes[offset] - 0x80, tmp_str_offset + 1
    else:
        return file_bytes[offset], 2


def get_string(offset):
    if file_bytes[offset] == 0x0b:
        length, string_offset = get_length(offset + 1)
        return "".join([chr(i) for i in file_bytes[offset + string_offset:offset + string_offset + length]]), \
               string_offset + length
    else:
        return "", 1


def get_array(offset, length):
    decompressed_array = lzma.decompress(bytes(file_bytes[offset:offset + length]))
    return "".join([chr(i) for i in decompressed_array])


def get_double(offset):
    value = bytearray( file_bytes[offset:offset+8] )
    if len(value) == 8:
        double, = struct.unpack("d", value)  # struct.unpack returns a 1-tuple, so it is unpacked by the comma
        return double, 8

    else:
        return None, 0


def decompress_replay(path):
    """
    decompress_replay(path) -> dict

    :param path: The absolute path to the replay file (.osr). Can also be the path relative to the "Replays" folder
    """
    global file_bytes

    path = complete_path(path, root=osu_fp.get(), folder="Replays\\", extension=".osr")
    with open(path, 'rb') as file:
        file_bytes = [i for i in file.read()]

    replay_data = []
    offset = 0
    for data_name, data_type in DATA_TYPES.items():
        if data_type in TYPE_LENGTH:  # For number values (byte, short, int and long)
            data, data_length = get_int(offset, TYPE_LENGTH[data_type])

        elif data_type == "str":
            data, data_length = get_string(offset)

        elif data_type == "array":
            data, data_length = get_array(offset, replay_data[-1]), replay_data[-1]

        elif data_type == "double":
            data, data_length = get_double(offset)

        else:
            data, data_length = None, 0

        replay_data.append(data)
        offset += data_length

    return Replay(*replay_data)
