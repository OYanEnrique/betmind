import json
import re
import sys


def main():
    # Read input from stdin
    input_data = sys.stdin.read().strip()

    # Default to scanning raw input text
    command_text = input_data

    # Try parsing as JSON to extract tool arguments if available
    try:
        data = json.loads(input_data)
        if isinstance(data, dict):
            # Check common keys for command line arguments in tool calls
            command_text = (
                data.get("CommandLine")
                or data.get("command")
                or data.get("args", {}).get("CommandLine")
                or input_data
            )
    except Exception:
        pass

    # Normalize command for checks
    normalized_cmd = command_text.strip().lower()

    # Destructive pattern checks
    destructive_patterns = [
        r"\brm\s+-rf\b",
        r"\brm\s+-f\s+-r\b",
        r"\brm\s+-r\s+-f\b",
        r"\bformat\b",
        r"\bdel\s+/s\b",
        r"\brd\s+/s\b",
    ]

    for pattern in destructive_patterns:
        if re.search(pattern, normalized_cmd):
            print(
                f"ERROR: Destructive command blocked by validate_tool_call.py: '{command_text}'",
                file=sys.stderr,
            )
            sys.exit(1)

    # If safe, exit with success
    sys.exit(0)


if __name__ == "__main__":
    main()
