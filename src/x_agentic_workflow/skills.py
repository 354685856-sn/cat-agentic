"""Lightweight local skills.

Skills are markdown files with optional YAML-like metadata. Full skill content is
loaded into the system prompt only when the user asks for that skill by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    content: str
    path: Path
    source: str = "project"
    root: Path | None = None
    version: str = ""
    user_invocable: bool = False


class SkillRegistry:
    def __init__(
        self,
        root: Path,
        *,
        source: str = "project",
        create: bool = True,
        include_loose_markdown: bool = True,
    ) -> None:
        self.root = root
        self.source = source
        self.include_loose_markdown = include_loose_markdown
        if create:
            self.root.mkdir(parents=True, exist_ok=True)

    def discover(self) -> list[Skill]:
        skills: list[Skill] = []
        if not self.root.exists():
            return skills
        for path in self._skill_files():
            content = path.read_text(encoding="utf-8")
            name, description, version, user_invocable = self._metadata(path, content)
            skills.append(
                Skill(
                    name=name,
                    description=description,
                    content=content,
                    path=path,
                    source=self.source,
                    root=self.root,
                    version=version,
                    user_invocable=user_invocable,
                )
            )
        return skills

    def _skill_files(self) -> list[Path]:
        paths: list[Path] = []
        seen: set[Path] = set()
        skill_dirs: set[Path] = set()
        for filename in ("SKILL.md", "skill.md"):
            for path in sorted(self.root.rglob(filename)):
                if path in seen:
                    continue
                if path.parent in skill_dirs:
                    continue
                seen.add(path)
                skill_dirs.add(path.parent)
                paths.append(path)
        if self.include_loose_markdown:
            for path in sorted(self.root.rglob("*.md")):
                if path in seen or path.name.lower() == "readme.md":
                    continue
                if path.parent in skill_dirs:
                    continue
                seen.add(path)
                paths.append(path)
        return paths

    def _metadata(self, path: Path, content: str) -> tuple[str, str, str, bool]:
        name = path.parent.name if path.name.lower() == "skill.md" else path.stem
        description = ""
        version = ""
        user_invocable = False
        for line in content.splitlines()[:40]:
            key, _, value = line.partition(":")
            normalized = key.strip().lower()
            value = value.strip().strip('"').strip("'")
            if normalized == "name" and value:
                name = value
            elif normalized == "description" and value:
                description = value
            elif normalized == "version" and value:
                version = value
            elif normalized in {"user_invocable", "user-invocable"}:
                user_invocable = value.lower() in {"1", "true", "yes", "on"}
        return name, description, version, user_invocable

    def matching_prompt(self, user_text: str) -> str:
        wanted = []
        lowered = user_text.lower()
        for skill in self.discover():
            if skill.name.lower() in lowered:
                wanted.append(f"# Skill: {skill.name}\n\n{skill.content}")
        return "\n\n".join(wanted)
