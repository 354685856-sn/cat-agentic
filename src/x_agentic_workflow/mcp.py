"""MCP configuration placeholder.

The v0.1 runtime records MCP server definitions and exposes them in context.
Full JSON-RPC tool bridging is intentionally isolated behind this module so it
can be implemented without changing the agent loop.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass
class McpServer:
    name: str
    command: str
    args: list[str]
    transport: str = "stdio"
    url: str | None = None
    env_keys: list[str] | None = None
    enabled: bool = True


class McpRegistry:
    def __init__(self, config_file: Path | Sequence[Path]) -> None:
        if isinstance(config_file, Path):
            self.config_files = [config_file]
        else:
            self.config_files = list(config_file)
        self.config_file = self.config_files[0] if self.config_files else Path("mcp.json")

    def list_servers(self) -> list[McpServer]:
        servers = []
        for config_file in self.config_files:
            if not config_file.exists():
                continue
            data = json.loads(config_file.read_text(encoding="utf-8"))
            raw_servers = data.get("servers", data.get("mcpServers", {}))
            if not isinstance(raw_servers, dict):
                continue
            for name, spec in raw_servers.items():
                if not isinstance(spec, dict):
                    continue
                args = spec.get("args", [])
                env = spec.get("env", {})
                servers.append(
                    McpServer(
                        name=name,
                        command=str(spec.get("command", "")),
                        args=[str(arg) for arg in args] if isinstance(args, list) else [],
                        transport=str(spec.get("transport", spec.get("type", "stdio")) or "stdio"),
                        url=str(spec["url"]) if spec.get("url") else None,
                        env_keys=sorted(str(key) for key in env) if isinstance(env, dict) else [],
                        enabled=bool(spec.get("enabled", True)),
                    )
                )
        return servers

    def context_summary(self) -> str:
        try:
            servers = self.list_servers()
        except (json.JSONDecodeError, OSError, TypeError):
            return ""
        enabled_servers = [server for server in servers if server.enabled]
        if not enabled_servers:
            return ""
        lines = ["Configured MCP servers:"]
        for server in enabled_servers:
            if server.url:
                lines.append(f"- {server.name}: {server.transport} {server.url}")
            else:
                lines.append(f"- {server.name}: {server.command} {' '.join(server.args)}".strip())
        return "\n".join(lines)


def project_private_mcp_file(config_dir: Path, workdir: Path) -> Path:
    resolved = str(workdir.resolve())
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", workdir.name).strip(".-") or "project"
    return config_dir / "mcp" / "projects" / f"{slug}-{digest}" / "mcp.json"


def project_shared_mcp_file(workdir: Path) -> Path:
    return workdir / ".mcp.json"


def scoped_mcp_config_files(config_dir: Path, workdir: Path, user_mcp_file: Path) -> list[Path]:
    files = [
        project_private_mcp_file(config_dir, workdir),
        project_shared_mcp_file(workdir),
        user_mcp_file,
    ]
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique
