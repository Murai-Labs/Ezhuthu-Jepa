"""Frequency + split tests (TASK PA.002): counting is exact; buckets partition; splits don't leak."""

import pytest

from ezhuthu_jepa.data.frequency import count_uyirmei
from ezhuthu_jepa.data.frequency_split import (
    BUCKET_LABELS,
    assign_buckets,
    assign_split,
)
from ezhuthu_jepa.data.grapheme import enumerate_uyirmei


# --- frequency counting ---


def test_counts_bare_sign_and_skips_mei():
    # க (k_a) · கா (k_aa) · கி (k_i) · க் (pure consonant, skipped) · ம (m_a)
    counts = count_uyirmei("க கா கி க் ம")
    assert counts["k_a"] == 1
    assert counts["k_aa"] == 1
    assert counts["k_i"] == 1
    assert counts["m_a"] == 1
    assert sum(counts.values()) == 4  # the mei க் is not counted


def test_counts_two_part_vowels():
    counts = count_uyirmei("கொ கோ கௌ")  # o, oo, au
    assert counts["k_o"] == 1
    assert counts["k_oo"] == 1
    assert counts["k_au"] == 1


def test_ignores_non_tamil_and_independent_vowels():
    counts = count_uyirmei("abc 123 அ ஆ !! \n")  # independent vowels + latin/digits/punct
    assert sum(counts.values()) == 0


def test_repeated_akshara_accumulates():
    assert count_uyirmei("ககக")["k_a"] == 3


# --- bucketing ---


def _uniform_freqs(value: int = 0) -> dict[str, int]:
    return {a.id: value for a in enumerate_uyirmei()}


def test_buckets_partition_all_216_into_quartiles():
    freqs = _uniform_freqs()
    # make a clear ordering: give each akshara a distinct frequency by index
    for i, a in enumerate(enumerate_uyirmei()):
        freqs[a.id] = i
    bucket_of, boundaries, bottom = assign_buckets(freqs, n_buckets=4)
    assert len(bucket_of) == 216
    assert len(bottom) == 54
    assert len(boundaries) == 4
    # every akshara has exactly one bucket; buckets are the defined labels
    assert set(bucket_of.values()) == set(BUCKET_LABELS)
    counts = {label: sum(1 for v in bucket_of.values() if v == label) for label in BUCKET_LABELS}
    assert all(c == 54 for c in counts.values())


def test_zero_frequency_lands_in_bottom_quartile():
    freqs = _uniform_freqs()
    # one common akshara, the rest zero → the zeros dominate the bottom quartile
    freqs["k_a"] = 1000
    _, _, bottom = assign_buckets(freqs, n_buckets=4)
    assert "k_a" not in bottom


def test_bad_bucket_count_raises():
    with pytest.raises(Exception):
        assign_buckets(_uniform_freqs(), n_buckets=5)  # 216 not divisible by 5


# --- train/eval split ---


def _instances(n_fonts: int = 2):
    fonts = ["noto", "nirmala", "extra"][:n_fonts]
    return [
        {"akshara_id": a.id, "font_id": f, "image": f"{a.id}__{f}.png"}
        for a in enumerate_uyirmei()
        for f in fonts
    ]


def test_split_is_disjoint_and_covers_every_class():
    insts = _instances(2)
    asgn = assign_split(insts, eval_fraction=0.5, seed=42)
    per_akshara = {}
    for (aid, _font), split in asgn.items():
        per_akshara.setdefault(aid, set()).add(split)
    # every akshara (2 instances) has one train and one eval — disjoint, both covered
    assert all(s == {"train", "eval"} for s in per_akshara.values())


def test_split_is_deterministic_given_seed():
    insts = _instances(2)
    assert assign_split(insts, 0.5, 42) == assign_split(insts, 0.5, 42)


def test_split_seed_changes_assignment():
    insts = _instances(2)
    a = assign_split(insts, 0.5, 1)
    b = assign_split(insts, 0.5, 2)
    assert a != b  # different seed → at least some instances swap split


def test_single_instance_akshara_goes_to_train():
    insts = _instances(1)
    asgn = assign_split(insts, eval_fraction=0.5, seed=42)
    assert set(asgn.values()) == {"train"}
