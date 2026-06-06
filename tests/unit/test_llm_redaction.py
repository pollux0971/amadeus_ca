import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.llm.redaction import redact_text, redact_mapping, REDACTED

# Built at runtime so this file never contains a real-looking literal key.
SK = "sk-" + "a" * 40
SK_ANT = "sk-ant-" + "b" * 40
BEARER = "Bearer " + "c" * 30


def test_sk_pattern_redacted():
    out = redact_text(f"key={SK}")
    assert SK not in out and REDACTED in out


def test_sk_ant_pattern_redacted():
    out = redact_text(f"anthropic {SK_ANT} end")
    assert SK_ANT not in out and REDACTED in out


def test_bearer_token_redacted():
    out = redact_text(f"Authorization: {BEARER}")
    assert "c" * 30 not in out and REDACTED in out


def test_nested_mapping_redacted():
    obj = {"a": {"key": SK}, "list": [f"hdr {BEARER}", {"k": SK_ANT}]}
    out = redact_mapping(obj)
    flat = json.dumps(out)
    assert SK not in flat and SK_ANT not in flat and "c" * 30 not in flat
    assert out["a"]["key"] == REDACTED


def test_output_never_contains_original_secret():
    blob = f"line1 {SK}\nline2 {SK_ANT}\nline3 {BEARER}\n"
    out = redact_text(blob)
    for secret in (SK, SK_ANT, "c" * 30):
        assert secret not in out


def test_non_string_passthrough():
    assert redact_mapping(5) == 5
    assert redact_mapping(True) is True
    assert redact_mapping(None) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
