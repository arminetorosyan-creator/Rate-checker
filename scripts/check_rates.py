#!/usr/bin/env python3
"""
Fetches USD/EUR buy-sell rates from rate.am and prints average rates
for banks vs. exchange offices, either as JSON or as Slack-ready text.

This parser is deliberately generic (it scans every <table> on the page
rather than relying on hardcoded CSS selectors) because the exact markup
of rate.am has not yet been verified against a live fetch in this
environment. Run with --debug the first time against the real site to
see what sections/headers were detected, and adjust SECTION_KEYWORDS /
CURRENCY_HEADERS below if a table is misclassified or missed.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date

import requests
from bs4 import BeautifulSoup

RATES_URL = "https://rate.am/en"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Keywords used to classify a table (or its nearest heading) as covering
# banks vs. currency exchange offices. Matched case-insensitively against
# the table's own text and the text of preceding heading elements.
SECTION_KEYWORDS = {
    "banks": ["bank"],
    "exchange": ["exchange office", "exchange point", "currency exchange", "obmen"],
}

CURRENCY_HEADERS = {
    "usd": ["usd", "$", "dollar"],
    "eur": ["eur", "€", "euro"],
}
BUY_HEADERS = ["buy", "bid", "purchase"]
SELL_HEADERS = ["sell", "ask", "sale"]


@dataclass
class RateRow:
    institution: str
    usd_buy: float | None = None
    usd_sell: float | None = None
    eur_buy: float | None = None
    eur_sell: float | None = None


@dataclass
class Section:
    kind: str  # "banks" or "exchange"
    rows: list = field(default_factory=list)


def fetch_html(url: str = RATES_URL) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return resp.text


def _classify_table(table, soup) -> str | None:
    context_text = table.get_text(" ", strip=True).lower()
    heading = ""
    prev = table.find_previous(["h1", "h2", "h3", "h4", "caption"])
    if prev:
        heading = prev.get_text(" ", strip=True).lower()
    combined = f"{heading} {context_text[:200]}"
    for kind, keywords in SECTION_KEYWORDS.items():
        if any(k in combined for k in keywords):
            return kind
    return None


def _find_col_indexes(header_cells):
    """Given header cell texts, find column indexes for usd/eur buy/sell."""
    idx = {"usd_buy": None, "usd_sell": None, "eur_buy": None, "eur_sell": None}
    texts = [c.lower() for c in header_cells]
    current_currency = None
    for i, text in enumerate(texts):
        for cur, keys in CURRENCY_HEADERS.items():
            if any(k in text for k in keys):
                current_currency = cur
        if current_currency:
            if any(k in text for k in BUY_HEADERS):
                idx[f"{current_currency}_buy"] = i
            elif any(k in text for k in SELL_HEADERS):
                idx[f"{current_currency}_sell"] = i
    return idx


def _to_float(text: str):
    text = text.strip().replace(",", "")
    m = re.search(r"\d+(\.\d+)?", text)
    return float(m.group(0)) if m else None


def parse_sections(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    sections = []
    for table in soup.find_all("table"):
        kind = _classify_table(table, soup)
        if kind is None:
            continue
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = [c.get_text(" ", strip=True) for c in rows[0].find_all(["th", "td"])]
        col_idx = _find_col_indexes(header_cells)
        if not any(v is not None for v in col_idx.values()):
            continue

        section = Section(kind=kind)
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            texts = [c.get_text(" ", strip=True) for c in cells]
            institution = texts[0]
            if not institution:
                continue

            def get(field_name):
                i = col_idx[field_name]
                return _to_float(texts[i]) if i is not None and i < len(texts) else None

            row = RateRow(
                institution=institution,
                usd_buy=get("usd_buy"),
                usd_sell=get("usd_sell"),
                eur_buy=get("eur_buy"),
                eur_sell=get("eur_sell"),
            )
            if any([row.usd_buy, row.usd_sell, row.eur_buy, row.eur_sell]):
                section.rows.append(row)

        if section.rows:
            sections.append(section)
    return sections


def _avg(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None


def compute_averages(sections: list) -> dict:
    result = {}
    for kind in ("banks", "exchange"):
        matching = [s for s in sections if s.kind == kind]
        rows = [r for s in matching for r in s.rows]
        result[kind] = {
            "usd": {
                "buy": _avg([r.usd_buy for r in rows]),
                "sell": _avg([r.usd_sell for r in rows]),
                "n": len([r for r in rows if r.usd_buy or r.usd_sell]),
            },
            "eur": {
                "buy": _avg([r.eur_buy for r in rows]),
                "sell": _avg([r.eur_sell for r in rows]),
                "n": len([r for r in rows if r.eur_buy or r.eur_sell]),
            },
        }
    return result


def format_slack_message(averages: dict, as_of: str) -> str:
    def line(kind_label, currency):
        d = averages.get("banks" if kind_label == "Banks" else "exchange", {}).get(currency, {})
        buy, sell, n = d.get("buy"), d.get("sell"), d.get("n", 0)
        if buy is None or sell is None:
            return f"  {currency.upper()}: n/a (0 sources)"
        return f"  {currency.upper()}: buy {buy} / sell {sell} AMD  ({n} sources)"

    lines = [f"*rate.am daily AMD rates — {as_of}*", "", "*Banks (avg)*"]
    lines.append(line("Banks", "usd"))
    lines.append(line("Banks", "eur"))
    lines.append("")
    lines.append("*Exchange offices (avg)*")
    lines.append(line("Exchange", "usd"))
    lines.append(line("Exchange", "eur"))
    return "\n".join(lines)


def format_email_subject(as_of: str) -> str:
    return f"rate.am daily AMD rates — {as_of}"


def format_email_body(averages: dict, as_of: str) -> str:
    def line(kind, currency):
        d = averages.get(kind, {}).get(currency, {})
        buy, sell, n = d.get("buy"), d.get("sell"), d.get("n", 0)
        if buy is None or sell is None:
            return f"  {currency.upper()}: n/a (0 sources)"
        return f"  {currency.upper()}: buy {buy} / sell {sell} AMD  ({n} sources)"

    lines = [f"rate.am daily AMD rates — {as_of}", "", "Banks (avg)"]
    lines.append(line("banks", "usd"))
    lines.append(line("banks", "eur"))
    lines.append("")
    lines.append("Exchange offices (avg)")
    lines.append(line("exchange", "usd"))
    lines.append(line("exchange", "eur"))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=RATES_URL, help="Page to fetch (default: %(default)s)")
    parser.add_argument("--slack", action="store_true", help="Print Slack-ready text instead of JSON")
    parser.add_argument("--email", action="store_true", help="Print email-ready text (Subject: line + body) instead of JSON")
    parser.add_argument("--debug", action="store_true", help="Print detected sections/rows for troubleshooting")
    parser.add_argument("--html-file", help="Parse a locally saved HTML file instead of fetching")
    args = parser.parse_args()

    if args.html_file:
        with open(args.html_file, encoding="utf-8") as f:
            html = f.read()
    else:
        html = fetch_html(args.url)

    sections = parse_sections(html)

    if args.debug:
        print(f"Detected {len(sections)} matching table(s):", file=sys.stderr)
        for s in sections:
            print(f"  kind={s.kind} rows={len(s.rows)}", file=sys.stderr)
            for r in s.rows[:5]:
                print(f"    {r}", file=sys.stderr)
        if not sections:
            print(
                "  No tables matched SECTION_KEYWORDS/CURRENCY_HEADERS. "
                "The page may render tables via JavaScript, or use different wording — "
                "inspect the HTML and adjust check_rates.py.",
                file=sys.stderr,
            )

    averages = compute_averages(sections)
    as_of = date.today().isoformat()

    if args.slack:
        print(format_slack_message(averages, as_of))
    elif args.email:
        print(f"Subject: {format_email_subject(as_of)}")
        print()
        print(format_email_body(averages, as_of))
    else:
        print(json.dumps({"date": as_of, **averages}, indent=2))

    if not sections:
        sys.exit(2)


if __name__ == "__main__":
    main()
