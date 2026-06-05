from pathlib import Path
import tempfile

def is_safe_relative_path(path: str) -> bool:
    p = Path(path)
    return not p.is_absolute() and ".." not in p.parts

def test_safe_path():
    assert is_safe_relative_path("src/App.tsx")
    assert not is_safe_relative_path("../secret.txt")
    assert not is_safe_relative_path("/etc/passwd")

if __name__ == "__main__":
    test_safe_path()
