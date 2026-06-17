from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_RUNTIME_DIR = Path("data") / "runtime"
_VENDOR_DIR = _RUNTIME_DIR / "site-packages"
_BROWSER_DIR = _RUNTIME_DIR / "ms-playwright"
_STATE_FILE = _RUNTIME_DIR / "dependency_state.json"

_REQUIRED_MODULES = {
    "playwright": "playwright",
    "PIL": "Pillow",
    "aiohttp": "aiohttp",
}


def bootstrap_plugin_runtime(plugin_root: Path) -> None:
    runtime_root = plugin_root / _RUNTIME_DIR
    vendor_dir = plugin_root / _VENDOR_DIR
    browser_dir = plugin_root / _BROWSER_DIR
    state_file = plugin_root / _STATE_FILE
    requirements_path = plugin_root / "requirements.txt"

    runtime_root.mkdir(parents=True, exist_ok=True)
    vendor_dir.mkdir(parents=True, exist_ok=True)

    _prepend_sys_path(vendor_dir)
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(browser_dir))

    expected_state = _build_expected_state(requirements_path)
    saved_state = _load_state(state_file)
    missing_modules = _find_missing_modules()
    packages_ready = _matches_expected_state(saved_state, expected_state) and not missing_modules
    browser_ready = (
        saved_state.get("browser_installed") is True
        and _has_playwright_browser(browser_dir)
    )

    if packages_ready and browser_ready:
        return

    install_env = _build_install_env(vendor_dir, browser_dir)

    if not packages_ready:
        logger.info("Installing plugin dependencies into %s", vendor_dir)
        _run_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-warn-script-location",
                "--upgrade",
                "--target",
                str(vendor_dir),
                "-r",
                str(requirements_path),
            ],
            env=install_env,
            timeout=900,
            error_prefix="安装插件 Python 依赖失败",
        )
        importlib.invalidate_caches()
        _prepend_sys_path(vendor_dir)

        missing_modules = _find_missing_modules()
        if missing_modules:
            raise RuntimeError(
                "插件依赖安装后仍无法导入: " + ", ".join(sorted(missing_modules))
            )

        saved_state = dict(expected_state)
        saved_state["browser_installed"] = False
        _save_state(state_file, saved_state)

    if not browser_ready:
        logger.info("Installing Playwright Chromium into %s", browser_dir)
        _run_command(
            [
                sys.executable,
                "-m",
                "playwright",
                "install",
                "chromium",
            ],
            env=install_env,
            timeout=1800,
            error_prefix="安装 Playwright Chromium 失败",
        )
        saved_state = dict(expected_state)
        saved_state["browser_installed"] = True
        _save_state(state_file, saved_state)


def _prepend_sys_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _build_expected_state(requirements_path: Path) -> dict[str, object]:
    digest = hashlib.sha256(requirements_path.read_bytes()).hexdigest()
    return {
        "requirements_sha256": digest,
        "python_executable": sys.executable,
        "python_version": list(sys.version_info[:3]),
    }


def _load_state(state_file: Path) -> dict[str, object]:
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _matches_expected_state(
    saved_state: dict[str, object],
    expected_state: dict[str, object],
) -> bool:
    return all(saved_state.get(key) == value for key, value in expected_state.items())


def _save_state(state_file: Path, state: dict[str, object]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _find_missing_modules() -> list[str]:
    missing: list[str] = []
    for module_name in _REQUIRED_MODULES:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def _has_playwright_browser(browser_dir: Path) -> bool:
    if not browser_dir.is_dir():
        return False

    executable_names = {
        "chrome",
        "chrome.exe",
        "chromium",
        "chromium.exe",
        "headless_shell",
        "headless_shell.exe",
        "headless-shell",
        "headless-shell.exe",
    }
    for path in browser_dir.rglob("*"):
        if path.is_file() and path.name.lower() in executable_names:
            return True
    return False


def _build_install_env(vendor_dir: Path, browser_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    python_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{vendor_dir}{os.pathsep}{python_path}" if python_path else str(vendor_dir)
    )
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_dir)
    return env


def _run_command(
    command: list[str],
    env: dict[str, str],
    timeout: int,
    error_prefix: str,
) -> None:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as exc:
        details = _tail_command_output(exc.stdout, exc.stderr)
        raise RuntimeError(f"{error_prefix}: {details}") from exc
    except Exception as exc:
        raise RuntimeError(f"{error_prefix}: {exc}") from exc

    if completed.stderr:
        logger.debug("%s stderr: %s", command[0], completed.stderr.strip())


def _tail_command_output(stdout: str | None, stderr: str | None) -> str:
    chunks = []
    if stderr:
        chunks.append(stderr.strip())
    if stdout:
        chunks.append(stdout.strip())

    merged = "\n".join(chunk for chunk in chunks if chunk).strip()
    if not merged:
        return "无输出"

    lines = merged.splitlines()
    return " | ".join(lines[-8:])
