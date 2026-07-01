"""Grapheme-model tests (TASK PA.001, AC1): base × sign decomposition is exact for all 216."""

import pytest

from ezhuthu_jepa.data.grapheme import (
    CONSONANTS,
    VOWELS,
    Akshara,
    compose,
    decompose,
    enumerate_uyirmei,
    pure_consonant_text,
)


def test_counts_match_abugida_structure():
    assert len(CONSONANTS) == 18
    assert len(VOWELS) == 12
    assert len(enumerate_uyirmei()) == 216


def test_ids_are_unique():
    assert len({c.id for c in CONSONANTS}) == 18
    assert len({v.id for v in VOWELS}) == 12
    assert len({a.id for a in enumerate_uyirmei()}) == 216


def test_inherent_a_has_no_sign():
    aksh = compose("k", "a")
    assert aksh.has_sign is False
    assert aksh.text == "க"
    assert aksh.codepoints == (0x0B95,)


def test_sign_is_appended_for_non_a_vowels():
    aksh = compose("k", "e")  # க + ெ
    assert aksh.has_sign is True
    assert aksh.codepoints == (0x0B95, 0x0BC6)
    assert aksh.codepoint_labels() == ["U+0B95", "U+0BC6"]


def test_recomposition_matches_source_codepoints_for_all_216():
    """AC1: for every uyirmei, decompose(compose(...)) round-trips AND the text is exactly
    base_char + optional sign_char (the source codepoint sequence). 100% or the test fails."""
    for aksh in enumerate_uyirmei():
        assert decompose(aksh.text) == (aksh.base_id, aksh.sign_id)
        expected = (aksh.consonant.codepoint,) + (
            () if not aksh.has_sign else (ord(aksh.vowel.sign),)
        )
        assert aksh.codepoints == expected


def test_decompose_rejects_non_consonant_lead():
    with pytest.raises(ValueError, match="not a Tamil consonant"):
        decompose("அ")  # independent vowel, not a consonant base


def test_decompose_rejects_bad_sign():
    with pytest.raises(ValueError, match="not a Tamil dependent vowel sign"):
        decompose("க" + "X")


def test_pure_consonant_adds_virama():
    text = pure_consonant_text("k")
    assert text == "க்"
    assert [f"U+{ord(c):04X}" for c in text] == ["U+0B95", "U+0BCD"]


def test_compose_unknown_id_raises():
    with pytest.raises(KeyError):
        compose("zzz", "a")
