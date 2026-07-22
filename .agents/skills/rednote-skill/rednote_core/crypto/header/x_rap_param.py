"""x-rap-param header generation — exact port of RedCrack header/X_Rap_Param.py.

x-rap-param is a binary protocol packet containing encrypted device fingerprint data
for risk assessment. Only generated for specific URLs (homefeed, search, user_posted, feed, comment/post).

Structure:
  [36-byte header] [random_str (4-6 bytes)] [encrypted_aes_key] [encrypted_payload]
  → all standard base64 encoded

The payload is:
  1. Fingerprint dict → serialized binary records
  2. XOR'd with derived key
  3. encrypted with fixed_block_cipher

Needs: serialize_fingerprint_payload.py and fixed_block_cipher.py from RedCrack.
"""

from __future__ import annotations

import random
import string
import struct
import time
import base64 as std_base64
import json

from rednote_core.crypto.config import XRAP_ENCRYPT_URLS

ALPHABET = string.ascii_lowercase + string.digits


# ---------------------------------------------------------------------------
# Minimal xxh32 (if xxhash not available)
# ---------------------------------------------------------------------------
try:
    import xxhash as _xxhash_mod

    def _xxh32(data: bytes | str, seed: int = 0) -> int:
        data = data.encode() if isinstance(data, str) else data
        return _xxhash_mod.xxh32(data, seed=seed).intdigest()

except ImportError:
    # Fallback: use Python's built-in hash (NOT the same, but avoids hard dependency)
    import hashlib

    def _xxh32(data: bytes | str, seed: int = 0) -> int:
        data = data.encode() if isinstance(data, str) else data
        h = hashlib.md5(data).digest()
        return struct.unpack("<I", h[:4])[0]


# ---------------------------------------------------------------------------
# Fixed block cipher (encrypt_bytes_with_length + xor_repeating)
# ---------------------------------------------------------------------------


def _u32(value: int) -> int:
    return value & 0xFFFFFFFF


def _to_bytes(data: bytes | bytearray | str | list[int]) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, str):
        return data.encode("latin1")
    return bytes(x & 0xFF for x in data)


def xor_repeating(data: bytes | bytearray | str | list[int], key: bytes | bytearray | str | list[int]) -> bytes:
    data_bytes = _to_bytes(data)
    key_bytes = _to_bytes(key)

    if len(data_bytes) == 0:
        return b""
    if len(data_bytes) < len(key_bytes):
        raise ValueError("error7")

    return bytes(value ^ key_bytes[index % len(key_bytes)] for index, value in enumerate(data_bytes))


# Fixed cipher tables (from RedCrack fixed_cipher_tables.json)
# These are loaded lazily from the JSON file bundled with the module
import importlib.resources as _resources
import json as _json

_FIXED_CIPHER_TABLES: tuple[list[list[int]], list[list[int]]] | None = None


def _load_fixed_cipher_tables() -> tuple[list[list[int]], list[list[int]]]:
    global _FIXED_CIPHER_TABLES
    if _FIXED_CIPHER_TABLES is not None:
        return _FIXED_CIPHER_TABLES

    table_text = _resources.files(__package__).joinpath("fixed_cipher_tables.json").read_text(encoding="utf-8")
    data = _json.loads(table_text)
    round_keys = [[_u32(x) for x in row] for row in data["roundKeys"]]
    tables = [[_u32(x) for x in row] for row in data["tables"]]
    _FIXED_CIPHER_TABLES = (round_keys, tables)
    return _FIXED_CIPHER_TABLES


