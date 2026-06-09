"""从谱面封面提取主题色，供渲染桥的 osu! 三角纹主题使用。

整个模块都是「尽力而为」：任何一步失败都返回 None，渲染流程会退回到
默认的 osu! 粉色主题（且不垫 map 背景），绝不影响出图。
"""

from __future__ import annotations

import base64
import colorsys
import io
import re
from pathlib import Path
from urllib.request import Request, urlopen

# osu! 封面资源按清晰度降级尝试：fullsize 才是「真·谱面背景」
_COVER_VARIANTS = ("fullsize.jpg", "cover@2x.jpg", "cover.jpg")
_COVER_HOST = "https://assets.ppy.sh/beatmaps/{set_id}/covers/{variant}"
_USER_AGENT = "astrbot-osu-mania-map-analyser/1.0"

# 垫在 pattern 块后面的封面：缩到这个宽度再编码，控制 payload 体积
_COVER_MAX_WIDTH = 800
_COVER_JPEG_QUALITY = 80

_BEATMAPSET_ID_RE = re.compile(r"(?mi)^\s*BeatmapSetID\s*:\s*(\d+)\s*$")


def build_cover_theme(osu_text: str, cache_dir: Path) -> dict | None:
    """返回 {"accent": "#rrggbb", "coverDataUri": "data:image/jpeg;base64,...",
    "hasCover": True}；任何失败都返回 None。"""

    set_id = _parse_beatmapset_id(osu_text)
    if not set_id:
        return None

    try:
        from PIL import Image
    except Exception:
        return None

    raw = _load_cover_bytes(set_id, cache_dir)
    if not raw:
        return None

    try:
        with Image.open(io.BytesIO(raw)) as im:
            rgb = im.convert("RGB")
            accent = _extract_accent(rgb, Image)
            cover_uri = _encode_cover_data_uri(rgb, Image)
    except Exception:
        return None

    if not accent or not cover_uri:
        return None

    return {
        "accent": accent,
        "coverDataUri": cover_uri,
        "hasCover": True,
    }


def _parse_beatmapset_id(osu_text: str) -> str | None:
    match = _BEATMAPSET_ID_RE.search(osu_text or "")
    if not match:
        return None
    set_id = match.group(1)
    return set_id if set_id and set_id != "-1" else None


def _load_cover_bytes(set_id: str, cache_dir: Path) -> bytes | None:
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        cache_dir = None  # 没有缓存目录也能直接下，只是不落盘

    cached = cache_dir / f"{set_id}.cover" if cache_dir else None
    if cached and cached.is_file() and cached.stat().st_size > 0:
        try:
            return cached.read_bytes()
        except Exception:
            pass

    for variant in _COVER_VARIANTS:
        data = _http_get(_COVER_HOST.format(set_id=set_id, variant=variant))
        if data:
            if cached:
                try:
                    cached.write_bytes(data)
                except Exception:
                    pass
            return data
    return None


def _http_get(url: str) -> bytes | None:
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(request, timeout=15) as response:
            if getattr(response, "status", 200) != 200:
                return None
            data = response.read()
        return data or None
    except Exception:
        return None


def _extract_accent(rgb_image, image_module) -> str | None:
    """挑一个鲜艳、又有代表性的主色。"""
    try:
        small = rgb_image.copy()
        small.thumbnail((110, 110))
        quantized = small.quantize(colors=12, method=image_module.Quantize.MEDIANCUT)
        palette = quantized.getpalette() or []
        color_counts = quantized.getcolors() or []
    except Exception:
        return None

    best_score = -1.0
    best_rgb: tuple[int, int, int] | None = None
    total = sum(count for count, _ in color_counts) or 1

    for count, index in color_counts:
        base = index * 3
        if base + 2 >= len(palette):
            continue
        r, g, b = palette[base], palette[base + 1], palette[base + 2]
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        freq = count / total
        # 偏好：够鲜艳 + 亮度适中（不要纯黑纯白）+ 占比别太小
        brightness_fit = 1.0 - abs(l - 0.55) * 1.4
        brightness_fit = max(brightness_fit, 0.05)
        score = (freq ** 0.5) * (0.25 + s * 1.35) * brightness_fit
        if score > best_score:
            best_score = score
            best_rgb = (r, g, b)

    if best_rgb is None:
        return None

    return _normalize_accent(*best_rgb)


def _normalize_accent(r: int, g: int, b: int) -> str:
    """把主色压进一个「好看且可读」的区间，避免太暗/太灰/太刺眼。"""
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

    if s < 0.15:
        # 近乎灰度的封面：给一点点饱和，让主题呈现「带色调的石板蓝/灰」而非死灰，
        # 但仍贴着封面里本就存在的色相，不凭空造色
        s = max(s, 0.18)
        l = min(max(l, 0.43), 0.56)
    else:
        s = min(max(s, 0.5), 0.9)
        l = min(max(l, 0.46), 0.62)

    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(
        round(nr * 255), round(ng * 255), round(nb * 255)
    )


def _encode_cover_data_uri(rgb_image, image_module) -> str | None:
    try:
        cover = rgb_image
        if cover.width > _COVER_MAX_WIDTH:
            ratio = _COVER_MAX_WIDTH / cover.width
            new_size = (_COVER_MAX_WIDTH, max(1, round(cover.height * ratio)))
            cover = cover.resize(new_size, image_module.Resampling.LANCZOS)

        buffer = io.BytesIO()
        cover.save(buffer, format="JPEG", quality=_COVER_JPEG_QUALITY, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception:
        return None

    return f"data:image/jpeg;base64,{encoded}"
