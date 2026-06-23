from typing import Dict, Optional


def _call_openai(instruction: str, status_code: int, body: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an API test assertion engine. "
                    "Given a natural language assertion, HTTP status code, "
                    "and response body, return 'PASS' if the assertion "
                    "holds, or explain why it fails."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Assertion: {instruction}\n"
                    f"Status: {status_code}\n"
                    f"Body: {body[:2000]}"
                ),
            },
        ],
        temperature=0.0,
        max_tokens=200,
    )
    return response.choices[0].message.content or ""


def _call_anthropic(instruction: str, status_code: int, body: str) -> str:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        temperature=0.0,
        system=(
            "You are an API test assertion engine. "
            "Given a natural language assertion, HTTP status code, "
            "and response body, return 'PASS' if the assertion "
            "holds, or explain why it fails."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Assertion: {instruction}\n"
                    f"Status: {status_code}\n"
                    f"Body: {body[:2000]}"
                ),
            }
        ],
    )
    return response.content[0].text if response.content else ""


def ai_assert(
    instruction: str,
    status_code: int,
    body: str,
    variables: Dict[str, str],
) -> Optional[str]:
    provider = variables.get("AI_PROVIDER", "openai").lower()
    try:
        if provider == "anthropic":
            result = _call_anthropic(instruction, status_code, body)
        else:
            result = _call_openai(instruction, status_code, body)
    except ImportError:
        raise
    except Exception as e:
        return f"AI call failed: {e}"

    if result.strip().upper() == "PASS":
        return None
    return result.strip()
