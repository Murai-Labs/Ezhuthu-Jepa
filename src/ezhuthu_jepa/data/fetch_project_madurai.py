"""Fetch a reproducible Project Madurai Tamil corpus snapshot (TASK PA.002 corpus ingestion).

Downloads Project Madurai UTF-8 e-texts, strips HTML to plain Tamil text, and writes one ``.txt``
per work under ``--out`` (gitignored). Pages with too little Tamil (index/empty pages, 404s) are
skipped. The exact bytes are pinned downstream by the split manifest's per-file sha256 + the
provenance data_hash, so the corpus is reproducible from this snapshot even though it is not committed.

Project Madurai e-texts are public domain / freely distributable (the project's stated purpose).

    python -m ezhuthu_jepa.data.fetch_project_madurai --start 1 --end 80
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_URL = "https://www.projectmadurai.org/pm_etexts/utf8/pmuni{n:04d}.html"
_UA = "Mozilla/5.0 (research corpus fetch; Ezhuthu-Jepa/Murai-Labs)"
_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_ANYTAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_TAMIL_RE = re.compile(r"[஀-௿]")
_MIN_TAMIL_CHARS = 500


def _strip_html(raw: str) -> str:
    text = _TAG_RE.sub(" ", raw)
    text = _ANYTAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def fetch(start: int, end: int, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for n in range(start, end + 1):
        url = _URL.format(n=n)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            print(f"[fetch] pmuni{n:04d}: skip ({exc})", flush=True)
            continue
        text = _strip_html(raw)
        tamil = len(_TAMIL_RE.findall(text))
        if tamil < _MIN_TAMIL_CHARS:
            print(f"[fetch] pmuni{n:04d}: skip (only {tamil} tamil chars)", flush=True)
            continue
        path = out_dir / f"pmuni{n:04d}.txt"
        path.write_text(text, encoding="utf-8")
        written.append(path)
        print(f"[fetch] pmuni{n:04d}: wrote {tamil} tamil chars -> {path.name}", flush=True)
        time.sleep(0.3)  # be polite to the server
    print(f"[fetch] done: {len(written)} texts under {out_dir}", flush=True)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch a Project Madurai Tamil corpus snapshot.")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=80)
    parser.add_argument("--out", type=Path, default=Path("data/raw/project-madurai"))
    args = parser.parse_args(argv)
    fetch(args.start, args.end, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
