"""Count uyirmei (vowel-consonant compound) frequencies in Tamil text (TASK PA.002).

Parses Tamil text into aksharas and counts how often each of the 216 uyirmei appears, using the
exact base × sign model from :mod:`grapheme`. This is what defines metric M's long tail: the
bottom-quartile-frequency compounds (DEC-0004, corpus = Project Madurai).

Parsing rule (left to right):
- a consonant followed by the virama (puḷḷi) is a *pure consonant* (mei) — not a uyirmei; skipped.
- a consonant followed by a dependent vowel sign is that uyirmei.
- a bare consonant (nothing, or a non-sign char, follows) is the inherent-'a' uyirmei.
- anything else (independent vowels, digits, punctuation, other scripts, whitespace) is ignored.

Text is NFC-normalized and the two-part o/oo/au signs are folded to their single codepoints first,
so a one-character lookahead is sufficient regardless of how the source encoded them.
"""

from __future__ import annotations

import unicodedata
from collections import Counter

from .grapheme import CONSONANTS, VOWELS, VIRAMA

_CONSONANT_BY_CHAR = {c.char: c.id for c in CONSONANTS}
_SIGN_BY_CHAR = {v.sign: v.id for v in VOWELS if v.sign is not None}

# Two-part vowel signs, decomposed (left-part + right-part) -> single codepoint. Given by explicit
# codepoints so there is no decomposed/composed literal ambiguity. NFC usually composes these
# already; this fold makes counting correct even under a composition exclusion.
_TWO_PART_FOLD = {
    "ொ": "ொ",  # e-sign  + aa-sign     -> o-sign  (ொ)
    "ோ": "ோ",  # ee-sign + aa-sign     -> oo-sign (ோ)
    "ௌ": "ௌ",  # e-sign  + au-length   -> au-sign (ௌ)
}


def normalize(text: str) -> str:
    """NFC-normalize and fold two-part vowel signs to single codepoints."""
    text = unicodedata.normalize("NFC", text)
    for seq, single in _TWO_PART_FOLD.items():
        text = text.replace(seq, single)
    return text


def count_uyirmei(text: str) -> Counter[str]:
    """Return a Counter of ``akshara_id`` -> occurrences over the 216 uyirmei in ``text``."""
    text = normalize(text)
    counts: Counter[str] = Counter()
    i, n = 0, len(text)
    while i < n:
        cid = _CONSONANT_BY_CHAR.get(text[i])
        if cid is None:
            i += 1
            continue
        nxt = text[i + 1] if i + 1 < n else ""
        if nxt == VIRAMA:
            i += 2  # pure consonant (mei) — not a uyirmei
            continue
        sign_id = _SIGN_BY_CHAR.get(nxt)
        if sign_id is not None:
            counts[f"{cid}_{sign_id}"] += 1
            i += 2
        else:
            counts[f"{cid}_a"] += 1
            i += 1
    return counts


def count_uyirmei_in_files(paths) -> tuple[Counter[str], dict[str, int]]:
    """Count over multiple UTF-8 files; return (total counts, per-file uyirmei totals)."""
    total: Counter[str] = Counter()
    per_file: dict[str, int] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        c = count_uyirmei(text)
        per_file[path.name] = sum(c.values())
        total.update(c)
    return total, per_file
