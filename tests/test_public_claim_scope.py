"""Public summaries must not contradict the dated archive erratum."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_readme_preserves_chronology_and_validation_limits():
    text = (ROOT / "README.md").read_text()
    assert "Public history does not establish registration-before-execution" in text
    assert "Two unsupported Paper 5 filter-count rows are explicitly corrected" in text
    assert "Experimental hypotheses were pre-registered before execution" not in text
    assert "registrations were committed before execution" not in text
    assert "all claims are traceable" not in text
    assert "records an unresolved Paper 5 table discrepancy" not in text
    claims = (ROOT / "docs/CLAIMS_TO_EVIDENCE.md").read_text()
    assert "unresolved Paper 5 table discrepancy" not in claims
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

def test_registration_file_hashes_and_public_descriptions_agree():
    """The source checker records file identity, not preregistration timing."""
    import ast

    checker = (ROOT / "scripts/ci/verify_prereg_locks.py").read_text()
    tree = ast.parse(checker)
    assignment = next(
        item
        for item in tree.body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "EXPECTED"
                for target in item.targets)
    )
    assert len(ast.literal_eval(assignment.value)) == 3
    assert "Public history does not establish" in checker
    assert "via SHA256 before any experiment ran" not in checker

    status = (ROOT / "STATUS.md").read_text()
    assert "public history does not establish registration-before-execution" in status
    assert "Hypothesis and success criterion committed (as text file) before experiment" not in status

    figure_source = (ROOT / "scripts/build_summary_figure.py").read_text()
    assert "3 verified registration hashes" in figure_source
    assert "4 SHA256-locked pre-registrations" not in figure_source
    assert "9,360 pre-registered cells" not in figure_source

    readme = (ROOT / "README.md").read_text()
    assert "Historical figure-footer correction" in readme
    assert "archived image is" in readme
