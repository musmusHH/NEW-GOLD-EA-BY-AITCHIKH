> **Current UI:** v6.720 uses the Full Focus layout and four themes without GX9 bitmap dependencies. See [FOCUS_DESIGN.md](FOCUS_DESIGN.md) for current installation details. The reporting findings below remain applicable.

# Carryover trade performance fix

Updated source: `GOOOOLD X9 SETINGS.txt` (MQL4).

## Findings and changes

- The tracker and strategy performance only displayed closed history. Added an `OPEN (LIVE)` tracker row aggregating matching market positions regardless of age or original pending-order placement date. With live positions the table shows that row plus four recent closed-trade dates; otherwise it shows five closed-trade dates.
- Live P/L previously required the current magic number, while closed reporting allowed the configured magic/comment filter. Live reporting now uses that same filter. This can include an older-version X9 trade by comment under the default filter. Strict magic mode still intentionally excludes other magic numbers.
- Strategy trade counts and P/L now include live positions. Tooltips explain that win rates remain closed-only. Profit factor, expectancy and other closed-result metrics remain closed-only.
- The tracker previously collected only the first 128 distinct history dates before sorting, potentially omitting recent results on long histories. Its date storage now accommodates the loaded history.
- Untriggered/cancelled pending orders are not counted as executed trades. Once triggered, MT4 reports buy-stop/sell-stop positions as BUY/SELL.
- Entry, exit, risk controls and strict trade-management ownership have not changed. Reporting a legacy position does not grant permission to manage it.

## Validation

Run `python -m unittest discover -s tests -v` (Python and g++ required).
The test compiles the actual extracted MQL4-compatible reporting loop and matching helpers against C++ terminal stubs: buy/sell carryovers, legacy comment matching, strict magic filtering, unrelated-symbol/manual/pending exclusions, repeated refresh and removal from the live pool. Source contract checks cover history date storage and strict management ownership.

Full MetaEditor compilation and MT4 runtime testing are still required; this checkout has neither the MT4 toolchain nor the referenced GX9 bitmap resources.

## Install and demo-account checks

1. Use the updated text as the EA's `.mq4` source in your existing MT4 setup, retain its GX9 image resources, compile in MetaEditor and reload the EA.
2. In MT4 Account History, select **All History**. MQL4 can only read the history loaded by the terminal.
3. On a demo account, verify yesterday's triggered buy-stop and sell-stop trades appear in `OPEN (LIVE)`, including after reattaching the EA and across server midnight.
4. Close a position and verify it leaves the live total and appears in the row for its **close date**, without double counting. Closed totals keep the existing commission calculation.
5. Check filters if an older trade is still missing: its symbol and configured magic/comment criteria must match. A legacy trade with a different magic and a broker-replaced comment cannot safely be identified automatically.
