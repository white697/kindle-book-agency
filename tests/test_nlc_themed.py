"""Smoke tests for the themed (kids) NLC interior system. Run: python -m pytest tests -q"""

import json
import random
from pathlib import Path

from nlc import puzzles
from nlc.builder import build_interior, build_plan, default_spec
from nlc.lint import lint_plan, lint_spec

EXAMPLE = Path(__file__).resolve().parent.parent / "nlc" / "examples" / "football_girls_spec.json"


def _example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_builds_and_lints_clean(tmp_path):
    spec = _example()
    plan, warnings = build_plan(spec, tmp_path)
    assert len(plan) == spec["page_count"]
    assert lint_spec(spec) == [] and lint_plan(plan) == []
    assert not [w for w in warnings if "skipped" in w]
    build_interior(spec, plan, tmp_path / "interior.pdf")
    assert (tmp_path / "interior.pdf").stat().st_size > 50_000


def test_secret_word_is_placed_but_not_listed():
    data = puzzles.make_wordsearch(["BOOTS", "SOCKS", "CONES"], 10, "easy", random.Random(1), secret="STRETCH")
    secret = [p for p in data["placed"] if p.get("secret")]
    assert [p["word"] for p in secret] == ["STRETCH"]
    assert len(data["placed"]) == 4


def test_preset_is_buildable_and_flags_placeholders(tmp_path):
    spec = default_spec("kids_activity", "Test")
    plan, _ = build_plan(spec, tmp_path)
    build_interior(spec, plan, tmp_path / "i.pdf")
    assert any("EDIT" in w or "thin" in w or "words" in w for w in lint_spec(spec))


def test_lint_catches_generic_faults():
    spec = _example()
    spec["sections"] = [
        {"type": "log_table", "title": "Name: ____ / Date: ____", "count": 1, "columns": ["A"], "rows": 3},
        {"type": "gratitude", "count": 1},
        {"type": "lined", "count": 5},
        {"type": "pages", "items": [
            {"type": "doodle", "text": "Doodle here"},
            {"type": "prompt", "kind": "opinion", "text": "The position I like to play is... because..."}]},
        {"type": "wordsearch", "count": 1, "puzzles": [{"title": "T", "words": ["ONE", "TWO"]}]},
    ]
    found = " | ".join(lint_spec(spec))
    for needle in ("bare", "gratitude", "flat 'lined'", "no printed starter", "thin", "only 2 words"):
        assert needle in found, needle


def test_padding_is_flagged(tmp_path):
    spec = _example()
    spec["page_count"] = 110
    plan, _ = build_plan(spec, tmp_path)
    assert any("padding" in w for w in lint_plan(plan))


def test_skills_table_draws_every_row_label(tmp_path):
    spec = _example()
    plan, _ = build_plan(spec, tmp_path)
    skills = [kw for fn, kw in plan if fn.__name__ == "log_table" and kw.get("row_labels")]
    assert skills and all(len(kw["row_labels"]) == kw["rows"] if kw.get("rows") else True for kw in skills)
