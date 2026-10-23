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
