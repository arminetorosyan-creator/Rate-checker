# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script tool that fetches USD/EUR buy/sell exchange rates from
[rate.am](https://rate.am), computes average buy/sell rates split into
"banks" vs. "exchange offices", and formats the result for email or Slack
delivery. A scheduled Routine (owned by a Claude Code session, not system
cron) is meant to run it daily at 6 PM Yerevan time and email the result to
armine.torosyan@gmail.com via the Gmail MCP connector.

## Commands

```
pip install -r requirements.txt

# Manual run, email-ready output
python3 scripts/check_rates.py --email

# Debug: show which tables/sections were detected on the page
python3 scripts/check_rates.py --debug --email

# Test against a locally saved copy of the page instead of fetching live
python3 scripts/check_rates.py --html-file page.html --debug

# Slack-ready text instead of email
python3 scripts/check_rates.py --slack

# Default: raw JSON of computed averages
python3 scripts/check_rates.py
```

There is no test suite, linter, or build step in this repo — it's one
dependency-light script (`scripts/check_rates.py`).

## Architecture

Everything lives in `scripts/check_rates.py`, structured as a pipeline:

1. `fetch_html()` — GETs `RATES_URL` (or reads `--html-file` instead).
2. `parse_sections()` — scans **every** `<table>` on the page (no hardcoded
   CSS selectors) and classifies each one as `"banks"` or `"exchange"` by
   matching `SECTION_KEYWORDS` against the table's text and its nearest
   preceding heading. Column indexes for USD/EUR buy/sell are located
   per-table via `CURRENCY_HEADERS`/`BUY_HEADERS`/`SELL_HEADERS` rather than
   fixed positions, since the exact markup of rate.am hasn't been verified
   against a live fetch.
3. `compute_averages()` — averages buy/sell per currency across all rows in
   each section kind.
4. `format_email_body()` / `format_slack_message()` — render the averages
   dict into the two output formats; `main()` picks one via `--email`/`--slack`
   (default: JSON).

Because the parser is generic-by-necessity, `SECTION_KEYWORDS` and
`CURRENCY_HEADERS` (near the top of the file) are the first place to adjust
if a table is misclassified or missed — run with `--debug` first to see what
was detected. If `--debug` reports zero matching tables, the page likely
renders tables via JavaScript or uses different wording than expected.

## Known status

Per README.md: this environment's network egress policy currently blocks
rate.am (and every other external domain tested), so the parser has not yet
been validated against a live fetch. Treat `SECTION_KEYWORDS`/
`CURRENCY_HEADERS` as unverified until a real `--debug` run against the live
site succeeds.
