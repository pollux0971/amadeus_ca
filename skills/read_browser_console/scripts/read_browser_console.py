import json


def summarize_console(messages):
    errors = [m for m in messages if m.get("type") == "error"]
    return {
        "console_errors": errors,
        "fatal_error_count": len(errors),
        "summary": f"{len(errors)} error(s) found",
        "evidence_ref": "artifacts/browser_console.json",
    }


if __name__ == "__main__":
    sample = [{"type": "error", "text": "Cannot read properties of undefined"}]
    print(json.dumps(summarize_console(sample), indent=2))