def encrypt_bytes_with_length(data: bytes | bytearray | str | list[int]) -> bytes:
    """Exact port of RedCrack fixed_block_cipher.encrypt_bytes_with_length."""
    data_bytes = _to_bytes(data)
    round_keys, tables = _load_fixed_cipher_tables()

    blocks = (len(data_bytes) + 15) // 16
    out = bytearray()

    for block_index in range(blocks):
        block = data_bytes[block_index * 16 : block_index * 16 + 16]
        block = block + b"\x00" * (16 - len(block))

        state = [0, 0, 0, 0]
        for col in range(4):
            offset = col << 2
            word = (
                (block[offset] << 24)
                | (block[offset + 1] << 16)
                | (block[offset + 2] << 8)
                | block[offset + 3]
            )
            state[col] = _u32(word ^ round_keys[0][col])

        for round_index in range(1, 10):
            next_state = [0, 0, 0, 0]
            for col in range(4):
                next_state[col] = _u32(
                    tables[0][(state[col] >> 24) & 0xFF]
                    ^ tables[1][(state[(col + 1) & 3] >> 16) & 0xFF]
                    ^ tables[2][(state[(col + 2) & 3] >> 8) & 0xFF]
                    ^ tables[3][state[(col + 3) & 3] & 0xFF]
                    ^ round_keys[round_index][col]
                )
            state = next_state

        sbox = tables[4]
        final_round = round_keys[10]
        final_block = bytearray(16)

        for col in range(4):
            key = final_round[col]
            base = col << 2
            final_block[base] = (sbox[(state[col] >> 24) & 0xFF] ^ (key >> 24)) & 0xFF
            final_block[base + 1] = (sbox[(state[(col + 1) & 3] >> 16) & 0xFF] ^ (key >> 16)) & 0xFF
            final_block[base + 2] = (sbox[(state[(col + 2) & 3] >> 8) & 0xFF] ^ (key >> 8)) & 0xFF
            final_block[base + 3] = (sbox[state[(col + 3) & 3] & 0xFF] ^ key) & 0xFF

        out.extend(final_block)

    out.extend(len(data_bytes).to_bytes(4, "big"))
    return bytes(out)


# ---------------------------------------------------------------------------
# Fingerprint payload serialization
# ---------------------------------------------------------------------------

VAR88 = "dc9cf1d927716ce4e2282c04a4d79d778c34ac7d8642496ab2a2ea2de0b5969b41874b79da271796784ca77cacb7a001ac425df6f2864375b7c04474443ba2ff441e162e24b33181561a057d9f12859d056ff9c8aabe50cd8082b204189039c844973347fd57aa26e027531b10cd4c1d914bde1bb294814309a86dd604e507f7"

ORDER = [
    "Timestamp", "Xorkeyverifyvalue", "Uuid", "RequestHash",
    "PhantomjsV1", "PhantomjsV2", "ChromedriverV1", "ChromedriverV2", "ChromedriverV3", "ChromedriverV4",
    "CDPV1", "UndetectedChromeDriverV1", "PlayWrightV1", "PlayWrightV2", "PlayWrightV3",
    "CrawleeV1", "CefBrowserV1", "PuppteerV1", "SeleniumV1", "BrowserUseV1",
    "DrissionRunV1", "AnonymousReadyStateV1", "DrissionAutomationV1", "DrissionAutomationV2",
    "FieldAbnormal", "isStealthV1", "isCodeBeautify", "stealthJs",
    "MouseBaseX", "MouseBaseY", "MouseBaseTime", "MouseData",
    "TouchData", "KeyboardData", "WheelData", "FocusBaseTime", "FocusData", "VisibilityData",
    "WindowBaseWidth", "WindowBaseHeight", "WindowBaseTime", "WindowResizeData",
    "WheelIsTrusted", "SignCostTime",
    "HpIconCloseClick", "HpIconSearchClick", "HpIconInputClick", "HpChannelClick", "HpFilterClick", "HpCreatorTabClick",
]

