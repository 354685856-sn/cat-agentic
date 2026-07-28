from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME_PAGE = ROOT / "site" / "index.html"
DOWNLOAD_PAGE = ROOT / "site" / "download" / "index.html"


class DownloadPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.platforms: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if values.get("data-platform"):
            self.platforms.add(str(values["data-platform"]))
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))


def test_customer_download_page_has_real_release_and_install_paths() -> None:
    html = DOWNLOAD_PAGE.read_text(encoding="utf-8")
    parser = DownloadPageParser()
    parser.feed(html)

    assert {"downloads", "install", "macDownload", "releaseStatus"}.issubset(parser.ids)
    assert parser.platforms == {"mac", "windows", "linux", "source"}
    assert "https://api.github.com/repos/${repo}/releases?per_page=20" in html
    assert "X-Agentic-Workflow-0.5.0-macos-preview.dmg" in html
    assert "pipx install x-agentic-workflow" in html
    assert "xaw desktop" in html
    assert "site/download" not in html
    assert not any(href in {"#", "javascript:void(0)"} for href in parser.links)


def test_customer_download_page_references_existing_product_preview() -> None:
    html = DOWNLOAD_PAGE.read_text(encoding="utf-8")
    asset = ROOT / "site" / "assets" / "cat-agentic-workspace.png"

    assert "../assets/cat-agentic-workspace.png" in html
    assert asset.is_file()
    assert asset.stat().st_size > 20_000


def test_customer_home_page_leads_with_product_and_real_download() -> None:
    html = HOME_PAGE.read_text(encoding="utf-8")

    assert "cat-agentic" in html
    assert "本地 AI 编码工作区" in html
    assert 'href="./download/"' in html
    assert "./assets/cat-agentic-workspace.png" in html
    assert "项目与会话保存在本机" in html
    assert "API 密钥由客户自己保管" in html
    assert "终端命令默认需要审批" in html
