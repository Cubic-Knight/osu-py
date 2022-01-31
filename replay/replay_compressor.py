import lzma
import struct
import hashlib
from .replay_classes import *
from ..helpers import osu_fp, complete_path

LZMA_CONFIG = {
    "id": lzma.FILTER_LZMA1,
    "mode": lzma.MODE_NORMAL,
    "lc": 3,
    "lp": 0,
    "pb": 2,
    "preset": 2,
    "dict_size": 1 << 21
}


def osr_string(string: str) -> bytes:
    if string == "": return bytes([0x00])
    # Determine the uleb128 that corresponds to the length of the string
    str_len = []
    l = len(string)
    while l:
        str_len.append(l % 0x80 + 0x80)
        l >>= 7
    str_len[-1] -= 0x80  # The last byte does not exceed 0x80

    return bytes([0x0b]) + bytes(str_len) + bytes(string, "utf-8")


def compress_replay(replay: Replay, output_path: str = None) -> bytes:
    # Reformat mod list to an integer
    mods = sum(
        1 << i
        for i, mod in MODS_INDEX_TO_STR.items()
        if mod in replay.mods
    )

    # Compress the array early to get its length
    replay_str = "".join(
        f"{frame.time}|{frame.x:.7g}|{frame.y:.7g}|{frame.action},"
        for frame in replay.replay
    ).encode("ascii")
    compressed_array = lzma.compress(replay_str, format=lzma.FORMAT_ALONE, filters=[LZMA_CONFIG])
    replay_hash = hashlib.md5(replay_str).hexdigest() if replay.replayHash is None else replay.replayHash
    replay_length = len(compressed_array)

    # Reformat life graph dictionary to a string
    life_graph = "".join(
        f"{time}|{health:n},"
        for time, health in replay.lifeGraph.items()
    )

    # Encode strings into their .osr format
    beatmap_hash = osr_string(replay.beatmapHash)
    player_name = osr_string(replay.playerName)
    replay_hash = osr_string(replay_hash)
    life_graph = osr_string(life_graph)

    compressed_replay = struct.pack(
        f"<BI{len(beatmap_hash)}s{len(player_name)}s{len(replay_hash)}s6HIHBI{len(life_graph)}sQI{replay_length}sQd",
        replay.gameMode,
        replay.version,
        beatmap_hash,
        player_name,
        replay_hash,
        replay.count300,
        replay.count100,
        replay.count50,
        replay.countGeki,
        replay.countKatu,
        replay.countMiss,
        replay.score,
        replay.maxCombo,
        replay.fullCombo,
        mods,
        life_graph,
        replay.time,
        replay_length,
        compressed_array,
        replay.scoreID,
        replay.additionalModInfo if replay.additionalModInfo is not None else 0.0
    )

    if output_path is not None:
        # Write the return value to a file
        output_path = complete_path(output_path, root=osu_fp.get(), folder="Replays\\", ext=".osr")
        with open(output_path, 'wb') as output_file:
            output_file.write(compressed_replay)
    return compressed_replay
