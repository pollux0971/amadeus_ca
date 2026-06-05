import json


def is_localhost(url: str) -> bool:
    return url.startswith("http://localhost") or url.startswith("http://127.0.0.1")


def open_localhost_browser(server_url: str) -> dict:
    if not is_localhost(server_url):
        return {"status": "failed", "error": "invalid_url_not_localhost"}
    return {
        "status": "opened",
        "url": server_url,
        "title": "placeholder",
        "dom_summary": "Placeholder DOM summary. Replace with Playwright/browser-use.",
        "screenshot_ref": None,
        "console_errors": [],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("server_url")
    args = parser.parse_args()
    print(json.dumps(open_localhost_browser(args.server_url), indent=2))
