"""Configuration loading for x-agentic-workflow."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

ProviderName = Literal["anthropic", "openai-compatible"]

DEFAULT_CONFIG_DIR = Path.home() / ".x-agentic-workflow"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class ProviderConfig:
    name: ProviderName = "anthropic"
    model: str = "claude-3-5-sonnet-latest"
    base_url: str | None = None
    api_key_env: str = "ANTHROPIC_API_KEY"


@dataclass
class RuntimeConfig:
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    provider_profiles: list[dict[str, Any]] = field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.2
    workdir: Path = field(default_factory=lambda: Path.cwd().resolve())
    config_file: Path = DEFAULT_CONFIG_FILE
    max_output_chars: int = 20_000
    require_command_approval: bool = True
    sessions_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR / "sessions")
    skills_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR / "skills")
    hooks_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR / "hooks")
    mcp_config_file: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR / "mcp.json")
    recent_projects: list[str] = field(default_factory=list)
    desktop_theme: Literal["pure", "classic", "dark", "ocean", "comic"] = "ocean"
    # Display languages are intentionally limited to the two complete UI bundles.
    # Reply-language preferences remain independent below and may use model-supported
    # languages without implying that the desktop chrome is translated.
    desktop_language: Literal["en", "zh-CN"] = "zh-CN"
    desktop_reply_language: Literal["default", "en", "zh-CN", "zh-TW", "ja", "ko"] = "default"
    desktop_output_style: Literal["default", "concise", "explanatory", "review"] = "default"
    desktop_permission_mode: Literal["ask", "skip"] = "ask"
    desktop_thinking_enabled: bool = True
    desktop_auto_memory_enabled: bool = False
    desktop_trace_enabled: bool = True
    desktop_network_mode: Literal["direct", "system", "manual"] = "direct"
    desktop_manual_proxy: str = ""
    ai_request_timeout_seconds: int = 600
    desktop_webfetch_preflight_skip: bool = True
    desktop_web_search_provider: Literal["auto", "tavily", "brave", "provider", "off"] = "auto"
    desktop_tavily_api_key_env: str = "TAVILY_API_KEY"
    desktop_brave_api_key_env: str = "BRAVE_SEARCH_API_KEY"
    desktop_data_dir_mode: Literal["system", "portable"] = "system"
    desktop_portable_data_dir: str = ""
    desktop_send_mode: Literal["enter", "modifier-enter"] = "modifier-enter"
    desktop_ui_scale: int = 100
    desktop_notifications_enabled: bool = False
    desktop_h5_enabled: bool = False
    desktop_h5_host: str = "127.0.0.1"
    desktop_h5_fixed_port: int | None = None
    desktop_h5_keepalive_seconds: int = 30

    @property
    def api_key(self) -> str:
        return os.environ.get(self.provider.api_key_env, "").strip()

    @classmethod
    def load(cls, config_file: Path | None = None, workdir: Path | None = None) -> RuntimeConfig:
        load_dotenv(Path.cwd() / ".env")
        path = config_file or DEFAULT_CONFIG_FILE
        data: dict[str, Any] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))

        provider_data = data.get("provider", {})
        provider = ProviderConfig(
            name=provider_data.get("name", os.environ.get("XAW_PROVIDER", "anthropic")),
            model=provider_data.get(
                "model",
                os.environ.get("XAW_MODEL", "claude-3-5-sonnet-latest"),
            ),
            base_url=provider_data.get("base_url", os.environ.get("XAW_BASE_URL") or None),
            api_key_env=provider_data.get(
                "api_key_env",
                "OPENAI_API_KEY"
                if os.environ.get("XAW_PROVIDER") == "openai-compatible"
                else "ANTHROPIC_API_KEY",
            ),
        )
        fixed_port = data.get("desktop_h5_fixed_port")
        if isinstance(fixed_port, bool):
            fixed_port = None
        try:
            parsed_fixed_port = int(fixed_port) if fixed_port is not None else None
        except (TypeError, ValueError):
            parsed_fixed_port = None
        if parsed_fixed_port is not None and not 1024 <= parsed_fixed_port <= 65535:
            parsed_fixed_port = None

        try:
            h5_keepalive = int(data.get("desktop_h5_keepalive_seconds", 30))
        except (TypeError, ValueError):
            h5_keepalive = 30

        provider_profiles = data.get("provider_profiles", [])
        if not isinstance(provider_profiles, list):
            provider_profiles = []

        desktop_theme = data.get("desktop_theme")
        desktop_language = data.get("desktop_language")
        desktop_reply_language = data.get("desktop_reply_language")
        desktop_output_style = data.get("desktop_output_style")
        desktop_permission_mode = data.get("desktop_permission_mode")
        desktop_network_mode = data.get("desktop_network_mode")
        desktop_web_search_provider = data.get("desktop_web_search_provider")
        desktop_data_dir_mode = data.get("desktop_data_dir_mode")
        try:
            ai_timeout = int(data.get("ai_request_timeout_seconds", 600))
        except (TypeError, ValueError):
            ai_timeout = 600

        return cls(
            provider=provider,
            provider_profiles=[
                profile for profile in provider_profiles if isinstance(profile, dict)
            ],
            max_tokens=int(data.get("max_tokens", os.environ.get("XAW_MAX_TOKENS", 4096))),
            temperature=float(data.get("temperature", os.environ.get("XAW_TEMPERATURE", 0.2))),
            workdir=(workdir or Path.cwd()).resolve(),
            config_file=path,
            max_output_chars=int(data.get("max_output_chars", 20_000)),
            require_command_approval=bool(data.get("require_command_approval", True)),
            recent_projects=[
                str(Path(raw).expanduser().resolve())
                for raw in data.get("recent_projects", [])
                if isinstance(raw, str) and raw.strip()
            ][:8],
            desktop_theme=cast(
                Literal["pure", "classic", "dark", "ocean", "comic"],
                desktop_theme
                if desktop_theme in {"pure", "classic", "dark", "ocean", "comic"}
                else "ocean",
            ),
            desktop_language=cast(
                Literal["en", "zh-CN"],
                desktop_language if desktop_language in {"en", "zh-CN"} else "zh-CN",
            ),
            desktop_reply_language=cast(
                Literal["default", "en", "zh-CN", "zh-TW", "ja", "ko"],
                desktop_reply_language
                if desktop_reply_language in {"default", "en", "zh-CN", "zh-TW", "ja", "ko"}
                else "default",
            ),
            desktop_output_style=cast(
                Literal["default", "concise", "explanatory", "review"],
                desktop_output_style
                if desktop_output_style in {"default", "concise", "explanatory", "review"}
                else "default",
            ),
            desktop_permission_mode=cast(
                Literal["ask", "skip"],
                desktop_permission_mode if desktop_permission_mode in {"ask", "skip"} else "ask",
            ),
            desktop_thinking_enabled=bool(data.get("desktop_thinking_enabled", True)),
            desktop_auto_memory_enabled=bool(data.get("desktop_auto_memory_enabled", False)),
            desktop_trace_enabled=bool(data.get("desktop_trace_enabled", True)),
            desktop_network_mode=cast(
                Literal["direct", "system", "manual"],
                desktop_network_mode
                if desktop_network_mode in {"direct", "system", "manual"}
                else "direct",
            ),
            desktop_manual_proxy=str(data.get("desktop_manual_proxy", "")).strip(),
            ai_request_timeout_seconds=max(30, min(1800, ai_timeout)),
            desktop_webfetch_preflight_skip=bool(
                data.get("desktop_webfetch_preflight_skip", True)
            ),
            desktop_web_search_provider=cast(
                Literal["auto", "tavily", "brave", "provider", "off"],
                desktop_web_search_provider
                if desktop_web_search_provider in {"auto", "tavily", "brave", "provider", "off"}
                else "auto",
            ),
            desktop_tavily_api_key_env=str(
                data.get("desktop_tavily_api_key_env", "TAVILY_API_KEY")
            ).strip()
            or "TAVILY_API_KEY",
            desktop_brave_api_key_env=str(
                data.get("desktop_brave_api_key_env", "BRAVE_SEARCH_API_KEY")
            ).strip()
            or "BRAVE_SEARCH_API_KEY",
            desktop_data_dir_mode=cast(
                Literal["system", "portable"],
                desktop_data_dir_mode
                if desktop_data_dir_mode in {"system", "portable"}
                else "system",
            ),
            desktop_portable_data_dir=str(data.get("desktop_portable_data_dir", "")).strip(),
            desktop_send_mode=cast(
                Literal["enter", "modifier-enter"],
                data.get("desktop_send_mode")
                if data.get("desktop_send_mode") in {"enter", "modifier-enter"}
                else "modifier-enter",
            ),
            desktop_ui_scale=max(50, min(200, int(data.get("desktop_ui_scale", 100)))),
            desktop_notifications_enabled=bool(
                data.get("desktop_notifications_enabled", False)
            ),
            desktop_h5_enabled=bool(data.get("desktop_h5_enabled", False)),
            desktop_h5_host=str(data.get("desktop_h5_host", "127.0.0.1")).strip()
            or "127.0.0.1",
            desktop_h5_fixed_port=parsed_fixed_port,
            desktop_h5_keepalive_seconds=max(5, min(3600, h5_keepalive)),
        )

    def validate_for_model_call(self) -> None:
        if self.provider.name not in {"anthropic", "openai-compatible"}:
            raise ValueError(f"Unsupported provider: {self.provider.name}")
        if not self.api_key:
            raise ValueError(
                f"{self.provider.api_key_env} is not set. Run `xaw init` or export the key."
            )

    def save(self) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "provider": {
                "name": self.provider.name,
                "model": self.provider.model,
                "base_url": self.provider.base_url,
                "api_key_env": self.provider.api_key_env,
            },
            "provider_profiles": self.provider_profiles,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "max_output_chars": self.max_output_chars,
            "require_command_approval": self.require_command_approval,
            "recent_projects": self.recent_projects[:8],
            "desktop_theme": self.desktop_theme,
            "desktop_language": self.desktop_language,
            "desktop_reply_language": self.desktop_reply_language,
            "desktop_output_style": self.desktop_output_style,
            "desktop_permission_mode": self.desktop_permission_mode,
            "desktop_thinking_enabled": self.desktop_thinking_enabled,
            "desktop_auto_memory_enabled": self.desktop_auto_memory_enabled,
            "desktop_trace_enabled": self.desktop_trace_enabled,
            "desktop_network_mode": self.desktop_network_mode,
            "desktop_manual_proxy": self.desktop_manual_proxy,
            "ai_request_timeout_seconds": self.ai_request_timeout_seconds,
            "desktop_webfetch_preflight_skip": self.desktop_webfetch_preflight_skip,
            "desktop_web_search_provider": self.desktop_web_search_provider,
            "desktop_tavily_api_key_env": self.desktop_tavily_api_key_env,
            "desktop_brave_api_key_env": self.desktop_brave_api_key_env,
            "desktop_data_dir_mode": self.desktop_data_dir_mode,
            "desktop_portable_data_dir": self.desktop_portable_data_dir,
            "desktop_send_mode": self.desktop_send_mode,
            "desktop_ui_scale": self.desktop_ui_scale,
            "desktop_notifications_enabled": self.desktop_notifications_enabled,
            "desktop_h5_enabled": self.desktop_h5_enabled,
            "desktop_h5_host": self.desktop_h5_host,
            "desktop_h5_fixed_port": self.desktop_h5_fixed_port,
            "desktop_h5_keepalive_seconds": self.desktop_h5_keepalive_seconds,
        }
        self.config_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
