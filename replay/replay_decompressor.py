import lzma
import struct
from .replay_classes import *
from ..helpers import osu_fp, complete_path


def get_uleb128(offset: int, file_bytes: bytes) -> tuple[int, int]:
    if file_bytes[offset] > 0x7f:
        tmp_length, tmp_str_offset = get_uleb128(offset + 1, file_bytes)
        return (tmp_length << 7) + file_bytes[offset] - 0x80, tmp_str_offset + 1
    else:
        return file_bytes[offset], 1


def decompress_replay(path: str) -> Replay:
    path = complete_path(path, root=osu_fp.get(), folder="Replays\\", ext=".osr")
    with open(path, 'rb') as file:
        file_bytes = file.read()

    # Locate the length of every string beforehand
    str_formats = []
    offset = 0
    for pos in [5, 6, 7, 31]:
        addr = pos + offset
        if file_bytes[addr] == 0x00:
            str_formats.append("x")
        elif file_bytes[addr] == 0x0b:
            str_len, size_of_uleb128 = get_uleb128(addr + 1, file_bytes)
            str_formats.append(f"x{size_of_uleb128}x{str_len}s")
            offset += size_of_uleb128 + str_len
        else:
            raise ValueError

    # Locate the length of the replay beforehand
    replay_length, = struct.unpack("I", file_bytes[40+offset:44+offset])

    f1, f2, f3, f4 = str_formats
    replay_data = struct.unpack(
        f"<BI{f1}{f2}{f3}6HIHBI{f4}QI{replay_length}sQ",
        file_bytes[:52+offset+replay_length]
    )
    additional_mod_info = (
        struct.unpack("d", value)
        if len(value := file_bytes[52+offset+replay_length:]) == 8
        else None
    )

    replay_data = [
        data.decode("utf-8") if i in (2, 3, 4, 15) else data
        for i, data in enumerate(replay_data)
    ]
    replay_data[18] = lzma.decompress(replay_data[18]).decode("utf-8")  # Decompress the replay
    return Replay(*replay_data, additional_mod_info)
