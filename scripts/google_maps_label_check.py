#!/usr/bin/env python3
"""Check one US-region Google Maps server response for an exact label string.

This is deliberately a rollout *signal*, not a resolution oracle. A single
server HTML response does not execute the client-rendered map canvas and cannot
establish what a majority of US users see; callers must use the observation
only to trigger a fresh, broader review.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from urllib.parse import quote_plus

import httpx


MAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/126 Safari/537.36"
)
# This is Google's non-personal consent-choice cookie, not an account cookie.
SOCS_COOKIE = "CAESHAgCEhJnd3NfMjAyNTA4MjYtMF9SQzEaAmVuIAEaBgiA_LyaBg"
SCHEMA_MARKERS = ("APP_INITIALIZATION_STATE", "window.APP_FLAGS", "Google Maps")
CONSENT_MARKERS = ("Before you continue to Google", "consent.google.com")


class LabelCheckError(RuntimeError):
    """The Maps response could not be safely interpreted."""


@dataclass(frozen=True)
class LabelObservation:
    query: str
    target_label: str
    control_label: str
    target_count: int
    control_count: int
    region: str
    language: str
    final_url: str

    @property
    def rollout_signal(self) -> bool:
        return self.target_count > 0


def check_google_maps_label(
    *,
    query: str,
    target_label: str,
    control_label: str,
    region: str = "us",
    language: str = "en",
    timeout: float = 20.0,
) -> LabelObservation:
    """Return exact-string counts from one Maps server response, failing closed.

    Schema markers reject interstitials and unrelated payloads. The control
    string confirms that the intended query survived into the response, but it
    can occur in query/SEO metadata and does not prove a rendered map label.
    Likewise, target_count > 0 is only a review signal and target_count == 0 is
    only "not present in this server payload," never proof about the canvas.
    """
    if not query or not target_label or not control_label:
        raise LabelCheckError("query, target_label, and control_label are required")

    url = MAPS_SEARCH_URL.format(query=quote_plus(query))
    try:
        response = httpx.get(
            url,
            params={"hl": language, "gl": region},
            headers={
                "User-Agent": USER_AGENT,
                "Cookie": f"SOCS={SOCS_COOKIE}",
                "Accept": "text/html,application/xhtml+xml",
            },
            follow_redirects=True,
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LabelCheckError(f"Google Maps request failed: {exc}") from exc

    text = response.text
    final_url = str(response.url)
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type:
        raise LabelCheckError(
            f"unexpected Google Maps content type {content_type or '<missing>'!r}"
        )
    if "consent.google." in final_url or any(marker in text for marker in CONSENT_MARKERS):
        raise LabelCheckError("Google consent/interstitial response; label state unknown")
    missing_markers = [marker for marker in SCHEMA_MARKERS if marker not in text]
    if missing_markers:
        raise LabelCheckError(
            "unexpected Google Maps response schema; missing " + ", ".join(missing_markers)
        )

    target_count = text.count(target_label)
    control_count = text.count(control_label)
    if target_count == 0 and control_count == 0:
        raise LabelCheckError(
            "Google Maps response contained neither target nor control label; state unknown"
        )

    return LabelObservation(
        query=query,
        target_label=target_label,
        control_label=control_label,
        target_count=target_count,
        control_count=control_count,
        region=region,
        language=language,
        final_url=final_url,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Observe one Google Maps label response (not proof of rollout majority)."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--target-label", required=True)
    parser.add_argument("--control-label", required=True)
    parser.add_argument("--region", default="us")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()
    try:
        observation = check_google_maps_label(
            query=args.query,
            target_label=args.target_label,
            control_label=args.control_label,
            region=args.region,
            language=args.language,
        )
    except LabelCheckError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2

    payload = asdict(observation)
    payload.update(
        {
            "ok": True,
            "rollout_signal": observation.rollout_signal,
            "interpretation": (
                "server-HTML string check only; not a rendered-map observation or "
                "proof of majority-US rollout/resolution"
            ),
        }
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
