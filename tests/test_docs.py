import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CODE_DIRS = [ROOT / "clashroyalebuildabot", ROOT / "main.py"]


def _python_files():
    for path in CODE_DIRS:
        yield from [path] if path.is_file() else path.rglob("*.py")


def _used_error_codes():
    pattern = re.compile(r'WikifiedError\(\s*"(\d{3})"')
    codes = set()
    for path in _python_files():
        codes |= set(pattern.findall(path.read_text(encoding="utf-8")))
    return codes


def _documented_error_codes():
    text = (DOCS / "troubleshooting.md").read_text(encoding="utf-8")
    return set(re.findall(r"^#+ Error E(\d{3})", text, re.MULTILINE))


def test_error_codes_are_found():
    assert _used_error_codes(), "regex no longer matches WikifiedError calls"


@pytest.mark.parametrize("code", sorted(_used_error_codes()))
def test_every_error_code_is_documented(code):
    assert code in _documented_error_codes(), (
        f"E{code} is raised in the code but has no section in "
        "docs/troubleshooting.md"
    )


def _relative_links():
    link = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
    for page in sorted(DOCS.rglob("*.md")):
        for target in link.findall(page.read_text(encoding="utf-8")):
            if not re.match(r"[a-z]+:", target) and not target.startswith("#"):
                yield page, target


@pytest.mark.parametrize(
    ("page", "target"),
    list(_relative_links()),
    ids=lambda v: v.name if isinstance(v, Path) else v,
)
def test_relative_links_resolve(page, target):
    path = target.split("#", 1)[0]
    assert (page.parent / path).exists(), f"{page.name} links to {target}"
