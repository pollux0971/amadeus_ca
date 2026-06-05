import re
import json


def detect_localhost_url(text: str):
    match = re.search(r"https?://(?:localhost|127\.0\.0\.1):\d+", text)
    return match.group(0) if match else None


def simulate_start_server(project_dir: str, preferred_command: str | None = None, timeout_sec: int = 30) -> dict:
    # MVP placeholder. Real implementation should use sandboxed subprocess runner.
    fake_log = "VITE ready in 100ms\nLocal: http://localhost:5173/"
    return {
        "status": "started",
        "server_url": detect_localhost_url(fake_log),
        "process_id": None,
        "log_ref": "artifacts/server.log",
        "error": None,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--preferred-command", default=None)
    parser.add_argument("--timeout-sec", type=int, default=30)
    args = parser.parse_args()
    print(json.dumps(simulate_start_server(args.project_dir, args.preferred_command, args.timeout_sec), indent=2))
