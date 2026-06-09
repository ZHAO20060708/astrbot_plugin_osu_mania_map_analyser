from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from .browser_runtime import ChromiumRenderRuntime, RenderRequest
from .cover_theme import build_cover_theme
from .downloader import download_beatmap_file
from .errors import ManiaMapAnalyserError, NonManiaBeatmapError


class ManiaMapAnalyserService:
    """把 beatmap 下载、缓存和 Playwright 渲染隔离在 service 层"""

    def __init__(self, plugin_root: Path, render_config: dict[str, Any]) -> None:
        self.plugin_root = plugin_root
        # 使用 plugin_root 的 data 子目录作为数据存储目录
        self.plugin_data_path = plugin_root / "data"
        self.plugin_data_path.mkdir(parents=True, exist_ok=True)
        self.render_settings = self._normalize_render_settings(render_config)
        self.runtime = ChromiumRenderRuntime(static_root=self.plugin_root)

    def generate_from_bid(
        self,
        bid: str,
        render_overrides: dict[str, Any],
        runtime_overrides: dict[str, Any],
    ) -> dict[str, Any]:
        effective_render_settings = dict(self.render_settings)
        effective_render_settings.update(render_overrides)

        effective_runtime = {
            "speedRate": 1.0,
            "odFlag": None,
            "cvtFlag": None,
        }
        effective_runtime.update(runtime_overrides)
        effective_runtime["modSignature"] = (
            f"{effective_runtime['speedRate']:.5f}|"
            f"{effective_runtime['odFlag'] or 'none'}|"
            f"{effective_runtime['cvtFlag'] or 'none'}"
        )

        # 确保输出目录存在
        output_dir = self.plugin_data_path / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{bid}_{uuid4().hex[:16]}.png"

        beatmap_path = download_beatmap_file(
            bid=bid,
            temp_dir=self.plugin_data_path / "osu-download-cache",
        )

        try:
            osu_text = beatmap_path.read_text(encoding="utf-8-sig", errors="replace")
        except Exception as exc:
            raise ManiaMapAnalyserError(f"读取谱面文件失败：{exc}") from exc

        beatmap_mode = self._extract_beatmap_mode(osu_text)
        if beatmap_mode != 3:
            raise NonManiaBeatmapError(
                f"该谱面不是 osu!mania 谱面，无法分析。当前 Mode: {beatmap_mode}"
            )

        payload = {
            "osuText": osu_text,
            "settings": effective_render_settings,
            "runtime": effective_runtime,
            "postRenderDelayMs": 700,
        }

        # 同步调用异步的 build_cover_theme
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在事件循环中，创建新的事件循环
                theme = asyncio.run(build_cover_theme(
                    osu_text=osu_text,
                    cache_dir=self.plugin_data_path / "cover-cache",
                ))
            else:
                theme = loop.run_until_complete(build_cover_theme(
                    osu_text=osu_text,
                    cache_dir=self.plugin_data_path / "cover-cache",
                ))
        except Exception:
            theme = None

        if theme:
            payload["theme"] = theme

        self.runtime.render(
            RenderRequest(
                output_path=output_path,
                payload=payload,
                capture_target=effective_render_settings["captureTarget"],
            )
        )

        return {
            "status": "success",
            "msg": f"rendered chart successfully for bid {bid}",
            "image_path": str(output_path.resolve()),
        }

    def _extract_beatmap_mode(self, osu_text: str) -> int | None:
        match = re.search(r"(?mi)^\s*Mode\s*:\s*(\d+)\s*$", osu_text)
        return int(match.group(1)) if match else None

    def _normalize_render_settings(self, config: dict[str, Any]) -> dict[str, Any]:
        capture_target = str(config["capture_target"]).strip()
        if capture_target not in {"full_card", "graph_only"}:
            capture_target = "full_card"

        return {
            "captureTarget": capture_target,
            "contentBar": str(config["content_bar"]).strip(),
            "srText": str(config["sr_text"]).strip(),
            "diffText": str(config["diff_text"]).strip(),
            "estimatorAlgorithm": str(config["estimator_algorithm"]).strip(),
            "etternaVersion": str(config["etterna_version"]).strip(),
            "companellaEtternaVersion": str(config["companella_etterna_version"]).strip(),
            "enableNumericDifficulty": bool(config["enable_numeric_difficulty"]),
            "enableEtternaRainbowBars": bool(config["enable_etterna_rainbow_bars"]),
            "showModeTagCapsule": bool(config["show_mode_tag_capsule"]),
            "vibroDetection": bool(config["vibro_detection"]),
            "debugUseAmount": bool(config["debug_use_amount"]),
            "useSvDetection": bool(config["debug_use_sv_detection"]),
            "azusaSunnyReferenceHo": bool(config["azusa_sunny_reference_ho"]),
            "cardOpacity": str(config["card_opacity"]).strip(),
            "cardBlur": str(config["card_blur"]).strip(),
            "cardRadius": str(config["card_radius"]).strip(),
        }
