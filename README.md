# Rate Checker

Fetches USD/EUR buy/sell rates from [rate.am](https://rate.am) and reports the
average rate for banks and for exchange offices, separately, emailed to
armine.torosyan@gmail.com every day at 6 PM Yerevan time.

## How it works

- `scripts/check_rates.py` fetches rate.am, parses the rate tables, and
  computes average buy/sell for USD and EUR — split into "banks" and
  "exchange offices".
- A scheduled Routine (owned by the Claude Code session, not cron on this
  machine) fires daily, runs the script, and emails the result to
  armine.torosyan@gmail.com via the Gmail MCP connector.

## Setup status

- [x] Scraper script written (`scripts/check_rates.py`)
- [ ] **Live validation** — rate.am (and every other external domain
      tested: cba.am, cb.am, acba.am, and unrelated sites) is currently
      blocked by this environment's network egress policy — a blanket
      "organization policy" denial at the proxy, not a per-domain issue.
      Once that's opened up (environment network settings, admin-controlled),
      run:
      ```
      pip install -r requirements.txt
      python3 scripts/check_rates.py --debug --email
      ```
      and adjust `SECTION_KEYWORDS` / `CURRENCY_HEADERS` in the script if
      the tables aren't detected correctly (rate.am's exact markup wasn't
      verified before writing this — the parser is generic on purpose but
      still needs a real test pass).
- [ ] Daily email Routine created (6 PM Yerevan / 14:00 UTC →
      armine.torosyan@gmail.com), pending the validation step above.

## Manual run

```
pip install -r requirements.txt
python3 scripts/check_rates.py --email
```

Prints an email-ready `Subject:` line followed by the body. Add `--debug` to
see which tables/sections were detected, or `--html-file page.html` to test
against a locally saved copy of the page instead of fetching live. Use
`--slack` instead of `--email` if Slack delivery is wanted again later.
