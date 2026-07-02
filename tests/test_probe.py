"""Probe/metric tests (TASK PA.003): ridge separates, CIs bracket accuracy, metric M is exposed."""

import numpy as np
import pytest

from ezhuthu_jepa.eval.akshara_probe import (
    METRIC_M_BUCKET,
    bootstrap_ci,
    fit_ridge,
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
