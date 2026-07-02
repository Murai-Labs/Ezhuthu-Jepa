"""Probe/metric tests (TASK PA.003, P1.001b): ridge, CIs, metric M, and the McNemar comparator."""

import numpy as np
import pytest

from ezhuthu_jepa.eval.akshara_probe import (
    EPSILON_PP,
    METRIC_M_BUCKET,
    ComparisonError,
    ProbeConfig,
    ProbeConfigError,
    bootstrap_ci,
    compare_arms,
    fit_ridge,
    mcnemar,
    predict,
    stratified_metrics,
)


def test_ridge_separates_linearly_separable_classes():
    rng = np.random.default_rng(0)
    n_classes = 4
    centers = np.eye(n_classes, 8) * 5.0
    x = np.repeat(centers, 10, axis=0) + rng.normal(0, 0.1, (40, 8))
    y = np.repeat(np.arange(n_classes), 10)
    w = fit_ridge(x, y, n_classes, lam=0.1)
    assert (predict(x, w) == y).mean() > 0.95


def test_bootstrap_ci_brackets_accuracy_and_orders():
    correct = np.array([True] * 70 + [False] * 30)
    ci = bootstrap_ci(correct, n_boot=1000, seed=1)
    assert abs(ci["accuracy"] - 0.7) < 1e-9
    assert ci["ci_low"] <= ci["accuracy"] <= ci["ci_high"]
    assert ci["n"] == 100


def test_bootstrap_ci_is_deterministic():
    correct = np.array([True, False, True, True, False, True])
    assert bootstrap_ci(correct, 500, 7) == bootstrap_ci(correct, 500, 7)


def test_bootstrap_ci_empty_is_nan():
    ci = bootstrap_ci(np.array([], dtype=bool), 100, 0)
    assert ci["n"] == 0
    assert np.isnan(ci["accuracy"])


def _records():
    recs = []
    # q1_bottom: 6/10 correct; others perfect — metric M should read ~0.6
    for i in range(10):
        recs.append({"correct": i < 6, "bucket": "q1_bottom", "seam_source": "glyph", "font": "noto"})
    for i in range(10):
        recs.append({"correct": True, "bucket": "q4_top", "seam_source": "diff", "font": "nirmala"})
    return recs


def test_stratified_metrics_exposes_metric_M_and_strata():
    m = stratified_metrics(_records(), n_boot=500, seed=42)
    assert set(m) == {"overall", "metric_M", "by_bucket", "by_seam_source", "by_font"}
    # metric M is the bottom-quartile bucket accuracy (AC2)
    assert m["metric_M"] == m["by_bucket"][METRIC_M_BUCKET]
    assert abs(m["metric_M"]["accuracy"] - 0.6) < 1e-9
    assert set(m["by_seam_source"]) == {"glyph", "diff"}
    assert set(m["by_font"]) == {"noto", "nirmala"}
    assert abs(m["overall"]["accuracy"] - 0.8) < 1e-9


def test_stratified_metrics_deterministic():
    assert stratified_metrics(_records(), 400, 3) == stratified_metrics(_records(), 400, 3)


# --- P1.001b: McNemar comparator -----------------------------------------------------------------


def test_mcnemar_ignores_concordant_pairs_and_counts_discordants():
    # 40 concordant (both correct) carry no information; only b=8, c=2 discordant do.
    a = np.array([True] * 40 + [True] * 8 + [False] * 2)
    b = np.array([True] * 40 + [False] * 8 + [True] * 2)
    res = mcnemar(a, b)
    assert (res.b, res.c, res.n_discordant) == (8, 2, 10)


def test_mcnemar_uses_exact_binomial_when_discordants_are_few():
    a = np.array([True] * 8 + [False] * 2)
    b = np.array([False] * 8 + [True] * 2)
    res = mcnemar(a, b)
    assert res.method == "exact_binomial"
    # exact two-sided p for (b=8, c=2), n=10: 2 * sum_{i<=2} C(10,i) / 2^10 = 2*56/1024
    assert res.p_value == pytest.approx(2 * 56 / 1024)


def test_mcnemar_uses_chi2_when_many_discordants_and_detects_strong_effect():
    a = np.array([True] * 75 + [False] * 15)   # b: A right / B wrong on the first 75
    b = np.array([False] * 75 + [True] * 15)   # c: A wrong / B right on the last 15
    res = mcnemar(a, b)
    assert res.method == "chi2_continuity"
    assert res.b == 75 and res.c == 15
    assert res.p_value < 0.05        # χ² = (60-1)²/90 = 38.7 → clearly significant


def test_mcnemar_shape_mismatch_raises():
    with pytest.raises(ComparisonError):
        mcnemar(np.array([True, False]), np.array([True]))


def _arm(keys, correct):
    return [{"key": k, "correct": c, "bucket": METRIC_M_BUCKET} for k, c in zip(keys, correct)]


def test_compare_arms_reports_primary_and_secondary_verdicts_on_a_real_gap():
    keys = [f"i{n}" for n in range(200)]
    # Arm A: 60 % correct; Arm B: 90 % correct, strictly dominating A instance-by-instance.
    a_correct = [i < 120 for i in range(200)]
    b_correct = [i < 180 for i in range(200)]
    cmp = compare_arms(_arm(keys, a_correct), _arm(keys, b_correct), arm_a_name="block", arm_b_name="seam")
    assert cmp.metric == METRIC_M_BUCKET and cmp.n == 200
    assert cmp.acc_a == pytest.approx(0.60) and cmp.acc_b == pytest.approx(0.90)
    assert cmp.delta_pp == pytest.approx(30.0)
    assert cmp.significant_primary is True        # McNemar (primary)
    assert cmp.non_overlapping_ci is True         # CI (secondary)
    assert cmp.meets_epsilon is True and cmp.epsilon_pp == EPSILON_PP


def test_compare_arms_bonferroni_scales_p_and_can_flip_primary_verdict():
    keys = [f"i{n}" for n in range(120)]
    # A mild but real edge: discordant b=30, c=15 → χ² path, single-test significant.
    a_correct = [False] * 30 + [True] * 15 + [True] * 75
    b_correct = [True] * 30 + [False] * 15 + [True] * 75
    single = compare_arms(_arm(keys, a_correct), _arm(keys, b_correct), n_comparisons=1)
    corrected = compare_arms(_arm(keys, a_correct), _arm(keys, b_correct), n_comparisons=50)
    assert corrected.p_bonferroni == pytest.approx(min(1.0, single.p_bonferroni * 50))
    assert corrected.p_bonferroni >= single.p_bonferroni


def test_compare_arms_requires_identical_instances():
    with pytest.raises(ComparisonError):
        compare_arms(_arm(["a", "b"], [True, False]), _arm(["a", "c"], [True, False]))


def test_probe_config_requires_a_backend():
    with pytest.raises(ProbeConfigError):
        ProbeConfig(image_dir="x")  # neither index_jsonl nor a manifest pair
    ProbeConfig(image_dir="x", index_jsonl="idx.jsonl")  # ok
    ProbeConfig(image_dir="x", split_manifest="s.json", render_manifest="r.json")  # ok
