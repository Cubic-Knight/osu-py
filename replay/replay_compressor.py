import lzma
import struct
import hashlib
from .replay_classes import *
from ..globals import osu_fp
from my_tools import complete_path

TYPE_LENGTH = {
        "byte": 1,
        "short": 2,
        "int": 4,
        "long": 8
    }


def compress_array(array):
    formatted_array = "".join([(
        f"{array[i].time}|{array[i].x:.7g}|{array[i].y:.7g}|{array[i].action},"
    ) for i in range(len(array))])

    replay_hash = hashlib.md5( bytes(formatted_array, "ascii") ).hexdigest()

    return lzma.compress(bytes(formatted_array, "ascii"), lzma.FORMAT_ALONE, -1, None, [
        {"id": lzma.FILTER_LZMA1, "mode": lzma.MODE_NORMAL,
         "lc": 3, "lp": 0, "pb": 2, "preset": 2, "dict_size": 1 << 21}
    ]), replay_hash


def uleb128(num):
    output = []
    while num > 0:
        output.append(num % 0x80 + 0x80)
        num >>= 7
    output[-1] -= 0x80

    return bytes(output)


def compress_string(string):
    if string == "":
        return bytes([0x00])

    return bytes([0x0b]) + uleb128(len(string)) + bytes(string, "utf-8")


def little_endian(num, length):
    output = []
    for i in range(length):
        output.append(num % 0x100)
        num >>= 8

    return bytes(output)


def double(num):
    return struct.pack('d', num)


def compress_replay(replay: Replay, output_path=None):
    # Reformat mod list to an integer
    mods = sum( 1 << i for i, mod in MODS_INDEX_TO_STR.items() if mod in replay.mods )

    # Reformat life graph dictionary to a string
    life_graph = "".join( f"{time}|{health:n}," for time, health in replay.lifeGraph.items() )

    # Compress the array early to get its length
    compressed_array, replay_hash = compress_array(replay.replay)
    replay_length = len(compressed_array)
    # If replayHash is not set, give it a hash
    if replay.replayHash is None:
        replay.replayHash = replay_hash

    compressed_replay = b''
    for data_name, data_type in DATA_TYPES.items():
        data = getattr(replay, data_name)
        if data is None:
            continue

        if data_name == "lifeGraph":  # Overrides since it's already computed
            data = life_graph
        if data_name == "mods":  # Overrides since it's already computed
            data = mods
        if data_name == "replayLength":  # Overrides since it's already computed
            data = replay_length

        if data_type in TYPE_LENGTH:  # For number values (byte, short, int and long)
            compressed_replay += little_endian(data, TYPE_LENGTH[data_type])

        elif data_type == "str":
            compressed_replay += compress_string(data)

        elif data_type == "array":
            compressed_replay += compressed_array

        elif data_type == "double":
            compressed_replay += double(data)

        else:
            pass

    if output_path is None:
        return compressed_replay

    # Create the file
    output_path = complete_path(output_path, root=osu_fp.get(), folder="Replays\\", extension=".osr")
    with open(output_path, 'wb') as output_file:
        output_file.write(compressed_replay)
