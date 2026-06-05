from __future__ import annotations

import importlib.util
import inspect
import traceback
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

UNIT_DIR = ROOT / "tests" / "unit"


def _install_pytest_shim() -> None:
    """Provide a tiny pytest-compatible module when pytest is not installed,
    so pytest-style unit tests (pytest.raises / mark / fixture) still run under
    this no-dependency runner. A real pytest install always takes precedence.
    """
    try:
        import pytest  # noqa: F401
        return
    except ImportError:
        pass

    import types
    from contextlib import contextmanager

    shim = types.ModuleType("pytest")

    class _Raises:
        def __init__(self, expected, match=None):
            self.expected = expected
            self.match = match
            self.value = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            if exc_type is None:
                raise AssertionError(f"DID NOT RAISE {self.expected!r}")
            if not issubclass(exc_type, self.expected):
                return False  # propagate unexpected exception
            if self.match is not None:
                import re

                assert re.search(self.match, str(exc)), f"pattern {self.match!r} not in {exc!r}"
            self.value = exc
            return True  # swallow the expected exception

    def raises(expected, match=None):
        return _Raises(expected, match=match)

    def fixture(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        def deco(fn):
            return fn
        return deco

    @contextmanager
    def _skip_ctx(*a, **k):
        yield

    class _Mark:
        def __getattr__(self, _name):
            def deco(*a, **k):
                if a and callable(a[0]):
                    return a[0]
                return lambda fn: fn
            return deco

    def skip(reason=""):
        raise _Skipped(reason)

    class _Skipped(Exception):
        pass

    def approx(expected, rel=1e-6, abs_tol=1e-12):
        class _Approx:
            def __eq__(self, other):
                return abs(other - expected) <= max(rel * abs(expected), abs_tol)

        return _Approx()

    shim.raises = raises
    shim.fixture = fixture
    shim.mark = _Mark()
    shim.skip = skip
    shim.Skipped = _Skipped
    shim.approx = approx
    sys.modules["pytest"] = shim


_install_pytest_shim()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"unittest_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    test_files = sorted(UNIT_DIR.glob("test_*.py"))
    if not test_files:
        print("[FAIL] no unit tests found under tests/unit/")
        return 1

    total = passed = failed = skipped = 0
    failures: list[str] = []

    for path in test_files:
        try:
            module = load_module(path)
        except Exception:  # noqa: BLE001 - import error counts as a failure
            failed += 1
            failures.append(f"{path.name} (import error)")
            print(f"[FAIL] {path.name} :: import\n{traceback.format_exc()}")
            continue

        for name, fn in sorted(vars(module).items()):
            if not (name.startswith("test_") and inspect.isfunction(fn)):
                continue
            # Skip pytest-style fixture tests (functions that require args).
            required = [
                p
                for p in inspect.signature(fn).parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
            ]
            if required:
                skipped += 1
                print(f"[SKIP] {path.name}::{name} (requires fixtures: {[p.name for p in required]})")
                continue

            total += 1
            try:
                fn()
                passed += 1
                print(f"[PASS] {path.name}::{name}")
            except Exception:  # noqa: BLE001
                failed += 1
                failures.append(f"{path.name}::{name}")
                print(f"[FAIL] {path.name}::{name}\n{traceback.format_exc()}")

    print(f"\n{passed}/{total} passed, {failed} failed, {skipped} skipped")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
