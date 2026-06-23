from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def load_test_file(path: str) -> Dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict) or "tests" not in data:
        raise ValueError("YAML file must contain a 'tests' key with a list of tests")
    if not isinstance(data["tests"], list):
        raise ValueError("'tests' must be a list")
    return data


def validate_test(test: Dict[str, Any]) -> Optional[str]:
    if "name" not in test:
        return "Each test must have a 'name' field"
    if "request" not in test:
        return f"Test '{test.get('name', '?')}' must have a 'request' field"
    req = test["request"]
    if not isinstance(req, dict):
        return f"Test '{test['name']}': 'request' must be a dict"
    if "url" not in req:
        return f"Test '{test['name']}': request must have a 'url' field"
    method = req.get("method", "GET")
    if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
        return f"Test '{test['name']}': unsupported method '{method}'"
    if "asserts" not in test:
        return f"Test '{test['name']}' must have an 'asserts' field"
    if not isinstance(test["asserts"], list):
        return f"Test '{test['name']}': 'asserts' must be a list"
    for i, assertion in enumerate(test["asserts"]):
        if not isinstance(assertion, dict):
            return f"Test '{test['name']}': assert #{i} must be a dict"
    return None


def parse_tests(
    path: str, variables: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    data = load_test_file(path)
    tests = data["tests"]
    errors = []
    for test in tests:
        err = validate_test(test)
        if err:
            errors.append(err)
    if errors:
        raise ValueError("\n".join(errors))
    resolved = []
    for test in tests:
        resolved.append(_resolve_vars(test, variables or {}))
    return resolved


def _resolve_vars(obj: Any, variables: Dict[str, str]) -> Any:
    if isinstance(obj, str):
        for key, val in variables.items():
            obj = obj.replace("{{" + key + "}}", val)
        return obj
    elif isinstance(obj, dict):
        return {k: _resolve_vars(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_vars(item, variables) for item in obj]
    return obj
