import json

from src.runner import (
    extract_jsonpath,
    evaluate_assertion,
    _compare,
    _get_operator,
    _get_expected,
    run_test,
)


class TestExtractJsonpath:
    def test_simple_key(self):
        assert extract_jsonpath({"a": 1}, "a") == 1

    def test_nested_key(self):
        assert extract_jsonpath({"a": {"b": 2}}, "a.b") == 2

    def test_list_index(self):
        assert extract_jsonpath({"a": [10, 20]}, "a.1") == 20

    def test_missing_key(self):
        assert extract_jsonpath({"a": 1}, "b") is None

    def test_dollar_prefix(self):
        assert extract_jsonpath({"x": 5}, "$.x") == 5

    def test_invalid_index(self):
        assert extract_jsonpath({"a": [1]}, "a.5") is None


class TestCompare:
    def test_eq(self):
        assert _compare(5, "eq", 5)
        assert not _compare(5, "eq", 6)

    def test_gt(self):
        assert _compare(10, "gt", 5)
        assert not _compare(3, "gt", 5)

    def test_contains(self):
        assert _compare("hello", "contains", "ell")
        assert not _compare("hello", "contains", "xyz")

    def test_regex(self):
        assert _compare("abc123", "regex", r"^[a-z]+\d+$")
        assert not _compare("abc", "regex", r"^\d+$")


class FakeResponse:
    def __init__(self, status_code=200, headers=None, text="", json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._text = text
        self._json_data = json_data

    def json(self):
        if self._json_data is not None:
            return self._json_data
        return json.loads(self._text)


class TestEvaluateAssertion:
    def test_status_pass(self):
        resp = FakeResponse(status_code=200)
        assert evaluate_assertion(resp, {"status": 200}, {}) is None

    def test_status_fail(self):
        resp = FakeResponse(status_code=404)
        err = evaluate_assertion(resp, {"status": 200}, {})
        assert err is not None
        assert "404" in err

    def test_jsonpath_found(self):
        resp = FakeResponse(json_data={"id": 42})
        assert evaluate_assertion(resp, {"jsonpath": "id", "eq": 42}, {}) is None

    def test_jsonpath_not_found(self):
        resp = FakeResponse(json_data={"id": 42})
        err = evaluate_assertion(resp, {"jsonpath": "name"}, {})
        assert err is not None
        assert "not found" in err

    def test_jsonpath_with_operator(self):
        resp = FakeResponse(json_data={"count": 100})
        err = evaluate_assertion(resp, {"jsonpath": "count", "gt": 50}, {})
        assert err is None

    def test_header_pass(self):
        resp = FakeResponse(headers={"X-Custom": "val"})
        assert evaluate_assertion(resp, {"header": "X-Custom", "value": "val"}, {}) is None

    def test_header_missing(self):
        resp = FakeResponse(headers={})
        err = evaluate_assertion(resp, {"header": "X-Missing"}, {})
        assert err is not None

    def test_ai_missing_deps(self):
        resp = FakeResponse(status_code=200, text="ok")
        err = evaluate_assertion(resp, {"ai": "response should be ok"}, {})
        assert err is not None
        assert "openai" in err or "anthropic" in err

    def test_unknown_assertion(self):
        resp = FakeResponse()
        err = evaluate_assertion(resp, {"unknown": True}, {})
        assert err is not None
        assert "Unknown" in err


class TestRunTest:
    def test_request_exception(self, mocker):
        mocker.patch("requests.request", side_effect=Exception("Connection failed"))
        result = run_test({
            "name": "fail",
            "request": {"url": "http://x.com", "method": "GET"},
            "asserts": [],
        })
        assert not result.passed
        assert "Connection failed" in result.errors[0]

    def test_successful_request(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_resp.headers = {}
        mock_resp.json.return_value = {"status": "ok"}
        mocker.patch("requests.request", return_value=mock_resp)

        result = run_test({
            "name": "pass",
            "request": {"url": "http://x.com", "method": "GET"},
            "asserts": [{"status": 200}],
        })
        assert result.passed

    def test_failing_assertion(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.status_code = 404
        mock_resp.text = "not found"
        mock_resp.headers = {}
        mock_resp.json.return_value = {}
        mocker.patch("requests.request", return_value=mock_resp)

        result = run_test({
            "name": "fail",
            "request": {"url": "http://x.com", "method": "GET"},
            "asserts": [{"status": 200}],
        })
        assert not result.passed


class TestGetOperator:
    def test_eq(self):
        assert _get_operator({"eq": 5}) == "eq"

    def test_no_operator(self):
        assert _get_operator({"status": 200}) is None


class TestGetExpected:
    def test_returns_value(self):
        assert _get_expected({"gt": 10}) == 10

    def test_none_when_missing(self):
        assert _get_expected({"status": 200}) is None
