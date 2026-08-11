from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[2]


def replace_language_link(path: Path, label: str, href: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<a class="nav-link" href=")[^"]*(">\s*<span class="menu-text">'
        + re.escape(label)
        + r"</span></a>)",
        re.MULTILINE,
    )
    updated, count = pattern.subn(r"\1" + href + r"\2", text)
    if count:
        path.write_text(updated, encoding="utf-8")


def copy_zh_runtime_assets() -> None:
    target = ROOT / "docs" / "zh" / "assets" / "js"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("language-switch.js", "academic-v35.js"):
        shutil.copy2(ROOT / "assets" / "js" / name, target / name)


def counterpart_href(path: Path, lang: str) -> str:
    rel = path.relative_to(ROOT / "docs")
    if rel.parts and rel.parts[0] == "zh":
        rel = Path(*rel.parts[1:])
    stem = path.stem
    rel_href = rel.as_posix()
    if lang == "english":
        return "https://olivia-wr-research.github.io/zh/" if stem == "index" and len(rel.parts) == 1 else f"https://olivia-wr-research.github.io/zh/{rel_href}"
    return "https://olivia-wr-research.github.io/" if stem == "index" and len(rel.parts) == 1 else f"https://olivia-wr-research.github.io/{rel_href}"


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"english", "zh"}:
        print("usage: fix_bilingual_nav.py english|zh", file=sys.stderr)
        return 2

    if sys.argv[1] == "english":
        for path in (ROOT / "docs").glob("**/*.html"):
            if "zh" in path.relative_to(ROOT / "docs").parts:
                continue
            replace_language_link(path, "中文", counterpart_href(path, "english"))
    else:
        for path in (ROOT / "docs" / "zh").glob("**/*.html"):
            replace_language_link(path, "English", counterpart_href(path, "zh"))
        copy_zh_runtime_assets()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
