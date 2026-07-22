"""Browser fingerprint generator — exact port of RedCrack XhsFpGenerator.

Generates an 80+ field browser fingerprint dict for:
  - gid request (profileData encryption)
  - x-s-common header (b1 subset)
  - Per-request fingerprint updates
"""

from __future__ import annotations

import hashlib
import random
import secrets
import time


def _weighted_random_choice(options: list, weights: list) -> str:
    """Weighted random choice, returns string."""
    return f"{random.choices(options, weights=weights, k=1)[0]}"


def _get_renderer_info() -> tuple[str, str]:
    """Return random (vendor, renderer) WebGL strings."""
    renderer_info_list = [
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) HD Graphics 400 (0x00000166) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) HD Graphics 4400 (0x00001112) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) HD Graphics 4600 (0x00000412) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) HD Graphics 520 (0x1912) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) HD Graphics 530 (0x00001912) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) HD Graphics 550 (0x00001512) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) UHD Graphics 620 (0x00003EA0) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E9B) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (Intel)|ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A8) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (NVIDIA)|ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x0000250F) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (NVIDIA)|ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 (0x00002488) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (NVIDIA)|ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002882) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (NVIDIA)|ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002786) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (AMD)|ANGLE (AMD, AMD Radeon RX 6600 (0x000073FF) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "Google Inc. (AMD)|ANGLE (AMD, AMD Radeon Graphics (0x00001636) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    ]
    return random.choice(renderer_info_list).split("|")


def _get_width_and_height() -> tuple[str, str, int | str, int | str]:
    """Return random (width, height, availWidth, availHeight)."""
    width, height = _weighted_random_choice(
        ["1366;768", "1600;900", "1920;1080", "2560;1440", "3840;2160"],
        [0.25, 0.15, 0.35, 0.15, 0.08],
    ).split(";")
    if random.choice([True, False]):
        avail_width = int(width) - int(_weighted_random_choice([0, 30, 60, 80], [0.1, 0.4, 0.3, 0.2]))
        avail_height = height
    else:
        avail_width = width
        avail_height = int(height) - int(_weighted_random_choice([30, 60, 80, 100], [0.2, 0.5, 0.2, 0.1]))
    return width, height, avail_width, avail_height


def get_fingerprint(cookies: dict, user_agent: str) -> dict:
    """Generate full 80+ field browser fingerprint — exact port of XhsFpGenerator.get_fingerprint.

    Args:
        cookies: Current cookie dict (used for x57 cookie_string field)
        user_agent: User-Agent string (used for x1 and x66)

    Returns:
        Full fingerprint dict with x1-x82 fields.
    """
    cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items())
    width, height, avail_width, avail_height = _get_width_and_height()
    is_incognito = _weighted_random_choice(["true", "false"], [0.95, 0.05])
    vendor, renderer = _get_renderer_info()
    x78_y = random.randint(2350, 2450)

    return {
        "x1": user_agent,
        "x2": "false",
        "x3": "zh-CN",
        "x4": _weighted_random_choice([16, 24, 30, 32], [0.05, 0.6, 0.05, 0.3]),
        "x5": _weighted_random_choice([1, 2, 4, 8, 12, 16], [0.10, 0.25, 0.4, 0.2, 0.03, 0.01]),
        "x6": "24",
        "x7": f"{vendor},{renderer}",
        "x8": _weighted_random_choice([2, 4, 6, 8, 12, 16, 24, 32], [0.1, 0.4, 0.2, 0.15, 0.08, 0.04, 0.02, 0.01]),
        "x9": f"{width};{height}",
        "x10": f"{avail_width};{avail_height}",
        "x11": "-480",
        "x12": "Asia/Hong_Kong",
        "x13": is_incognito,
        "x14": is_incognito,
        "x15": is_incognito,
        "x16": "false",
        "x17": "false",
        "x18": "un",
        "x19": "Win32",
        "x20": "",
        "x21": "PDF Viewer,Chrome PDF Viewer,Chromium PDF Viewer,Microsoft Edge PDF Viewer,WebKit built-in PDF",
        "x22": hashlib.md5(secrets.token_bytes(32)).hexdigest(),
        "x23": "false",
        "x24": "false",
        "x25": "false",
        "x26": "false",
        "x27": "false",
        "x28": "0,false,false",
        "x29": "4,7,8",
        "x30": "swf object not loaded",
        "x31": "124.04347527516074",
        "x33": "0",
        "x34": "0",
        "x35": "0",
        "x36": f"{random.randint(1, 20)}",
        "x37": "0|0|0|0|0|0|0|0|0|1|0|0|0|0|0|0|0|0|1|0|0|0|0|0",
        "x38": "0|0|1|0|1|0|0|0|0|0|1|0|1|0|1|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0",
        "x39": 0,
        "x40": "0",
        "x41": "0",
        "x42": "3.5.4",
        "x43": "Canvas not supported",
        "x44": f"{int(time.time() * 1000)}",
        "x45": "__SEC_CAV__1-1-1-1-1|__SEC_WSA__|",
        "x46": "false",
        "x47": "1|0|0|0|0|0",
        "x48": "",
        "x49": "{list:[],type:}",
        "x50": "",
        "x51": "",
        "x52": "",
        "x53": hashlib.md5(secrets.token_bytes(32)).hexdigest(),
        "x54": "11311144241322244122",
        "x55": "380,380,360,400,380,400,420,380,400,400,360,360,440,420",
        "x56": f"{vendor}|{renderer}|{hashlib.md5(secrets.token_bytes(32)).hexdigest()}|35",
        "x57": cookie_string,
        "x58": "180",
        "x59": "2",
        "x60": "63",
        "x61": "1348",
        "x62": "2047",
        "x63": "0",
        "x64": "0",
        "x65": "0",
        "x66": {
            "referer": "",
            "location": "https://www.xiaohongshu.com/explore",
            "frame": 0,
        },
        "x67": "1|0",
        "x68": "0",
        "x69": "326|1292|30",
        "x70": ["location"],
        "x71": "true",
        "x72": "complete",
        "x73": "1191",
        "x74": "0|0|0",
        "x75": "Google Inc.",
        "x76": "true",
        "x77": "1|1|1|1|1|1|1|1|1|1",
        "x78": {
            "x": 0,
            "y": x78_y,
            "left": 0,
            "right": 290.828125,
            "bottom": x78_y + 18,
            "height": 18,
            "top": x78_y,
            "width": 290.828125,
            "font": (
                'system-ui, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", '
                '"Noto Color Emoji", -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, '
                '"Noto Sans", sans-serif, BlinkMacSystemFont, "Helvetica Neue", Arial, '
                '"PingFang SC", "PingFang TC", "PingFang HK", "Microsoft Yahei", "Microsoft JhengHei"'
            ),
        },
        "x79": "144|599565058866",
        "x80": "1|[object FileSystemDirectoryHandle]",
        "x82": "_0x17a2|_0x1954",
    }


def update_fingerprint(fp: dict, cookies: dict, url: str) -> None:
    """Update fingerprint before each request — exact port of XhsFpGenerator.update_fingerprint.

    Updates: x39 (counter), x44 (timestamp), x57 (cookie_string), x66 (location).
    """
    cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items())
    fp.update({
        "x39": 0,
        "x44": f"{time.time() * 1000}",
        "x57": cookie_string,
        "x66": {
            "referer": "https://www.xiaohongshu.com/explore",
            "location": url,
            "frame": 0,
        },
    })
