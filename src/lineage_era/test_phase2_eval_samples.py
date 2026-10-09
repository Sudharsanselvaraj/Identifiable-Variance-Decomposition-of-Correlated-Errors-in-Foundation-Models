"""Regression tests for per-question extraction from lm_eval samples.

The original extractor read only resps[0] (choice A's log-likelihood), so every
item predicted choice 0. These tests pin the fix on lm_eval-shaped samples.
"""
import pytest

from lineage_era.phase2_eval import _choice_logprobs, _samples_to_rows


def _sample(lls, answer, as_strings=False, filtered=True):
    cast = str if as_strings else (lambda x: x)
    s = {
        "doc": {"question": "q", "choices": ["a", "b", "c", "d"], "answer": answer},
        "resps": [[[cast(ll), cast(False)]] for ll in lls],
        "acc": float(max(range(len(lls)), key=lls.__getitem__) == answer),
    }
    if filtered:
        s["filtered_resps"] = [[cast(ll), cast(False)] for ll in lls]
    return s


@pytest.mark.parametrize("as_strings", [False, True])
@pytest.mark.parametrize("filtered", [False, True])
def test_one_logprob_per_choice(as_strings, filtered):
    s = _sample([-3.0, -0.5, -2.0, -4.0], answer=1, as_strings=as_strings,
                filtered=filtered)
    assert _choice_logprobs(s) == [-3.0, -0.5, -2.0, -4.0]


def test_predictions_vary_and_match_lm_eval_acc():
    samples = {"mmlu_x": [
        _sample([-0.1, -2.0, -3.0, -4.0], answer=0),
        _sample([-2.0, -0.1, -3.0, -4.0], answer=1),
        _sample([-2.0, -3.0, -0.1, -4.0], answer=3),
    ]}
    rows = _samples_to_rows("M", "org/m", samples)
    assert [r["predicted"] for r in rows] == [0, 1, 2]
    assert [r["correct"] for r in rows] == [1, 1, 0]


def test_disagreement_with_lm_eval_acc_raises():
    s = _sample([-0.1, -2.0, -3.0, -4.0], answer=0)
    s["acc"] = 0.0
    with pytest.raises(ValueError, match="disagree"):
        _samples_to_rows("M", "org/m", {"mmlu_x": [s]})
