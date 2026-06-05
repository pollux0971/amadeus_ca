from src.harness.sensory_filter import extract_protected_terms, filter_browser_console, filter_cli_log


def test_extract_protected_terms_keeps_file_and_port():
    text = "TypeError in src/App.jsx line 12 at http://localhost:5173"
    terms = extract_protected_terms(text)
    assert "src/App.jsx" in terms
    assert "localhost:5173" in terms


def test_filter_cli_log_keeps_error_lines():
    log = "npm notice something\nTraceback in app.py line 3\nexit code 1"
    obs = filter_cli_log(log)
    assert "Traceback" in obs.summary
    assert "exit code 1" in obs.summary


def test_filter_browser_console_keeps_error():
    log = "info ok\nReferenceError in src/App.jsx line 7"
    obs = filter_browser_console(log)
    assert "ReferenceError" in obs.summary
    assert "src/App.jsx" in obs.protected_terms
