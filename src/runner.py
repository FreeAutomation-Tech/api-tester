import time
import json as json_module
from typing import Any, Dict, List, Optional

import requests

from .ai_assert import ai_assert


def extract_jsonpath(data: Any, path: str) -> Any:
    parts = path.lstrip("$.").split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def evaluate_assertion(
    response: requests.Response, assertion: Dict[str, Any], variables: Dict[str, str]
) -> Optional[str]:
    if "status" in assertion:
        expected = assertion["status"]
        if response.status_code != expected:
            return (
                f"Expected status {expected}, got {response.status_code}"
            )
        return None

    if "jsonpath" in assertion:
        jp = assertion["jsonpath"]
        actual = extract_jsonpath(response.json(), jp)
        op = _get_operator(assertion)
        expected = _get_expected(assertion)
        if op and expected is not None:
            if not _compare(actual, op, expected):
                return (
                    f"jsonpath '{jp}' = {actual!r} "
                    f"does not satisfy {op} {expected!r}"
                )
        else:
            if actual is None:
                return f"jsonpath '{jp}' not found in response"
        return None

    if "header" in assertion:
        header_name = assertion["header"]
        actual = response.headers.get(header_name)
        expected = assertion.get("value")
        if expected is not None and actual != expected:
            return (
                f"Expected header '{header_name}' = {expected!r}, "
                f"got {actual!r}"
            )
        if actual is None:
            return f"Header '{header_name}' not found in response"
        return None

    if "ai" in assertion:
        try:
            result = ai_assert(
                assertion["ai"],
                response.status_code,
                response.text,
                variables,
            )
            if result:
                return f"AI assertion failed: {result}"
        except ImportError as e:
            return (
                f"AI assertion requires openai or anthropic: {e}"
            )
        return None

    return f"Unknown assertion type: {assertion}"


def _get_operator(assertion: Dict[str, Any]) -> Optional[str]:
    for op in ("eq", "neq", "gt", "gte", "lt", "lte", "contains", "regex"):
        if op in assertion:
            return op
    return None


def _get_expected(assertion: Dict[str, Any]) -> Any:
    for op in ("eq", "neq", "gt", "gte", "lt", "lte", "contains", "regex"):
        if op in assertion:
            return assertion[op]
    return None


def _compare(actual: Any, op: str, expected: Any) -> bool:
    try:
        if op == "eq":
            return actual == expected
        elif op == "neq":
            return actual != expected
        elif op == "gt":
            return actual > expected
        elif op == "gte":
            return actual >= expected
        elif op == "lt":
            return actual < expected
        elif op == "lte":
            return actual <= expected
        elif op == "contains":
            return expected in actual
        elif op == "regex":
            import re
            return bool(re.match(str(expected), str(actual)))
    except (TypeError, ValueError):
        return False
    return False


class TestResult:
    def __init__(
        self,
        name: str,
        passed: bool,
        duration: float,
        errors: Optional[List[str]] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.errors = errors or []
        self.status_code = status_code
        self.response_body = response_body


def run_test(
    test: Dict[str, Any], variables: Optional[Dict[str, str]] = None
) -> TestResult:
    start = time.time()
    variables = variables or {}
    req = test["request"]
    method = req.get("method", "GET").upper()
    url = req["url"]
    headers = req.get("headers", {})
    body = req.get("body")
    timeout = req.get("timeout", 30)

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body if isinstance(body, dict) else None,
            data=body if isinstance(body, str) else None,
            timeout=timeout,
        )
    except requests.RequestException as e:
        duration = time.time() - start
        return TestResult(
            name=test["name"],
            passed=False,
            duration=duration,
            errors=[str(e)],
        )

    duration = time.time() - start
    errors = []
    for assertion in test["asserts"]:
        err = evaluate_assertion(response, assertion, variables)
        if err:
            errors.append(err)

    try:
        body_preview = response.text[:500]
    except Exception:
        body_preview = "<binary>"

    return TestResult(
        name=test["name"],
        passed=len(errors) == 0,
        duration=duration,
        errors=errors,
        status_code=response.status_code,
        response_body=body_preview,
    )


def run_tests(
    tests: List[Dict[str, Any]], variables: Optional[Dict[str, str]] = None
) -> List[TestResult]:
    return [run_test(test, variables) for test in tests]


def print_results(
    results: List[TestResult], json_output: bool = False
) -> None:
    if json_output:
        data = [
            {
                "name": r.name,
                "passed": r.passed,
                "duration": round(r.duration, 3),
                "errors": r.errors,
            }
            for r in results
        ]
        print(json_module.dumps(data, indent=2))
        return

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name} ({r.duration:.2f}s)")
        if r.errors:
            for err in r.errors:
                print(f"       {err}")
    print(f"\nResults: {passed}/{total} passed")
    if passed < total:
        print(f"         {total - passed}/{total} failed")
