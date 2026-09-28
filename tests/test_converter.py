"""ConfigJSONConverter against the golden cases in examples/converter_test_cases.json."""

import json
from pathlib import Path

import pytest

from gsconfig import ConfigJSONConverter

CASES_FILE = Path(__file__).resolve().parent.parent / "examples" / "converter_test_cases.json"


def _cases():
    for group in json.loads(CASES_FILE.read_text(encoding="utf-8")):
        for n, (source, expected) in enumerate(group["data"]):
            yield pytest.param(group["version"], source, expected, id=f"{group['version']}-{n:02d}")


@pytest.mark.parametrize(("version", "source", "expected"), _cases())
def test_jsonify_matches_golden_case(version, source, expected):
    # WHY: compared through json.dumps, like the notebook the cases came from — it pins
    # key order and the int/float distinction (1 vs 1.0) that == on dicts would ignore.
    result = ConfigJSONConverter({"parser_version": version}).jsonify(source)
    assert json.dumps(result) == json.dumps(expected)


def test_every_available_version_has_golden_cases():
    covered = {group["version"] for group in json.loads(CASES_FILE.read_text(encoding="utf-8"))}
    assert covered == set(ConfigJSONConverter.AVAILABLE_VERSIONS)


def test_unknown_version_is_refused():
    with pytest.raises(ValueError):
        ConfigJSONConverter.validate_version("v3")
