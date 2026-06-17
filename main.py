from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

PLUGIN_ROOT = Path(__file__).resolve().parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from astrbot_service.service_mania_map_analyser import ManiaMapAnalyserService
from astrbot_service.errors import ManiaMapAnalyserError

SCHEMA_PATH = PLUGIN_ROOT / "_conf_schema.json"
SCHEMA_DEFAULTS_SNAPSHOT_PATH = PLUGIN_ROOT / "data" / "schema_defaults_snapshot.json"
LEGACY_SCHEMA_DEFAULTS = {
    "sr_text": ["Auto"],
    "enable_etterna_rainbow_bars": [True],
    "card_blur": ["Soft"],
}


def _load_schema_defaults() -> dict[str, object]:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

    defaults: dict[str, object] = {}
    if isinstance(schema, dict):
        for key, meta in schema.items():
            if isinstance(meta, dict) and "default" in meta:
                defaults[key] = meta["default"]
    return defaults


SCHEMA_DEFAULTS = _load_schema_defaults()


def _load_previous_schema_defaults() -> dict[str, object]:
    try:
        data = json.loads(SCHEMA_DEFAULTS_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


PREVIOUS_SCHEMA_DEFAULTS = _load_previous_schema_defaults()


def _save_schema_defaults_snapshot() -> None:
    try:
        SCHEMA_DEFAULTS_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHEMA_DEFAULTS_SNAPSHOT_PATH.write_text(
            json.dumps(SCHEMA_DEFAULTS, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        return


def _schema_default(key: str, fallback: object) -> object:
    return SCHEMA_DEFAULTS.get(key, fallback)


def _config_value(
    config: AstrBotConfig,
    key: str,
    fallback: object,
) -> tuple[object, bool]:
    schema_default = _schema_default(key, fallback)
    if key not in config:
        return schema_default, False

    value = config.get(key, schema_default)
    stale_defaults = []
    if key in PREVIOUS_SCHEMA_DEFAULTS:
        stale_defaults.append(PREVIOUS_SCHEMA_DEFAULTS[key])
    stale_defaults.extend(LEGACY_SCHEMA_DEFAULTS.get(key, []))

    if value != schema_default and any(value == stale for stale in stale_defaults):
        config[key] = schema_default
        return schema_default, True

    return value, False


def _save_config_if_migrated(config: AstrBotConfig, migrated: bool) -> None:
    if not migrated or not hasattr(config, "save_config"):
        return
    try:
        config.save_config()
    except Exception:
        return

MODE_FLAG_TO_CONTENT_BAR = {
    "-n": "None",
    "-a": "Auto",
    "-p": "Pattern",
    "-e": "Etterna",
    "-g": "Graph",
}

MOD_DEFAULT_SPEED = {
    "dt": 1.5,
    "ht": 0.75,
}

MA_REQUEST_RE = re.compile(
    r"^\s*/ma(?P<graph>g)?(?P<tail>(?:\s*(?:help|[-+0-9].*))?)\s*$",
    re.IGNORECASE,
)

HELP_TEXT = "\n".join(
    [
        "osu!mania 谱面分析",
        "基于 osumania_map_analyser 实现本项目，可以分析键型/SV，并预估对应rf/ln段位。",
        "",
        "用法",
        "/ma <bid>      使用插件配置中的默认主体内容",
        "/ma -n <bid>   主体不显示任何内容，即短卡片模式",
        "/ma -a <bid>   主体内容按谱面 LN 占比自动选择 Pattern 或 Etterna",
        "/ma -p <bid>   主体显示键型分析，非4/6/7K 主体自动回退 Pattern",
        "/ma -e <bid>   主体显示 Etterna 7 大键型分",
        "/ma -g <bid>   主体显示难度变化图，命令简写/mag",
        "/ma help       显示本帮助文本",
        "",
        "示例：/ma 5170433+dt1.1 ",
    ]
)


@register(
    "astrbot_plugin_osu_mania_map_analyser",
    "ZHAO20060708",
    "Render osumania_map_analyser charts from beatmap id via Playwright.",
    "0.1.5",
)
class ManiaMapAnalyserPlugin(Star):
    """AstrBot 插件入口"""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)

        def cfg(key: str, fallback: object) -> object:
            value, changed = _config_value(config, key, fallback)
            nonlocal_config_migration["changed"] |= changed
            return value

        nonlocal_config_migration = {"changed": False}
        self.render_service = ManiaMapAnalyserService(
            plugin_root=PLUGIN_ROOT,
            render_config={
                "capture_target": cfg("capture_target", "full_card"),
                "content_bar": cfg("content_bar", "Auto"),
                "sr_text": cfg("sr_text", "ReworkSR"),
                "diff_text": cfg("diff_text", "Difficulty"),
                "estimator_algorithm": cfg("estimator_algorithm", "Mixed"),
                "etterna_version": cfg("etterna_version", "0.72.3"),
                "companella_etterna_version": cfg("companella_etterna_version", "0.74.0"),
                "enable_numeric_difficulty": cfg("enable_numeric_difficulty", True),
                "enable_etterna_rainbow_bars": cfg("enable_etterna_rainbow_bars", False),
                "show_mode_tag_capsule": cfg("show_mode_tag_capsule", True),
                "vibro_detection": cfg("vibro_detection", True),
                "debug_use_amount": cfg("debug_use_amount", False),
                "debug_use_sv_detection": cfg("debug_use_sv_detection", True),
                "azusa_sunny_reference_ho": cfg("azusa_sunny_reference_ho", True),
                "card_opacity": cfg("card_opacity", "95%"),
                "card_blur": cfg("card_blur", "4px"),
                "card_radius": cfg("card_radius", "Medium"),
            },
        )
        configured_max_concurrency = int(cfg("max_concurrency", 5))
        self.max_concurrency = max(1, min(configured_max_concurrency, 5))
        self.render_timeout_seconds = cfg("render_timeout_seconds", 120)
        self._render_semaphore = asyncio.Semaphore(self.max_concurrency)
        _save_config_if_migrated(config, nonlocal_config_migration["changed"])
        _save_schema_defaults_snapshot()

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def render_map_analysis(self, event: AstrMessageEvent):
        """统一处理 /ma 与 /mag 指令"""

        raw_text = event.message_obj.message_str
        matched = MA_REQUEST_RE.match(raw_text)
        if not matched:
            return

        try:
            bid, render_overrides, runtime_overrides = self._parse_request(
                graph_flag=matched.group("graph"),
                raw_tail=matched.group("tail"),
            )
        except ManiaMapAnalyserError as exc:
            yield event.plain_result(str(exc))
            return

        if bid is None:
            yield event.plain_result(HELP_TEXT)
            return

        yield await self._render_result(event, bid, render_overrides, runtime_overrides)

    async def _render_result(
        self,
        event: AstrMessageEvent,
        bid: str,
        render_overrides: dict[str, str],
        runtime_overrides: dict[str, str | float | None],
    ):
        """统一处理渲染命令，返回 plain_result 或 chain_result 对象。"""

        if self._render_semaphore.locked():
            return event.plain_result("当前谱面分析任务较多，请稍后再试")

        try:
            async with self._render_semaphore:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.render_service.generate_from_bid,
                        bid,
                        render_overrides,
                        runtime_overrides,
                    ),
                    timeout=self.render_timeout_seconds,
                )
        except asyncio.TimeoutError:
            return event.plain_result("谱面分析渲染超时，请稍后再试")
        except ManiaMapAnalyserError as exc:
            return event.plain_result(str(exc))
        except Exception as exc:
            logger.exception("osu mania map analyser plugin failed while rendering chart")
            return event.plain_result("谱面分析渲染失败：" + str(exc))

        image_path = result["image_path"]
        chain = [
            Comp.Reply(id=event.message_obj.message_id),
            Comp.Image.fromFileSystem(image_path),
        ]
        return event.chain_result(chain)

    def _parse_request(
        self,
        graph_flag: str | None,
        raw_tail: str,
    ) -> tuple[
        str | None,
        dict[str, str],
        dict[str, str | float | None],
    ]:
        normalized = re.sub(r"\s+", "", raw_tail).lower()
        if not normalized:
            return None, {}, {}

        if normalized in {"help", "-h", "--help"}:
            return None, {}, {}

        content_bar = "Graph" if graph_flag else None
        remaining = normalized

        if not graph_flag:
            for mode_flag, mode_name in MODE_FLAG_TO_CONTENT_BAR.items():
                if remaining.startswith(mode_flag):
                    content_bar = mode_name
                    remaining = remaining[len(mode_flag):]
                    break

        if not remaining:
            raise ManiaMapAnalyserError("缺少 bid。示例：/ma 5199917、/mag 5199917+dt")

        bid_text = remaining
        mod_text = ""
        if "+" in remaining:
            bid_text, mod_text = remaining.split("+", 1)
            if not bid_text or not mod_text or "+" in mod_text:
                raise ManiaMapAnalyserError(
                    "命令格式不正确。示例：/ma 5199917、/mag5170433+dt、/ma-g5170433+ht0.75"
                )

        if not bid_text.isdigit():
            raise ManiaMapAnalyserError("bid 格式无效，请输入谱面的数字 ID")

        runtime_overrides = self._build_runtime_overrides(mod_text)
        render_overrides = {"contentBar": content_bar} if content_bar else {}
        return bid_text, render_overrides, runtime_overrides

    def _build_runtime_overrides(
        self,
        mod_text: str,
    ) -> dict[str, str | float | None]:
        if not mod_text:
            return {}

        normalized = mod_text.strip().lower()
        mod = ""
        rate_text = ""
        for candidate in ("dt", "ht", "in", "ho"):
            if normalized.startswith(candidate):
                mod = candidate
                rate_text = normalized[len(candidate):]
                break

        if not mod:
            raise ManiaMapAnalyserError("目前仅支持 ht、dt、in、ho 四种 mod")

        if mod in {"in", "ho"}:
            if rate_text:
                raise ManiaMapAnalyserError(f"{mod.upper()} 不支持额外倍速参数")
            return {"cvtFlag": mod.upper()}

        speed_rate = MOD_DEFAULT_SPEED[mod]
        if rate_text:
            try:
                speed_rate = float(rate_text)
            except ValueError as exc:
                raise ManiaMapAnalyserError(f"{mod.upper()} 倍速参数无效：{rate_text}") from exc

        if speed_rate <= 0:
            raise ManiaMapAnalyserError(f"{mod.upper()} 倍速必须大于 0")

        if mod == "ht" and not (0.5 <= speed_rate <= 0.99):
            raise ManiaMapAnalyserError("HT 倍速范围仅支持 0.5-0.99")

        if mod == "dt" and not (1.01 <= speed_rate <= 2):
            raise ManiaMapAnalyserError("DT 倍速范围仅支持 1.01-2")

        return {"speedRate": speed_rate}
