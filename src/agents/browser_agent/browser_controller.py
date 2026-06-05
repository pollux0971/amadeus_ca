from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BrowserObservation:
    url: str
    title: str
    dom_summary: str
    console_errors: list[str]


class BrowserController:
    '''
    Placeholder browser controller.

    Replace this with Playwright or browser-use implementation:
    - open_url
    - extract_dom_summary
    - read_console_errors
    - click
    - screenshot
    '''

    def open_url(self, url: str) -> BrowserObservation:
        return BrowserObservation(
            url=url,
            title="placeholder",
            dom_summary="Browser automation placeholder. Implement with Playwright.",
            console_errors=[],
        )
