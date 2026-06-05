def is_localhost(url: str) -> bool:
    return url.startswith("http://localhost") or url.startswith("http://127.0.0.1")

def test_localhost_url():
    assert is_localhost("http://localhost:5173")
    assert is_localhost("http://127.0.0.1:8000")

def test_external_url_rejected():
    assert not is_localhost("https://example.com")

if __name__ == "__main__":
    test_localhost_url()
    test_external_url_rejected()
