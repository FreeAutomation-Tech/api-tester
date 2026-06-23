import argparse
import sys

from .parser import parse_tests
from .runner import run_tests, print_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="API Tester — Declarative API testing from YAML"
    )
    parser.add_argument(
        "test_file",
        help="Path to YAML test file",
    )
    parser.add_argument(
        "--var",
        "-v",
        action="append",
        default=[],
        help="Variables in KEY=VALUE format (can be repeated)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    variables = {}
    for v in args.var:
        if "=" not in v:
            print(f"Error: variable '{v}' must be in KEY=VALUE format", file=sys.stderr)
            sys.exit(1)
        key, val = v.split("=", 1)
        variables[key] = val

    try:
        tests = parse_tests(args.test_file, variables)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    results = run_tests(tests, variables)
    print_results(results, json_output=args.json)

    if not all(r.passed for r in results):
        sys.exit(1)