TAG_ID = {
    "Timestamp": 1000, "Xorkeyverifyvalue": 1001, "Uuid": 1002, "RequestHash": 1003,
    "PhantomjsV1": 1051, "PhantomjsV2": 1052, "ChromedriverV1": 1053, "ChromedriverV2": 1054,
    "ChromedriverV3": 1055, "ChromedriverV4": 1056, "CDPV1": 1057, "UndetectedChromeDriverV1": 1058,
    "PlayWrightV1": 1059, "PlayWrightV2": 1060, "PlayWrightV3": 1061, "CrawleeV1": 1062,
    "CefBrowserV1": 1063, "PuppteerV1": 1064, "SeleniumV1": 1065, "DrissionRunV1": 1066,
    "AnonymousReadyStateV1": 1067, "DrissionAutomationV1": 1068, "DrissionAutomationV2": 1069,
    "BrowserUseV1": 1070, "isStealthV1": 1071, "isCodeBeautify": 1072, "stealthJs": 1073,
    "MouseBaseX": 1075, "MouseBaseY": 1076, "MouseBaseTime": 1077, "MouseData": 1078,
    "TouchData": 1082, "KeyboardData": 1084, "WheelData": 1088, "FocusBaseTime": 1089,
    "FocusData": 1090, "SignCostTime": 1091, "WindowBaseWidth": 1092, "WindowResizeData": 1093,
    "WindowBaseHeight": 1094, "WindowBaseTime": 1095, "WheelIsTrusted": 1096, "VisibilityData": 1097,
    "FieldAbnormal": 1100, "HpIconCloseClick": 1151, "HpIconSearchClick": 1152, "HpIconInputClick": 1153,
    "HpChannelClick": 1154, "HpFilterClick": 1155, "HpCreatorTabClick": 1156,
}

TYPE_BY_NAME = {
    "Timestamp": "u64", "Xorkeyverifyvalue": "u32", "Uuid": "bytes", "RequestHash": "u32",
    "MouseBaseX": "u32", "MouseBaseY": "u32", "MouseBaseTime": "u64", "MouseData": "bytes",
    "TouchData": "bytes", "KeyboardData": "bytes", "WheelData": "bytes",
    "FocusBaseTime": "u64", "FocusData": "bytes", "VisibilityData": "bytes",
    "WindowBaseWidth": "u32", "WindowResizeData": "bytes", "WindowBaseHeight": "u32",
    "WindowBaseTime": "u64", "SignCostTime": "bytes", "FieldAbnormal": "bytes",
}

INT_PACK = {
    "u8": (">HB", 0xFF),
    "u16": (">HH", 0xFFFF),
    "u32": (">HI", 0xFFFFFFFF),
    "u64": (">HQ", 0xFFFFFFFFFFFFFFFF),
}


def _to_bytes_generic(value) -> bytes:
    """Convert value to bytes — exact port of serialize to_bytes."""
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray, list)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("latin1")
    raise TypeError(f"unsupported bytes value: {type(value)!r}")


def _pack_mouse_events(value: dict) -> bytes:
    return b"".join(
        struct.pack(
            ">hhHB",
            int(e.get("dx", e.get("deltaX", 0))),
            int(e.get("dy", e.get("deltaY", 0))),
            int(e.get("dt", e.get("deltaTime", 0))) & 0xFFFF,
            int(e.get("type", e.get("eventType", 0))) & 0xFF,
        )
        for e in value.get("events", [])
    )


def _pack_focus_events(value: dict) -> bytes:
    return b"".join(
        struct.pack(
            ">BH",
            int(e.get("type", e.get("eventType", 0))) & 0xFF,
            int(e.get("dt", e.get("deltaTime", 0))) & 0xFFFF,
        )
        for e in value.get("events", [])
    )


def _pack_sign_cost(value: dict) -> bytes:
    return struct.pack(">Hh", int(value["signCost"]) & 0xFFFF, int(value["transformCost"]))


_SPECIAL_BYTES_PACKER = {
    "MouseData": _pack_mouse_events,
    "FocusData": _pack_focus_events,
    "SignCostTime": _pack_sign_cost,
}


def _pack_bytes_field(name: str, value) -> bytes:
    packer = _SPECIAL_BYTES_PACKER.get(name)
    return packer(value) if packer and isinstance(value, dict) else _to_bytes_generic(value)


def _xorkey_from_timestamp(timestamp) -> bytes:
    timestamp_bytes = struct.pack(">Q", int(timestamp) & 0xFFFFFFFFFFFFFFFF)
    idx = _xxh32(timestamp_bytes) % len(VAR88)
    return VAR88[idx].encode("latin1")


