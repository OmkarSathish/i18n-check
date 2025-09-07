# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tests for the repeat_values.py.
"""

from pathlib import Path
from typing import Dict

import pytest

from i18n_check.check.repeat_values import (
    analyze_and_generate_repeat_value_report,
    get_repeat_value_counts,
    i18n_src_dict,
    validate_repeat_values,
)
from i18n_check.utils import read_json_file

# repeat values across the repo
json_repeat_value_counts = get_repeat_value_counts(i18n_src_dict)

fail_checks_json = read_json_file(
    file_path=Path(__file__).parent.parent.parent
    / "src"
    / "i18n_check"
    / "test_frontends"
    / "all_checks_fail"
    / "test_i18n"
    / "test_i18n_src.json"
)
pass_checks_json = read_json_file(
    file_path=Path(__file__).parent.parent.parent
    / "src"
    / "i18n_check"
    / "test_frontends"
    / "all_checks_pass"
    / "test_i18n"
    / "test_i18n_src.json"
)


@pytest.mark.parametrize(
    "input_dict,expected_output",
    [
        # Empty dicts.
        ({}, {}),
        # Unicode/special characters.
        ({"key_0": "café", "key_1": "CAFÉ", "key_2": "café"}, {"café": 3}),
        (pass_checks_json, {}),
        # The second value will be filtered out by analyze_and_generate_repeat_value_report.
        (
            fail_checks_json,
            {
                "hello global!": 2,
                "hello single file!": 2,
                "hello multiple files!": 2,
                "this key is duplicated but the value is not": 2,
            },
        ),
    ],
)
def test_get_repeat_value_counts(
    input_dict: Dict[str, str], expected_output: Dict[str, int]
) -> None:
    """
    Test get_repeat_value_counts with various scenarios.
    """
    result = get_repeat_value_counts(input_dict)
    assert result == expected_output


def test_multiple_repeats_with_common_prefix(capsys) -> None:
    fail_result, fail_report = analyze_and_generate_repeat_value_report(
        fail_checks_json, get_repeat_value_counts(fail_checks_json)
    )
    pass_result, pass_report = analyze_and_generate_repeat_value_report(
        pass_checks_json, get_repeat_value_counts(pass_checks_json)
    )

    assert "Repeat value: 'hello global!'" in fail_report
    assert "Number of instances: 2" in fail_report
    assert (
        "Keys: i18n._global.hello_global, i18n._global.repeat_value_hello_global"
        in fail_report
    )
    assert "Suggested new key: i18n._global.CONTENT_REFERENCE" in fail_report

    # Result remain unchanged (not removed).
    assert fail_result == {
        "hello global!": 2,
        "hello single file!": 2,
        "hello multiple files!": 2,
    }
    assert pass_result == {}


def test_key_with_lower_suffix_ignored(capsys) -> None:
    i18n_src_dict = {
        "i18n.repeat_value_multiple_files": "Test",
        "i18n.repeat_value_single_file": "Test",
        "i18n.test_file.repeat_key_lower": "Test",
    }
    json_repeat_value_counts = {"test": 3}

    result, report = analyze_and_generate_repeat_value_report(
        i18n_src_dict, json_repeat_value_counts.copy()
    )

    assert "i18n.test_file.repeat_key_lower" not in report
    assert "Number of instances: 2" in report
    assert (
        "Keys: i18n.repeat_value_multiple_files, i18n.repeat_value_single_file"
        in report
    )
    assert "Suggested new key: i18n.test_file.CONTENT_REFERENCE" in report


def test_validate_repeat_values_behavior(capsys) -> None:
    with pytest.raises(SystemExit):
        validate_repeat_values(
            json_repeat_value_counts=get_repeat_value_counts(fail_checks_json),
            repeat_value_error_report="",
        )
        assert (
            "❌ repeat_values error: 1 repeat i18n value is present."
            in capsys.readouterr().out
        )

    validate_repeat_values(
        json_repeat_value_counts=get_repeat_value_counts(pass_checks_json),
        repeat_value_error_report="",
    )
    output = capsys.readouterr().out
    assert "✅ repeat_values success: No repeat i18n values found" in output


if __name__ == "__main__":
    pytest.main()
