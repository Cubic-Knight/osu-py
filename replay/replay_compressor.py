import lzma
import struct
import hashlib
from .replay_classes import *
from ..helpers import osu_fp, complete_path

LZMA_CONFIG = [
    lzma.FORMAT_ALONE,
    -1,
    None,
    [
        {
            "id": lzma.FILTER_LZMA1,
            "mode": lzma.MODE_NORMAL,
            "lc": 3,
            "lp": 0,
            "pb": 2,
            "preset": 2,
            "dict_size": 1 << 21
        }
    ]
]


def compress_array(array: list[ReplayFrame]) -> tuple[bytes, str]:
    formatted_array = "".join(
        f"{frame.time}|{frame.x:.7g}|{frame.y:.7g}|{frame.action},"
        for frame in array
    )
    encoded = bytes(formatted_array, "ascii")
    return lzma.compress(encoded, *LZMA_CONFIG), hashlib.md5(encoded).hexdigest()


def uleb128(num: int) -> bytes:
    output = []
    while num > 0:
        output.append(num % 0x80 + 0x80)
        num >>= 7
    output[-1] -= 0x80
    return bytes(output)


def compress_string(string: str) -> bytes:
    if string == "": return bytes([0x00])
    return bytes([0x0b]) + uleb128(len(string)) + bytes(string, "utf-8")


def format_number(num: float, format: str) -> bytes:
    return struct.pack(f"<{format}", num)


def compress_replay(replay: Replay, output_path=None) -> bytes:
    # Reformat mod list to an integer
    mods = sum(
        1 << i
        for i, mod in MODS_INDEX_TO_STR.items()
        if mod in replay.mods
    )

    # Reformat life graph dictionary to a string
    life_graph = "".join(
        f"{time}|{health:n},"
        for time, health in replay.lifeGraph.items()
    )

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

        # Override already computed data
        if data_name == "lifeGraph": data = life_graph
        if data_name == "mods": data = mods
        if data_name == "replayLength": data = replay_length

        if data_type in NUMBER_TYPES:  # For number values (byte, short, int and long)
            compressed_replay += format_number(data, NUMBER_TYPES[data_type])
        elif data_type == "str":
            compressed_replay += compress_string(data)
        elif data_type == "array":
            compressed_replay += compressed_array

    if output_path is not None:
        # Write the return value to a file
        output_path = complete_path(output_path, root=osu_fp.get(), folder="Replays\\", ext=".osr")
        with open(output_path, 'wb') as output_file:
            output_file.write(compressed_replay)
    return compressed_replay
