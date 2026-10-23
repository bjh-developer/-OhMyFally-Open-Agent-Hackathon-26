import csv

import pytest

from app.schemas import Match
from scripts.eval_resolver import evaluate, load_labels


def label(name, uen, status="agent_reviewed"):
    return {"supplier_name": name, "correct_uen": uen, "review_status": status,
            "reviewer": "test" if status != "pending" else "", "category": "test"}


def test_metrics_distinguish_wrong_links_missed_links_and_abstentions():
    labels = [label("A", "U1"), label("B", "U2"), label("C", "U3"),
              label("D", "NONE"), label("E", "NONE"), label("F", "U6"), label("G", "", "pending")]
    matches = [Match(supplier_name="A", uen="U1", confidence=1),
               Match(supplier_name="B", uen="wrong", confidence=1),
               Match(supplier_name="C"), Match(supplier_name="D"),
               Match(supplier_name="E", uen="wrong", confidence=1),
               Match(supplier_name="F", uen="U6", confidence=.9)]
    report = evaluate(labels, matches)
    metrics = report["overall"]
    assert metrics["accuracy"] == .5
    assert metrics["link_precision"] == .5
    assert metrics["link_recall"] == .5
    assert metrics["wrong_links"] == 2
    assert metrics["missed_links"] == 1
    assert metrics["correct_abstentions"] == 1
    assert metrics["critic_accepted_links"] == 3
    assert metrics["critic_link_recall"] == .25
    assert report["pending_excluded"] == 1
    assert report["human_reviewed"]["accuracy"] is None


def test_missing_prediction_is_an_error_not_a_negative_label():
    with pytest.raises(ValueError):
        evaluate([label("A", "NONE")], [])


@pytest.mark.parametrize("rows", [
    [label("A", "")],
    [label("A", "U1"), label("A", "U2")],
    [label("A", "U1", "pending")],
])
def test_invalid_labels_are_rejected(tmp_path, rows):
    path = tmp_path / "labels.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError):
        load_labels(path)
