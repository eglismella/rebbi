import copy
import json

import pytest

from rebbi.verify import DEFAULT_KEY, passed, verify_report


@pytest.fixture
def key():
    return json.loads(DEFAULT_KEY.read_text(encoding="utf-8"))


def report_from(data, sections=range(1, 8)):
    body = "\n\n".join(f"## {n}. Section {n}\n\nFindings for section {n}." for n in sections)
    appendix = {k: data[k] for k in ("runtime_dependencies", "optional_groups", "imports", "unused_dependencies",
                                      "undeclared_imports", "unpinned")}
    return f"# Dependency audit\n\n{body}\n\n```json\n{json.dumps(appendix, indent=2)}\n```\n"


def failed(checks):
    return {c.name for c in checks if not c.ok}


def test_a_report_matching_the_key_passes(key):
    assert passed(verify_report(report_from(key), key))


def test_names_are_compared_loosely_but_values_exactly(key):
    data = copy.deepcopy(key)
    data["runtime_dependencies"][0]["name"] = "SQLite_FTS4"
    data["imports"]["click"] = ["./sqlite_utils\\cli.py", "sqlite_utils/utils.py"]
    assert passed(verify_report(report_from(data), key))


def test_optional_groups_are_compared_by_package_not_version(key):
    data = copy.deepcopy(key)
    data["optional_groups"]["test"] = ["pytest", "black>=24.1.1", "hypothesis", "cogapp"]
    assert passed(verify_report(report_from(data), key))
    data["optional_groups"]["test"] = ["pytest", "hypothesis", "cogapp"]
    assert failed(verify_report(report_from(data), key)) == {"optional groups"}


def test_a_report_that_stopped_early_fails(key):
    report = report_from(key, sections=range(1, 4)).split("```json")[0]
    checks = verify_report(report, key)
    assert not passed(checks)
    assert failed(checks) == {"seven numbered sections", "JSON appendix"}


def test_a_wrong_constraint_fails(key):
    data = copy.deepcopy(key)
    data["runtime_dependencies"][2]["constraint"] = ""
    assert failed(verify_report(report_from(data), key)) == {"runtime dependencies"}


def test_calling_an_optional_import_required_fails(key):
    data = copy.deepcopy(key)
    data["undeclared_imports"][0]["optional"] = False
    assert failed(verify_report(report_from(data), key)) == {"undeclared imports"}


def test_missing_an_importing_file_fails(key):
    data = copy.deepcopy(key)
    data["imports"]["pluggy"] = ["sqlite_utils/plugins.py"]
    assert failed(verify_report(report_from(data), key)) == {"imports per runtime dependency"}


def test_a_malformed_appendix_fails_closed(key):
    report = report_from(key).replace('"unpinned"', '"pinned"')
    assert not passed(verify_report(report, key))
    assert not passed(verify_report("## 1. x\n```json\n[1, 2]\n```", key))
