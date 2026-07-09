# API Tester

Declarative API testing from YAML with AI-powered assertions.
Define your HTTP tests as YAML files, run them from the CLI.

## Quick Start

```bash
pip install pyyaml requests
api-tester examples/sample.yaml
```

## Example Test File

```yaml
tests:
  - name: Get user
    request:
      method: GET
      url: https://api.example.com/users/1
    asserts:
      - status: 200
      - jsonpath: id
        eq: 1
      - jsonpath: name
        contains: "John"
```

## Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `status` | Check HTTP status code | `status: 200` |
| `jsonpath` | Extract value from JSON body | `jsonpath: data.id` |
| `header` | Check response header | `header: Content-Type` |
| `eq/neq/gt/gte/lt/lte` | Compare operators | `jsonpath: count, gt: 0` |
| `contains` | Substring check | `jsonpath: name, contains: "John"` |
| `regex` | Regex match | `jsonpath: email, regex: "^.+@.+\\..+$"` |
| `ai` | Natural language assertion | `ai: "response contains a list of users"` |

## Variables

```bash
api-tester tests.yaml -v BASE_URL=https://api.example.com -v TOKEN=abc123
```

Use `{{VARIABLE_NAME}}` in YAML.

## AI Assertions

Requires `openai` or `anthropic` package:

```bash
pip install api-tester[ai]
```

Set `AI_PROVIDER=anthropic` (default: openai).

```yaml
asserts:
  - ai: "the response error message mentions authentication failure"
```
---
*If you find this useful, please consider giving it a star ⭐ — it helps others discover it too!*

*Thank you for your support! 🙏*
