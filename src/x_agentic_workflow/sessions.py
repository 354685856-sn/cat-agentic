"""Conversation session persistence."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .types import Message


class SessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, session_id: str) -> Path:
        safe = "".join(ch for ch in session_id if ch.isalnum() or ch in {"-", "_"})
        if not safe:
            raise ValueError("session_id cannot be empty")
        return self.root / f"{safe}.json"

    def new_id(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")

    def load(self, session_id: str) -> list[Message]:
        data = self.load_payload(session_id)
        return [Message(**item) for item in data.get("messages", [])]

    def load_payload(self, session_id: str) -> dict[str, Any]:
        path = self.path_for(session_id)
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data

    def save(self, session_id: str, messages: list[Message]) -> None:
        path = self.path_for(session_id)
        payload = self.load_payload(session_id)
        payload.update(
            {
                "session_id": session_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "messages": [asdict(m) for m in messages],
            }
        )
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def load_file_changes(self, session_id: str) -> list[dict[str, Any]]:
        data = self.load_payload(session_id)
        changes = data.get("file_changes", [])
        if not isinstance(changes, list):
            return []
        return [change for change in changes if isinstance(change, dict)]

    def save_file_changes(self, session_id: str, changes: list[dict[str, Any]]) -> None:
        path = self.path_for(session_id)
        payload = {
            **self.load_payload(session_id),
            "session_id": session_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "file_changes": changes,
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def session_summary(self, session_id: str) -> dict[str, Any]:
        payload = self.load_payload(session_id)
        messages = payload.get("messages", [])
        title = session_id
        if isinstance(messages, list):
            for message in messages:
                if not isinstance(message, dict):
                    continue
                if message.get("role") != "user":
                    continue
                content = str(message.get("content", "")).strip()
                if content:
                    title = _compact_title(content)
                    break
        file_changes = payload.get("file_changes", [])
        updated_at = str(payload.get("updated_at", ""))
        return {
            "id": session_id,
            "title": title,
            "updatedAt": updated_at,
            "updatedLabel": _format_updated_label(updated_at),
            "updatedSortKey": _updated_sort_key(updated_at, session_id),
            "messageCount": len(messages) if isinstance(messages, list) else 0,
            "fileChangeCount": len(file_changes) if isinstance(file_changes, list) else 0,
        }

    def list_session_summaries(self) -> list[dict[str, Any]]:
        summaries = [self.session_summary(session_id) for session_id in self.list_sessions()]
        return sorted(summaries, key=lambda item: str(item["updatedSortKey"]))

    def list_sessions(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.json"))


def _compact_title(text: str, limit: int = 42) -> str:
    single_line = " ".join(text.split())
    if len(single_line) <= limit:
        return single_line
    return f"{single_line[: limit - 1]}…"


def _format_updated_label(value: str) -> str:
    timestamp = _parse_iso_datetime(value)
    if timestamp is None:
        return ""
    local_time = timestamp.astimezone()
    return local_time.strftime("%m-%d %H:%M")


def _updated_sort_key(value: str, fallback: str) -> str:
    timestamp = _parse_iso_datetime(value)
    if timestamp is None:
        return fallback
    return timestamp.isoformat()


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
