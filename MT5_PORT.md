# X9 MT5 — Hedging port / v7.000

## Status and scope

**Source implementation for validation — not yet compiled in MetaEditor 5 or run in a broker-connected MT5 terminal.** No EX5 binary is supplied. Passing the local regression suite does not prove native compilation, fills, visual behavior or profitability. Do not use real money before native compile, tester and demo acceptance.

Standalone deliverable: **[gold_x9_MT5.mq5](gold_x9_MT5.mq5)**. This is a trading EA, not merely a dashboard. It ports the MT4 v6.750 strategy and Raised Solid interface to MT5 hedging accounts. The original `.mq4` and text source are unchanged.

Included:
- Fractal/swing entry discovery; buy/sell pending orders; manual, tiered and risk-based lot sizing.
- Pending expiry, strict symbol/magic ownership, position limits, break-even, trailing, salvage, aged-loss handling and optional partial exits.
- Existing daily/equity drawdown halts, probation sizing and dead-window rules.
- Four Raised Solid themes, real broker candles, MOVE/CENTER/horizontal and vertical zoom, color-coded level text without diagonal leaders or result boxes.
- Open-first/pending trade table, per-position P/L, estimated TP/SL and successful trailing levels, separate tracker and closed-result EMA/DD.
- MT5 positions + pending-order snapshots, explicit position-ticket close/modify requests, and 64-bit tickets throughout the UI and strategy.

## Account requirements and safety defaults

- **Hedging only** (`ACCOUNT_MARGIN_MODE_RETAIL_HEDGING`). Netting and exchange accounts are rejected at initialization; they are not silently treated as hedging.
- `mt5AllowLiveTrading=false` is the default. Tester/demo use is allowed; a real account is rejected until this input is explicitly enabled. Trading permission is checked again for every request.
- Broker restrictions still apply. Requests are checked with `OrderCheck` and the `OrderSend` server retcode, not just the API's boolean result.
- Existing reporting can include comment-matched legacy trades, but management remains strictly restricted to the attached symbol and configured magic.
- Do not run two copies with the same symbol/magic or another EA managing those positions. Do not import an MT4 `.set` blindly: review every MT5 input.

## Install and compile

1. In **MT5**, choose **File → Open Data Folder**.
2. Copy **gold_x9_MT5.mq5** into `MQL5/Experts/` (or an Experts subfolder).
3. Open it in **MetaEditor 5**, press **F7**, and inspect all compiler errors/warnings. If compilation fails, keep live trading disabled and supply the exact error text/line numbers for correction.
4. No bridge include file needs to be installed: it is embedded in the `.mq5`. Only the standard current MT5 `Canvas/Canvas.mqh` is required. No GX9 BMPs or DLLs are required.
5. Test the EA on the broker's actual gold symbol (including its suffix) and intended timeframe. Attach to a **hedging demo account**. MT5 Algo Trading / EA trading permissions must be enabled for orders.
6. The Experts/Journal initialization line identifies **gold_x9 MT5 v7.000 (HEDGING)**.

## MT5-specific behavior

- MT5 does not have an MT4-style combined order pool: the adapter enumerates positions first, then pending orders. Unknown stop-limit types are not managed by this strategy.
- Closing uses `TRADE_ACTION_DEAL` with an explicit `position` ticket and opposite deal direction. SL/TP use `TRADE_ACTION_SLTP`; pending cancellation uses `TRADE_ACTION_REMOVE`. This avoids accidentally closing another hedged position on the same symbol.
- Pending orders use RETURN filling. Closures choose supported FOK/IOC; RETURN is allowed only for non-market execution. Prices are rounded to the symbol's tick size.
- Specified expiry is used when supported. Otherwise GTC is used if available and the existing EA expiry loop expires it locally; the terminal/EA must remain running. Symbols supporting neither mode are rejected rather than silently using DAY expiry.
- Uncertain/failed requests are not counted as success. Ambiguous timeouts are not blindly retried by the legacy retry loop. A timeout still needs inspection in the terminal before manual resubmission.
- History consists of **realized exit deals**, excluding entries, deposits, credits and canceled pending orders. Entry position identity supplies side, comment, magic and weighted entry price: a BUY closed by a SELL deal still reports BUY. OUT and OUT_BY are supported; netting INOUT reversals are intentionally unsupported.
- Partial closes and multiple execution fills may create several realized rows. Closed-trade counts/hold statistics can therefore differ from MT4 order-history counts. Incomplete broker history without the corresponding entry is skipped instead of attributing it to the EA.
- Transaction events invalidate the history snapshot. A five-second history-count check also detects later terminal history synchronization. Floating price ticks alone do not add curve samples; revised realized history can rebuild the curve.
- Displayed net P/L and TP/SL retain the original **estimated commission convention** (`0.07 per 0.01 lot`, in account currency), not an assertion of exact broker net costs. Actual deal commission/fees are available in the adapter but are not substituted into the existing dashboard formula. Compare raw deals separately in testing.
- No guarantee of identical MT4/MT5 results: broker feeds, spreads, execution, contract specifications and deal accounting differ.
- The inherited lot-step normalization primarily targets gold symbols using 0.01-lot steps. Confirm generated volumes and risk amounts against your broker's specifications before use.

## Acceptance checklist — required before live use

- Compile in current MetaEditor 5; resolve errors and review warnings.
- Confirm netting rejection and the real-account lock; never bypass these simply to run a test.
- Strategy Tester: **Every tick based on real ticks**, with visual mode for UI checks. Verify the tester account uses hedging.
- Check pending BUY/SELL entry, expiry (native and GTC/local), fills and position-limit behavior.
- Verify modification, full close and partial close target only the intended position ticket; include several same-symbol BUY/SELL positions and an unrelated magic number.
- Check break-even, trailing, salvage, aged loss, optional partial exits and drawdown halts using controlled inputs. Confirm rejected requests do not show successful trailing changes.
- Compare live rows to Trade and closed rows to History/Deals, including manual closure, partial closure and close-by. Verify deposits/credits are excluded from the realized curve.
- Test all four themes, MOVE/CENTER/zoom, resize with Terminal/Tester visible, and the supported 800×400 minimum client area. Restart and reattach; note session-local navigation/trailing evidence is not persisted.
- Use a hedging demo account after tester checks. Enable `mt5AllowLiveTrading` only after independent validation; this setting is not an endorsement of live readiness.

## Maintenance and local tests

`mt5/MT5Bridge.mqh` is the editable native adapter; `tools/build_mt5.py` applies explicit transformations to the unchanged MT4 source and embeds the adapter into the standalone file.

```sh
python tools/build_mt5.py
python tools/build_mt5.py --check
python -m unittest discover -s tests -v
```

Python and g++ are required. The 16 tests include existing rendering/risk/reporting checks, generated-source consistency, strategy-body comparison after API renaming, and compiled C++ bridge stubs for large tickets, pending/position routing, entry attribution, partial/close-by history, failed snapshots, request retcodes, filling/expiry, ownership and account safety gates. **These are not a native MQL5 compiler or an MT5 execution simulator.**
