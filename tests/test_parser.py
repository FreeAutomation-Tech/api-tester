import json
import tempfile
from pathlib import Path

import pytest
import yaml

from src.parser import load_test_file, validate_test, parse_tests, _resolve_vars


def _write_yaml(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    tmp.write(content)
    tmp.close()
    return tmp.name


class TestLoadTestFile:
    def test_valid_yaml(self):
        path = _write_yaml("tests:\n  - name: test1\n    request:\n      url: https://example.com\n      method: GET\n    asserts:\n      - status: 200\n")
        data = load_test_file(path)
        assert "tests" in data
        assert len(data["tests"]) == 1
        Path(path).unlink()

    def test_missing_tests_key(self):
        path = _write_yaml("foo: bar\n")
        with pytest.raises(ValueError, match="'tests' key"):
            load_test_file(path)
        Path(path).unlink()

    def test_tests_not_list(self):
        path = _write_yaml("tests: not_a_list\n")
        with pytest.raises(ValueError, match="'tests' must be a list"):
            load_test_file(path)
        Path(path).unlink()


class TestValidateTest:
    def test_missing_name(self):
        err = validate_test({"request": {"url": "x"}, "asserts": []})
        assert err is not None
        assert "name" in err

    def test_missing_request(self):
        err = validate_test({"name": "t", "asserts": []})
        assert err is not None
        assert "request" in err

    def test_missing_url(self):
        err = validate_test({"name": "t", "request": {"method": "GET"}, "asserts": []})
        assert err is not None
        assert "url" in err

    def test_unsupported_method(self):
        err = validate_test({
            "name": "t", "request": {"url": "x", "method": "INVALID"}, "asserts": []
        })
        assert err is not None
        assert "unsupported" in err

    def test_missing_asserts(self):
        err = validate_test({"name": "t", "request": {"url": "x"}})
        assert err is not None
        assert "asserts" in err

    def test_valid(self):
        err = validate_test({
            "name": "t", "request": {"url": "x"}, "asserts": [{"status": 200}]
        })
        assert err is None


class TestParseTests:
    def test_parse_with_vars(self):
        path = _write_yaml(
            "tests:\n  - name: test1\n    request:\n      url: '{{BASE}}/api'\n      method: GET\n    asserts:\n      - status: 200\n"
        )
        tests = parse_tests(path, {"BASE": "https://example.com"})
        assert tests[0]["request"]["url"] == "https://example.com/api"
        Path(path).unlink()

    def test_parse_validation_error(self):
        path = _write_yaml("tests:\n  - name: t\n    request:\n      method: INVALID\n      url: x\n    asserts:\n      - status: 200\n")
        with pytest.raises(ValueError):
            parse_tests(path)
        Path(path).unlink()


class TestResolveVars:
    def test_string_replacement(self):
        result = _resolve_vars("Hello {{NAME}}", {"NAME": "World"})
        assert result == "Hello World"

    def test_dict_replacement(self):
        result = _resolve_vars({"url": "{{HOST}}/path"}, {"HOST": "https://x.com"})
        assert result["url"] == "https://x.com/path"

    def test_list_replacement(self):
        result = _resolve_vars(["{{A}}", "{{B}}"], {"A": "1", "B": "2"})
        assert result == ["1", "2"]

    def test_no_variables(self):
        result = _resolve_vars("hello", {})
        assert result == "hello"

    def test_non_string_unchanged(self):
        result = _resolve_vars(42, {"X": "y"})
        assert result == 42
