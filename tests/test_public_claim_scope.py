"""Public summaries must not contradict the dated archive erratum."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_readme_preserves_chronology_and_validation_limits():
    text = (ROOT / "README.md").read_text()
    assert "Public history does not establish registration-before-execution" in text
    assert "Two Paper 5 filter-count rows remain unresolved" in text
    assert "Experimental hypotheses were pre-registered before execution" not in text
    assert "registrations were committed before execution" not in text
    assert "all claims are traceable" not in text
    assert "exactly where novel threats will live" not in text

def test_website_avoids_unsupported_global_preregistration():
    text = (ROOT / "docs/index.html").read_text()
    assert "A pre-registered characterization" not in text
    assert "exactly where a novel threat would sit" not in text
    assert "three byte-locked registration hashes" in text
    assert "t30, R=1000, k=25" in text


def test_website_distinguishes_positive_precision_from_top_bin():
    import json
    data = json.loads((ROOT / "data/results_summaries/calibration_results.json").read_text())
    distant = data["distant"]
    assert distant["positive_prediction"]["n_predicted_positive"] == 44
    assert distant["positive_prediction"]["tp"] == 3
    top = distant["reliability"][-1]
    assert top["n"] == 3 and top["mean_obs"] == 0
    text = (ROOT / "docs/index.html").read_text()
    assert "across all 44 distant positive calls, 3 are correct" in text
    assert "In the highest-confidence bin, 0 of 3 are correct" in text
    assert "drop-in rescue" not in text