def _normalize_xorkey(xorkey, timestamp) -> bytes:
    if xorkey is None:
        return _xorkey_from_timestamp(timestamp)
    if isinstance(xorkey, str):
        return xorkey.encode("latin1")
    if isinstance(xorkey, int):
        return bytes([xorkey])
    return bytes(xorkey)


def _build_record(name: str, value) -> bytes:
    tag = TAG_ID[name]
    typ = TYPE_BY_NAME.get(name, "u8")

    if typ == "bytes":
        raw = _pack_bytes_field(name, value)
        return struct.pack(">HI", tag, len(raw)) + raw

    fmt, mask = INT_PACK[typ]
    return struct.pack(fmt, tag, int(value) & mask)


def _validate_full_dict(values: dict) -> None:
    required = [name for name in ORDER if name != "Xorkeyverifyvalue"]
    missing = [name for name in required if name not in values]
    if missing:
        raise KeyError(f"missing required fields: {missing}")


# fflate gzip implementation
try:
    from rednote_core.crypto.header.fflate import gzip_sync as _gzip_sync
except ImportError:
    # Fallback: use standard gzip (may produce slightly different output)
    import gzip as _stdlib_gzip

    def _gzip_sync(data, level=6, mtime=None):
        import time as _time
        if mtime is None:
            mtime = int(_time.time())
        compressed = _stdlib_gzip.compress(data, compresslevel=level)
        # gzip.compress doesn't include mtime in the same way, but it's close enough
        # for most use cases
        return compressed


def _serialize_payload_from_dict(
    values: dict,
    *,
    xorkey=None,
    mtime: int = 0,
    compresslevel: int = 6,
) -> list[int]:
    _validate_full_dict(values)

    key = _normalize_xorkey(xorkey, values["Timestamp"])

    values["Xorkeyverifyvalue"] = _xxh32(key)

    records = [_build_record(name, values[name]) for name in ORDER]
    payload = b"".join(records[:2] + [xor_repeating(record, key) for record in records[2:]])

    return list(_gzip_sync(payload, level=compresslevel, mtime=mtime))


# ---------------------------------------------------------------------------
# Fingerprint builder (minimal subset for v1)
# ---------------------------------------------------------------------------


