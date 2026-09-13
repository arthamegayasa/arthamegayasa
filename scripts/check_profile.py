"""Check profile assets and public repository links using the GitHub REST API.

Run from any directory with Python 3.12+: python scripts/check_profile.py
GITHUB_TOKEN is optional; CI supplies its read-only token for the API rate limit.
"""

import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent


class ProfileHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key] or "")
        if tag == "img" and not attrs.get("alt", "").strip():
            self.errors.append("Every profile image needs descriptive alt text.")


def public_repository(name):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "arthamegayasa-profile-checks",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/repos/{name}", headers=headers)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                repository = json.load(response)
            if repository.get("private") is not False:
                raise ValueError(f"{name}: repository is not public.")
            return
        except HTTPError as error:
            if error.code == 404:
                raise ValueError(f"{name}: repository is missing or private.") from None
            if error.code < 500 or attempt == 2:
                raise ValueError(f"{name}: GitHub API returned HTTP {error.code}.") from None
        except (URLError, TimeoutError) as error:
            if attempt == 2:
                raise ValueError(f"{name}: could not reach the GitHub API.") from error
        time.sleep(attempt + 1)


def main():
    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    parser = ProfileHTML()
    parser.feed(readme)
    links = parser.links + re.findall(r"!?\[[^\]]+\]\(([^\s)]+)\)", readme)
    errors = list(parser.errors)
    repositories = set()
    if not readme.strip() or not links:
        errors.append("README must contain profile content and links.")
    for link in sorted(set(links)):
        if not link:
            errors.append("Empty link or image source.")
            continue
        url = urlsplit(link)
        if url.scheme == "mailto":
            continue
        if not url.scheme and not url.netloc:
            asset = (ROOT / unquote(url.path)).resolve()
            if url.path and (not asset.is_relative_to(ROOT) or not asset.is_file()):
                errors.append(f"Missing local asset: {link}")
            elif asset.suffix.lower() == ".svg":
                try:
                    ET.parse(asset)
                except ET.ParseError:
                    errors.append(f"Invalid SVG XML: {link}")
            continue
        if url.scheme != "https":
            errors.append(f"Use HTTPS for public links: {link}")
        if url.hostname == "github.com":
            parts = url.path.strip("/").split("/")
            if len(parts) >= 2:
                repositories.add("/".join(parts[:2]))
    for name in sorted(repositories):
        try:
            public_repository(name)
            print(f"Public repository OK: {name}")
        except ValueError as error:
            errors.append(str(error))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Profile checks passed: {len(set(links))} links/assets; {len(repositories)} public repositories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
