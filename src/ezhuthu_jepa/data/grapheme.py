"""Tamil grapheme model — the exact base × sign → akshara composition (TASK PA.001).

Tamil is an abugida: 18 consonants × 12 vowels = 216 vowel-consonant compounds (uyirmei), plus 12
independent vowels and 18 pure consonants (mei). The whole thesis rests on this composition being
*exact and regular* (spec §2): every uyirmei genuinely is (consonant base) + (dependent vowel sign),
with no irregular forms. This module encodes that rule so seam labels are free and exact.

Representation: an akshara's Unicode text is ``consonant_char`` for the inherent-'a' vowel, or
``consonant_char + vowel_sign_char`` for the other 11 vowels. The dependent vowel sign is the region
the seam-masking objective hides; the consonant base is what stays visible.

Codepoints are the Tamil Unicode block (U+0B80–U+0BFF). Everything here is pure stdlib and exact —
no rendering, no fonts — so it is deterministically testable.
"""

from __future__ import annotations

from dataclasses import dataclass

# U+0BCD TAMIL SIGN VIRAMA (puḷḷi): turns a base consonant (inherent 'a') into a pure consonant.
VIRAMA = "்"


@dataclass(frozen=True)
class Consonant:
    """A Tamil consonant base (carries the inherent vowel 'a' when written bare)."""

    id: str          # stable short romanization, e.g. "k", "zh"; used in ids/filenames
    char: str        # the base consonant character (inherent 'a' form)

    @property
    def codepoint(self) -> int:
        return ord(self.char)


@dataclass(frozen=True)
class Vowel:
    """A Tamil vowel: its independent letter and its dependent sign (None for inherent 'a')."""

    id: str                  # e.g. "a", "aa", "ai"
    independent: str         # the standalone vowel letter, e.g. அ, ஆ
    sign: str | None         # the dependent sign appended to a consonant, or None for 'a'

    @property
    def has_sign(self) -> bool:
        return self.sign is not None


# The 18 core Tamil consonants, in traditional order. IDs are unique short romanizations.
CONSONANTS: tuple[Consonant, ...] = (
    Consonant("k", "க"),     # க
    Consonant("ng", "ங"),    # ங
    Consonant("c", "ச"),     # ச
    Consonant("nj", "ஞ"),    # ஞ
    Consonant("tt", "ட"),    # ட  (retroflex Ta)
    Consonant("nn", "ண"),    # ண  (retroflex Na)
    Consonant("t", "த"),     # த
    Consonant("n", "ந"),     # ந  (dental na)
    Consonant("p", "ப"),     # ப
    Consonant("m", "ம"),     # ம
    Consonant("y", "ய"),     # ய
    Consonant("r", "ர"),     # ர
    Consonant("l", "ல"),     # ல
    Consonant("v", "வ"),     # வ
    Consonant("zh", "ழ"),    # ழ
    Consonant("ll", "ள"),    # ள  (retroflex La)
    Consonant("rr", "ற"),    # ற  (Rra)
    Consonant("nnn", "ன"),   # ன  (alveolar na)
)

# The 12 vowels: 'a' is inherent (no sign); the other 11 have dependent signs. o/oo/au signs are
# single Unicode codepoints that shape into two-part (left+right) marks — handled at render time.
VOWELS: tuple[Vowel, ...] = (
    Vowel("a", "அ", None),        # அ  — inherent, no sign
    Vowel("aa", "ஆ", "ா"),   # ஆ  ா
    Vowel("i", "இ", "ி"),    # இ  ி
    Vowel("ii", "ஈ", "ீ"),   # ஈ  ீ
    Vowel("u", "உ", "ு"),    # உ  ு
    Vowel("uu", "ஊ", "ூ"),   # ஊ  ூ
    Vowel("e", "எ", "ெ"),    # எ  ெ  (left-reordering)
    Vowel("ee", "ஏ", "ே"),   # ஏ  ே  (left-reordering)
    Vowel("ai", "ஐ", "ை"),   # ஐ  ை  (left-reordering)
    Vowel("o", "ஒ", "ொ"),    # ஒ  ொ  (two-part)
    Vowel("oo", "ஓ", "ோ"),   # ஓ  ோ  (two-part)
    Vowel("au", "ஔ", "ௌ"),   # ஔ  ௌ  (two-part)
)

_CONSONANT_BY_ID = {c.id: c for c in CONSONANTS}
_VOWEL_BY_ID = {v.id: v for v in VOWELS}


@dataclass(frozen=True)
class Akshara:
    """A single vowel-consonant compound (uyirmei): consonant base + one vowel."""

    consonant: Consonant
    vowel: Vowel

    @property
    def id(self) -> str:
        """Stable id, e.g. ``k_a``, ``zh_ai`` — safe for filenames and manifests."""
        return f"{self.consonant.id}_{self.vowel.id}"

    @property
    def base_id(self) -> str:
        return self.consonant.id

    @property
    def sign_id(self) -> str:
        return self.vowel.id

    @property
    def has_sign(self) -> bool:
        return self.vowel.has_sign

    @property
    def text(self) -> str:
        """The Unicode string: bare consonant for 'a', else consonant + dependent sign."""
        if self.vowel.sign is None:
            return self.consonant.char
        return self.consonant.char + self.vowel.sign

    @property
    def codepoints(self) -> tuple[int, ...]:
        """The source codepoint sequence this akshara must compose to (the exact label)."""
        return tuple(ord(ch) for ch in self.text)

    def codepoint_labels(self) -> list[str]:
        """Human/manifest-friendly codepoints, e.g. ``["U+0B95", "U+0BC6"]`` — ASCII, text-free."""
        return [f"U+{cp:04X}" for cp in self.codepoints]


def compose(base_id: str, sign_id: str) -> Akshara:
    """Build the akshara for a (consonant id, vowel id) pair. Raises KeyError on unknown ids."""
    return Akshara(_CONSONANT_BY_ID[base_id], _VOWEL_BY_ID[sign_id])


def decompose(text: str) -> tuple[str, str]:
    """Recover (consonant id, vowel id) from an akshara's Unicode text.

    This is the inverse of :attr:`Akshara.text`; a round-trip check that it equals the intended
    ids is what proves the base × sign decomposition is exact (PA.001 acceptance criterion 1).
    """
    if not text:
        raise ValueError("empty akshara text")
    base_char = text[0]
    consonant = next((c for c in CONSONANTS if c.char == base_char), None)
    if consonant is None:
        raise ValueError(f"leading char U+{ord(base_char):04X} is not a Tamil consonant")
    rest = text[1:]
    if rest == "":
        return consonant.id, "a"
    if len(rest) != 1:
        raise ValueError(f"expected a single dependent sign after the base, got {len(rest)} chars")
    vowel = next((v for v in VOWELS if v.sign == rest), None)
    if vowel is None:
        raise ValueError(f"U+{ord(rest):04X} is not a Tamil dependent vowel sign")
    return consonant.id, vowel.id


def enumerate_uyirmei() -> list[Akshara]:
    """All 216 vowel-consonant compounds (18 consonants × 12 vowels), in a deterministic order."""
    return [Akshara(c, v) for c in CONSONANTS for v in VOWELS]


def pure_consonant_text(base_id: str) -> str:
    """The mei (pure consonant) form: base + virama, e.g. க + ் → க். Missing puḷḷi is the manuscript
    ambiguity (spec §0) — the dot that a bare consonant vs its 'a' form differ by."""
    return _CONSONANT_BY_ID[base_id].char + VIRAMA