def _build_fingerprint_payload(uri: str, data: dict | None = None, now_ms: int = 0) -> list[int]:
    """Build fingerprint payload — port of XHS_XRapParam_Encrypt._build_fingerprint_payload."""
    if uri.startswith("https:"):
        uri = uri[6:]

    if data is not None:
        data_str = json.dumps(data, separators=(",", ":"))
        uri = uri + data_str

    if now_ms == 0:
        now_ms = int(time.time() * 1000)
    now_ms = now_ms - random.randint(10, 100)

    fp = {
        "AnonymousReadyStateV1": 0,
        "BrowserUseV1": 0,
        "CDPV1": 0,
        "CefBrowserV1": 0,
        "ChromedriverV1": 0,
        "ChromedriverV2": 0,
        "ChromedriverV3": 0,
        "ChromedriverV4": 0,
        "CrawleeV1": 0,
        "DrissionAutomationV1": 0,
        "DrissionAutomationV2": 0,
        "DrissionRunV1": 0,
        "FieldAbnormal": "",
        "FocusData": {"events": [{"type": 0, "dt": 0}, {"type": 1, "dt": 5621}]},
        "HpChannelClick": 0,
        "HpCreatorTabClick": 0,
        "HpFilterClick": 0,
        "HpIconCloseClick": 0,
        "HpIconInputClick": 0,
        "HpIconSearchClick": 0,
        "KeyboardData": "",
        "MouseBaseX": 484,
        "MouseBaseY": 121,
        "MouseData": {
            "events": [
                {"dx": 1, "dy": 0, "dt": 0, "type": 235},
                {"dx": 0, "dy": 0, "dt": 0, "type": 1},
                {"dx": 1, "dy": -3, "dt": 68, "type": 239},
                {"dx": -7, "dy": -3, "dt": 21, "type": 1},
                {"dx": -262, "dy": -30, "dt": 808, "type": 156},
                {"dx": -174, "dy": -13, "dt": 752, "type": 2},
            ]
        },
        "PhantomjsV1": 0,
        "PhantomjsV2": 0,
        "PlayWrightV1": 0,
        "PlayWrightV2": 0,
        "PlayWrightV3": 0,
        "PuppteerV1": 0,
        "RequestHash": _xxh32(uri, seed=0),
        "SeleniumV1": 0,
        "SignCostTime": {"signCost": random.randint(10, 40), "transformCost": -1},
        "TouchData": "",
        "UndetectedChromeDriverV1": 0,
        "Uuid": "joiamkprgeyi238i",
        "VisibilityData": "",
        "WheelData": "",
        "WheelIsTrusted": 0,
        "WindowBaseHeight": 1106,
        "WindowBaseWidth": 486,
        "WindowResizeData": "",
        "isCodeBeautify": 0,
        "isStealthV1": 0,
        "stealthJs": 0,
    }

    max_mouse_dt = max(e["dt"] for e in fp["MouseData"]["events"])
    max_focus_dt = max(e["dt"] for e in fp["FocusData"]["events"])

    fp.update({
        "Timestamp": str(now_ms),
        "MouseBaseTime": str(now_ms - max_mouse_dt - random.randint(50, 300)),
        "FocusBaseTime": str(now_ms - max_focus_dt - random.randint(100, 1000)),
        "WindowBaseTime": str(now_ms - random.randint(30_000, 20 * 60_000)),
    })

    return _serialize_payload_from_dict(fp, mtime=int(now_ms // 1000))


def _build_header(meta: dict) -> bytes:
    return struct.pack(
        ">BBBBIIIIIIII",
        (meta["protocolVersion"] << 2) + 3,
        meta["headerLen"],
        meta["protocolCryptType"],
        meta["randomStrLength"],
        meta["protocolCryptVersion"],
        meta["keyLength"],
        meta["payloadLen"],
        meta["bodyhash"],
        meta["sdkVersion"],
        meta["bodyEncryTime"],
        meta["flags"],
        meta["trailerLen"],
    )


def generate_x_rap_param(url: str, data: str | dict | None = None) -> str | None:
    """Generate x-rap-param header — exact port of XHS_XRapParam_Encrypt.encrypt_headers_xrap_param.

    Only generates for URLs in XRAP_ENCRYPT_URLS.

    Args:
        url: Full request URL
        data: Request body (str or dict)

    Returns:
        x-rap-param header value, or None if this URL doesn't need one
    """
    if url not in XRAP_ENCRYPT_URLS:
        return None

    if isinstance(data, str) and data.strip():
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            data = None

    finish_ts = int(time.time() * 1000)
    raw_payload = _build_fingerprint_payload(url, data, finish_ts)

    aes_key = _rand_str(16).encode("latin1")
    encrypted_aes_key = encrypt_bytes_with_length(aes_key)
    pre_encrypt = xor_repeating(raw_payload, aes_key)
    encrypted_payload = encrypt_bytes_with_length(pre_encrypt)

    random_string = _rand_str(random.randint(4, 6))

    payload_body = list(random_string.encode("latin1")) + list(encrypted_aes_key) + list(encrypted_payload)

    header_meta = {
        "protocolVersion": 1,
        "headerLen": 36,
        "protocolCryptType": 1,
        "randomStrLength": len(random_string),
        "protocolCryptVersion": 1,
        "keyLength": len(encrypted_aes_key),
        "payloadLen": len(encrypted_payload),
        "bodyhash": _xxh32(bytes(payload_body), seed=0),
        "sdkVersion": 10300,
        "bodyEncryTime": random.randint(100, 500),
        "flags": 0,
        "trailerLen": 0,
    }
    header = _build_header(header_meta)

    packet = list(header) + payload_body
    return std_base64.b64encode(bytes(packet)).decode()


def _rand_str(length: int) -> str:
    return "".join(random.choice(ALPHABET) for _ in range(length))
