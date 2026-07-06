"""MCP configuration placeholder.

The v0.1 runtime records MCP server definitions and exposes them in context.
Full JSON-RPC tool bridging is intentionally isolated behind this module so it
can be implemented without changing the agent loop.
"""

from __future__ import annotations

import json
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


class McpRegistry:
    def __init__(self, config_file: Path) -> None:
        self.config_file = config_file

    def list_servers(self) -> list[McpServer]:
        if not self.config_file.exists():
            return []
        data = json.loads(self.config_file.read_text(encoding="utf-8"))
        servers = []
        raw_servers = data.get("servers", data.get("mcpServers", {}))
        if not isinstance(raw_servers, dict):
            return []
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
                )
            )
        return servers

    def context_summary(self) -> str:
        try:
            servers = self.list_servers()
        except (json.JSONDecodeError, OSError, TypeError):
            return ""
        if not servers:
            return ""
        lines = ["Configured MCP servers:"]
        for server in servers:
            if server.url:
                lines.append(f"- {server.name}: {server.transport} {server.url}")
            else:
                lines.append(f"- {server.name}: {server.command} {' '.join(server.args)}".strip())
        return "\n".join(lines)
