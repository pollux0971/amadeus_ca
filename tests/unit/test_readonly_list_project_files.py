import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.planner.read_only_execution_gate import (  # noqa: E402
    EXCLUDED_DIR_NAMES, EXCLUDED_RELPATHS, LIST_FILES_MAX, READONLY_ALLOWLIST,
    SKILL_RUNNERS, _is_excluded_name, list_project_files,
)


def _make_tree(base: Path):
    (base / "src").mkdir()
    (base / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (base / "README.md").write_text("# readme\n", encoding="utf-8")
    # excluded dirs
    (base / ".git").mkdir(); (base / ".git" / "config").write_text("x", encoding="utf-8")
    (base / ".venv").mkdir(); (base / ".venv" / "pyvenv.cfg").write_text("x", encoding="utf-8")
    (base / "runs").mkdir(); (base / "runs" / "r.json").write_text("{}", encoding="utf-8")
    (base / "__pycache__").mkdir(); (base / "__pycache__" / "m.pyc").write_text("x", encoding="utf-8")
    # excluded files
    (base / ".env").write_text("OPENAI_API_KEY=should-not-appear\n", encoding="utf-8")
    (base / "config").mkdir(); (base / "config" / "config.json").write_text("{}", encoding="utf-8")
    (base / "password_and_api.txt").write_text("secret", encoding="utf-8")
    (base / "secret_notes.txt").write_text("x", encoding="utf-8")
    (base / "shot.png").write_text("x", encoding="utf-8")


def test_list_is_in_allowlist_and_has_runner():
    assert "list_project_files" in READONLY_ALLOWLIST
    assert "list_project_files" in SKILL_RUNNERS


def test_lists_relative_paths_and_basic_metadata_no_content():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp); _make_tree(base)
        r = list_project_files(str(base))
        assert r["status"] == "ok"
        assert r["content_read"] is False
        # result carries no file-content fields
        for k in ("content", "file_content", "contents", "text"):
            assert k not in r
        paths = {e["path"] for e in r["files"]}
        assert "README.md" in paths and "src/app.py" in paths
        # entries are relative + carry only path/is_dir/size
        for e in r["files"]:
            assert set(e.keys()) == {"path", "is_dir", "size"}
            assert not e["path"].startswith("/")


def test_excluded_dirs_and_files_never_listed():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp); _make_tree(base)
        r = list_project_files(str(base))
        paths = {e["path"] for e in r["files"]}
        for bad in (".env", "config/config.json", "password_and_api.txt",
                    "secret_notes.txt", "shot.png"):
            assert bad not in paths, bad
        for e in r["files"]:
            segs = set(e["path"].split("/"))
            assert not (segs & EXCLUDED_DIR_NAMES), e["path"]


def test_no_env_secret_value_in_output():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp); _make_tree(base)
        r = list_project_files(str(base))
        import json
        assert "should-not-appear" not in json.dumps(r)


def test_max_files_cap_truncates():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for i in range(20):
            (base / f"f{i:03}.txt").write_text("x", encoding="utf-8")
        r = list_project_files(str(base), max_files=5)
        assert r["file_count"] == 5
        assert r["truncated"] is True
        assert r["max_files"] == 5


def test_default_max_files_is_bounded():
    assert LIST_FILES_MAX == 200


def test_does_not_follow_symlink_escaping_root():
    with tempfile.TemporaryDirectory() as outer:
        outer_p = Path(outer)
        secret_outside = outer_p / "outside_secret.txt"
        secret_outside.write_text("nope", encoding="utf-8")
        repo = outer_p / "repo"; repo.mkdir()
        (repo / "inside.txt").write_text("ok", encoding="utf-8")
        link = repo / "escape"
        try:
            link.symlink_to(outer_p)  # points OUTSIDE repo root
        except (OSError, NotImplementedError):
            return  # symlinks unsupported here; skip
        r = list_project_files(str(repo))
        paths = {e["path"] for e in r["files"]}
        assert "inside.txt" in paths
        # the escaping symlink (and anything via it) must not be listed
        assert not any(p.startswith("escape") for p in paths)


def test_missing_dir_fails_gracefully():
    r = list_project_files("/nonexistent/path/xyz")
    assert r["status"] == "failed"


def test_excluded_helpers():
    assert _is_excluded_name(".env") and _is_excluded_name("id_rsa")
    assert _is_excluded_name("shot.png") and _is_excluded_name("creds.pem")
    assert not _is_excluded_name("app.py")
    assert ".git" in EXCLUDED_DIR_NAMES and "runs" in EXCLUDED_DIR_NAMES
    assert "config/config.json" in EXCLUDED_RELPATHS


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"[PASS] {name}")
