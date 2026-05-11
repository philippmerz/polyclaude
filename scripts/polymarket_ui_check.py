#!/usr/bin/env python3
"""Polymarket UI-page warning monitor.

⚠ DRAFT / DO NOT USE — V1 produces false positives.

2026-05-11 smoke-test against active May-15 NO position revealed:
- HTML contains 4× "umaResolutionStatus":"resolved" tokens, but gamma-api
  confirms umaResolutionStatus=None for the viewed market. The "resolved"
  matches come from related-markets sidebar (showing other recently-resolved
  markets in the navigation chrome).
- __NEXT_DATA__ JSON blob NOT present in current Polymarket SSR (next.js may
  serve a streaming-react variant).
- Without a way to scope the regex match to the SPECIFIC market being viewed,
  the parser misreports active positions as "resolved" — false positive rate
  effectively 100% on active markets.

Decision: SCRAPPED for now. uma_status_check.py (gamma-api) is reliable and
covers the actual safety surface (umaResolutionStatus changes). The
hypothesized UI-lead-over-gamma race condition was not observed; gamma-api
showed all states correctly.

v2 alternative if needed: render via headless browser (Playwright) to capture
actual DOM warning banners. Heavy build (~4h) for marginal value given gamma-
api parity. Not pursuing unless gamma-api becomes unreliable.

KEEP FILE for future reference / restart possibility. NOT wired into cron.



The Polymarket React/Next.js UI shows safety-critical signals (umaResolutionStatus,
dispute warnings, "(Resolved)" suffix, "(Disputed)" badge) PROMINENTLY to human
traders. The data is embedded in the SSR HTML — accessible via plain HTTP GET
without JavaScript rendering.

This script:
1. For each held position (data-api/positions + decisions.json open trades)
2. Fetches https://polymarket.com/market/{slug} with browser-User-Agent
3. Parses SSR HTML for: umaResolutionStatus, umaResolutionStatuses, title-suffix
4. Cross-references with gamma-api/markets/{id}
5. Alerts on:
   - UI shows status but gamma doesn't (UI ahead of API — could happen on
     freshly-disputed markets)
   - Title contains "(Resolved)" / "(Disputed)" / "(Pending)" but data-api
     position still shows non-zero size (= unredeemed)
   - umaResolutionStatuses ladder has multiple stages (proposed → disputed,
     etc.)

Lesson source: 2026-05-08 R-U miss cost $16.73 because I monitored only
backend APIs while Polymarket UI showed "In Dispute" prominently from
~Aug 8 onward. Built only AFTER the miss; this script replicates the UI
safety surface for the LLM-trader operating on backend APIs.

Wired into daily_checkin step 1 alongside uma_status_check.

Usage:
    python scripts/polymarket_ui_check.py
    python scripts/polymarket_ui_check.py --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent


UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_ui_page(slug: str) -> dict:
    """Fetch market UI page and extract safety-signal fields. Returns:
    {
      "status": "resolved" | "disputed" | "proposed" | None,
      "statuses": list[str],  # the umaResolutionStatuses array
      "title_suffix": str,  # e.g. "(Resolved)", "(Disputed)"
      "pendingDeployment": bool,
      "deploying": bool,
      "fetched": bool,
      "error": str | None,
    }
    """
    url = f"https://polymarket.com/market/{slug}"
    out = {"status": None, "statuses": [], "title_suffix": "",
           "pendingDeployment": None, "deploying": None,
           "fetched": False, "error": None}
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get(url, headers={"User-Agent": UA})
            if r.status_code != 200:
                out["error"] = f"HTTP {r.status_code}"
                return out
            text = r.text
    except Exception as e:
        out["error"] = f"fetch err: {e}"
        return out

    out["fetched"] = True

    m = re.search(r'"umaResolutionStatus":\s*"([^"]+)"', text)
    if m:
        out["status"] = m.group(1)

    m = re.search(r'"umaResolutionStatuses":\s*"(\[[^"]+\])"', text)
    if m:
        try:
            out["statuses"] = json.loads(m.group(1).replace('\\"', '"'))
        except Exception:
            pass

    # Title suffix: " (Resolved)" / " (Disputed)" / " (Pending)" / " (Proposed)"
    m = re.search(r'<title>([^<]+)</title>', text)
    if m:
        title = m.group(1)
        for suffix in [" (Resolved)", " (Disputed)", " (Pending)", " (Proposed)", " (Closed)"]:
            if suffix in title:
                out["title_suffix"] = suffix.strip()
                break

    m = re.search(r'"pendingDeployment":\s*(true|false)', text)
    if m:
        out["pendingDeployment"] = (m.group(1) == "true")

    m = re.search(r'"deploying":\s*(true|false)', text)
    if m:
        out["deploying"] = (m.group(1) == "true")

    return out


def fetch_gamma_status(market_id: str) -> str | None:
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get(f"https://gamma-api.polymarket.com/markets/{market_id}")
            if r.status_code != 200:
                return None
            return r.json().get("umaResolutionStatus")
    except Exception:
        return None


def fetch_positions(addr: str) -> list[dict]:
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get("https://data-api.polymarket.com/positions",
                      params={"user": addr.lower(), "limit": 100, "sizeThreshold": 0.0})
            r.raise_for_status()
            return r.json() or []
    except Exception:
        return []


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--wallet", default="/home/philipp/secrets/wallet.json")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    addr = json.load(open(args.wallet))["address"]
    positions = fetch_positions(addr)

    print(f"# polymarket_ui_check: {len(positions)} positions, fetching UI for each...", file=sys.stderr)
    alerts = []
    rows = []
    for pos in positions:
        slug = pos.get("slug", "")
        if not slug:
            continue
        size = float(pos.get("size", 0) or 0)
        if size <= 0:
            continue
        ui = fetch_ui_page(slug)
        # Look up market_id via slug query
        try:
            with httpx.Client(timeout=15) as c:
                r = c.get("https://gamma-api.polymarket.com/markets", params={"slug": slug})
                if r.status_code == 200:
                    rj = r.json()
                    if isinstance(rj, list) and rj:
                        market_id = rj[0].get("id")
                    elif isinstance(rj, dict):
                        market_id = rj.get("id")
                    else:
                        market_id = None
                else:
                    market_id = None
        except Exception:
            market_id = None

        gamma_status = fetch_gamma_status(market_id) if market_id else None

        row = {
            "slug": slug,
            "size": size,
            "ui_status": ui.get("status"),
            "ui_statuses": ui.get("statuses"),
            "title_suffix": ui.get("title_suffix"),
            "gamma_status": gamma_status,
            "ui_fetched": ui.get("fetched"),
            "ui_error": ui.get("error"),
        }
        rows.append(row)

        # Alerts
        if ui.get("title_suffix") in ("(Resolved)", "(Closed)"):
            alerts.append({"slug": slug, "type": "UI_SHOWS_RESOLVED",
                           "msg": f"UI title has {ui['title_suffix']} but position size={size} (unredeemed?)"})
        if ui.get("status") in ("proposed", "disputed") and gamma_status not in ("proposed", "disputed"):
            alerts.append({"slug": slug, "type": "UI_AHEAD_OF_GAMMA",
                           "msg": f"UI status={ui['status']} but gamma_status={gamma_status} (UI ahead of API)"})
        if (ui.get("status") == "disputed") or "disputed" in (ui.get("statuses") or []):
            alerts.append({"slug": slug, "type": "UI_DISPUTED",
                           "msg": f"UI flags disputed state. ui_status={ui['status']} statuses={ui['statuses']}"})

    if args.json:
        print(json.dumps({"rows": rows, "alerts": alerts}, indent=2, default=str))
        return 0

    print(f"\n# polymarket_ui_check: {len(rows)} positions, {len(alerts)} alerts\n")
    print(f"{'Slug':<55} {'size':<5} {'ui':<12} {'gamma':<10} {'title':<14}")
    print("-" * 100)
    for r in rows:
        print(f"{r['slug'][:55]:<55} {r['size']:<5.1f} {str(r['ui_status']):<12} {str(r['gamma_status']):<10} {r['title_suffix']:<14}")

    print()
    if not alerts:
        print("(no alerts)")
    else:
        for a in alerts:
            print(f"  [{a['type']}] {a['slug']}: {a['msg']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
