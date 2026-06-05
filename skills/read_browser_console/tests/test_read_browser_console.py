def summarize_console(messages):
    errors = [m for m in messages if m.get("type") == "error"]
    return {
        "fatal_error_count": len(errors),
        "summary": f"{len(errors)} error(s) found",
        "console_errors": errors,
    }

def test_summarize_console_errors():
    result = summarize_console([
        {"type": "log", "text": "hi"},
        {"type": "error", "text": "Cannot read properties of undefined"},
    ])
    assert result["fatal_error_count"] == 1
    assert "Cannot read" in result["console_errors"][0]["text"]

if __name__ == "__main__":
    test_summarize_console_errors()
