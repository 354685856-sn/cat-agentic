from pathlib import Path


def test_macos_preview_dmg_script_is_present_and_scoped() -> None:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts/build-macos-preview-dmg.sh"
    smoke_script = root / "scripts/smoke-macos-preview-dmg.sh"
    signing_script = root / "scripts/check-macos-signing.sh"
    launcher = root / "packaging/macos/x-agentic-workflow-distribution-launcher.zsh"

    assert script.is_file()
    assert smoke_script.is_file()
    assert signing_script.is_file()
    assert launcher.is_file()
    assert script.stat().st_mode & 0o111
    assert smoke_script.stat().st_mode & 0o111
    assert signing_script.stat().st_mode & 0o111
    assert launcher.stat().st_mode & 0o111

    script_text = script.read_text(encoding="utf-8")
    smoke_text = smoke_script.read_text(encoding="utf-8")
    signing_text = signing_script.read_text(encoding="utf-8")
    launcher_text = launcher.read_text(encoding="utf-8")

    assert "hdiutil create" in script_text
    assert "Contents/Resources/source" in script_text
    assert "ln -s /Applications" in script_text
    assert "hdiutil attach" in smoke_text
    assert "/api/state" in smoke_text
    assert "Notarization Ticket=stapled" in signing_text
    assert "Application Support/x-agentic-workflow" in launcher_text
    assert "xaw desktop --host 127.0.0.1 --port 8765" in launcher_text


def test_legal_reference_map_preserves_clean_room_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = root / "docs/product/legal-open-source-reference-map.md"
    text = doc.read_text(encoding="utf-8")

    assert "Not allowed" in text
    assert "Use leaked-source-derived code as a reference" in text
    assert "Reference matrix" in text
    assert "aider" in text
    assert "OpenHands" in text
    assert "Electron" in text


def test_docker_workflow_has_no_template_placeholders() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = root / ".github/workflows/docker-build.yml"
    dockerfile = root / "Dockerfile"

    text = workflow.read_text(encoding="utf-8")

    assert dockerfile.is_file()
    assert "{{REGISTRY" not in text
    assert "{{IMAGE_NAME" not in text
    assert "REGISTRY: ghcr.io" in text
    assert "IMAGE_NAME: ${{ github.repository }}" in text
    assert "actions/checkout@v7" in text
    assert "docker/login-action@v4" in text
    assert "docker/build-push-action@v7" in text
