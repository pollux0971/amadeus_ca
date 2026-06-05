import re

def detect_localhost_url(text: str):
    match = re.search(r"https?://(?:localhost|127\.0\.0\.1):\d+", text)
    return match.group(0) if match else None

def test_detect_localhost():
    log = "ready in 100ms\nLocal: http://localhost:5173/"
    assert detect_localhost_url(log) == "http://localhost:5173"

def test_no_url():
    assert detect_localhost_url("server failed") is None

if __name__ == "__main__":
    test_detect_localhost()
    test_no_url()
