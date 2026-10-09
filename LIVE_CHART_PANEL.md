> **Current release: v6.730 — Full Focus design 4.** See [FOCUS_DESIGN.md](FOCUS_DESIGN.md). The old sidebar layout and GX9 bitmap requirements below are historical; the current source draws the interface at runtime, has four themes and does not require BMP files.

# Live broker-data chart panel — v6.660

## Install

Use `gold_x9_FIXED.mq4` in `MQL4/Experts`, compile with a current MT4 MetaEditor, and reattach it. The text-source copy is kept identical for compatibility.

Requirements:
- The standard MT4 library `MQL4/Include/Canvas/Canvas.mqh` (installed with current MT4).
- The existing GX9 dashboard bitmap resources in `MQL4/Images/GX9`. These images are not included in this repository.

The new `showLiveChartPanel` input defaults to **true** and requires `showDashboardPanel`. Set it to **false** to return to the native chart. No additional DLLs, web service or price feed is used.

## What is real and what is custom

This is a custom display over the center of the native MT4 chart, not simulated prices. `CopyRates` supplies broker OHLC for the attached symbol/timeframe, including the forming candle; `SymbolInfoTick` supplies the latest bid/ask and quote timestamp. Refreshes are limited to five per second on ticks, with a one-second display-only timer. It cannot produce new prices while the broker feed is disconnected or the market is closed.

The blue line/badge shows **bid**. The panel hover tooltip shows the last broker quote time and a STALE indication after no fresh quote timestamp has been observed for a minute. Missing history produces a waiting message instead of synthetic candles.

The panel displays matching open positions (including carryovers), pending stop/limit orders, and each order's SL/TP. Matching uses the same symbol/magic/comment reporting identity as performance. Live P/L uses the existing dashboard commission estimate plus broker profit/swap, not a newly introduced accounting formula. Labels include tickets so levels can be associated with the correct position.

All order lines remain at their actual prices. The stacked order-label text and diagonal connectors are removed to keep candles readable. Order details are available in the table and panel hover tooltip. There is no visible LIVE/tick/page footer, TAG button, or TRADES button.

Up to four non-overlapping closed-result badges remain at their candle/close-price coordinates from the existing result-tag cache. The `drawResultTags` setting and historical lookback continue to control these result markers.

## Per-trade money table

The trade table is anchored near the bottom of the middle panel, just above TRADE TRACKER. Reclaiming the former footer space adds 44 pixels to the candle plot without shrinking trade rows.

A dedicated table below the candles shows **TICKET | TYPE | LIVE $ | TP~ $ | SL~ $** on USD accounts. Other accounts display their actual currency (for example EUR or USC), not a misleading dollar label.

- **LIVE**: current broker profit + accrued swap − the existing dashboard commission estimate. Pending orders show `Pending` rather than a fabricated live result.
- **TP~ / SL~**: estimated net P/L **from the entry price to that exit price**, not the remaining change from the current quote. Formula: signed price move ÷ broker price tick size × broker tick value × lots, plus currently accrued swap, minus the dashboard commission estimate. A trailing stop above a BUY entry can therefore show a positive SL amount.
- These are estimates, not guaranteed proceeds: conversion/tick value, future swap/commission and fill/slippage can change the final result. Missing broker tick size/value shows `N/A`; absent TP/SL shows `Not set`.
- Four trades are visible at normal panel heights. Smaller panels show one or two rows. **Clicking the trade table** cycles through all matching open positions first, then separate pending-order pages, with ticket sorting inside each group. The table updates alongside the chart and still displays when candle history is loading.
- Hover over the chart for full order-level details if a table value is shortened to fit.

## Controls

| Control | Action |
|---|---|
| `+` / `-` | Zoom to fewer/more candles (16–240) |
| `<` / `>` | Browse older/newer bars by half a window |
| `LIVE` | Return to the forming candle |
| `ALL` / `BARS` | Toggle price scaling: candles plus all order levels, or candles only (plus current quote in live view) |
| Click the trade table | Show the next page of trades (no visible paging button) |

`ALL` makes distant stops/targets visible but can compress the candles. In `BARS`, off-scale level lines are omitted; their details remain in the table/hover tooltip. They are not falsely drawn at a different price. Order P/L remains **current**, including while browsing historical candles. This is not a historical account replay.

The custom panel is read-only: it does not support dragging levels to modify orders. MT4 remains responsible for execution. Native trade-level lines and old result boxes are hidden while the custom panel is active to avoid duplicate clutter. The prior native trade-level/foreground settings are restored on removal or fallback. Windows without at least 400×240 pixels of center space use the native chart instead. Existing side-panel minimum-width limitations remain unchanged.

## Validation and limitations

Run `python -m unittest discover -s tests -v` with Python and g++ installed. The tests execute extracted reporting and renderer code against MT4/C++ stubs. They cover quote/history input, level scaling, foreign-symbol exclusion, bounded pixel geometry across resizes, zoom/pan/live controls, new-bar anchoring, pagination, stale quotes, missing data, fallback, allocation failure and cleanup. Static checks also ensure the renderer never sends, closes or modifies orders.

**These are not native MQL4 compilation or broker integration tests.** This environment has no MetaEditor/MT4 and lacks the dashboard images. Compile and verify in a demo account before live use:

1. Compare visible OHLC/bid against MT4's Data Window and Market Watch on M5 and another timeframe.
2. Verify the four open positions, tickets, live P/L, pending buy/sell stops and each SL/TP against the Trade tab.
3. Zoom, browse history, return LIVE, and switch ALL/BARS; check that horizontal levels match the correct prices.
4. Trigger/cancel a pending order and close a position; confirm the next refresh updates the overlay without duplicates.
5. Resize, change themes/timeframes, detach/reattach, and disable `showLiveChartPanel`; check native chart settings and controls recover.
6. Test with missing history/disconnected quotes and with many closely spaced orders.

Trading signals, ownership of managed positions, order limits, stop management and risk controls are unchanged by this display feature.

### Additional v6.580 demo checks

Compare each ticket with the MT4 Trade tab. Check both BUY and SELL targets/stops, a profitable trailing SL, unset SL/TP, pending orders, and table-click pagination. Verify currency labels on non-USD accounts. Automated tests additionally cover BUY/SELL cash signs, non-point-sized ticks, missing tick metadata, absent stops, pending status and currency headers.

## v6.600 — startup settings and dashboard layout

In EA Properties → Inputs:

- `chartStartBars` — starting candle count, clamped to 16–240 (default 64).
- `chartStartOffset` — how many bars back to start (default 0 = live).
- `chartStartFitOrders` — **false by default: BARS**; true starts in ALL mode.
- `hideOriginalChart` — true by default. While the custom panel is available, the underlying native chart colors match the dashboard panel and the native price/date scales and OHLC text are hidden. The custom chart's own price scale stays visible. Saved native appearance is restored when the custom panel is removed or falls back on a small window.

The runtime zoom, navigation and ALL/BARS buttons still work; reattaching the EA reapplies the startup inputs.

The unused S1–S8 rows are replaced with open BUY/SELL counts, pending BUY/SELL counts, open lots, spread, daily drawdown, average closed-trade holding time, closed-trade count and closed win rate. S9 trade count (open + closed) and total net P/L remain. All counts use the reporting filter, not a change to management ownership.

On normal-sized windows the strategy panel stretches with the available height, and the equity panel sits immediately below it, eight pixels above TRADE TRACKER. The existing small-window HUD minimum-size limitations still apply.

Demo checks: start with different bar counts/offsets, confirm BARS is the default, switch themes and resize, check native axes/candles are hidden while the custom axis remains visible, and detach/disable the custom panel to verify the native chart returns. Automated tests check the startup source wiring, native hide/restore behavior, replacement rows and normal-height layout geometry; full MetaEditor/MT4 testing is still required.


## v6.610 — native object cleanup and unambiguous counts

When `hideOriginalChart` is enabled and the custom chart is active, non-dashboard objects on the main native chart (old result boxes, lines, arrows and other drawings) have their timeframe visibility masks temporarily disabled. New objects are checked every half second. HUD/canvas/control objects remain visible. Original masks are restored on fallback or removal; user drawings are not permanently deleted. Current-EA native result tags continue to be replaced by the custom result markers as before.

STRATEGY / LIVE now displays explicit totals, for example:

- `OPEN TOTAL (B/S)` → `4 (B1 S3)` = four positions: one BUY, three SELL.
- `PENDING TOTAL (B/S)` → `13 (B3 S10)` = thirteen pending orders: three buys, ten sells. This is **not** a used/maximum limit.

Position totals, direction breakdowns, pending counts and floating P/L now come from one scan of the live order pool. Both stop and limit pending orders count. The same symbol/magic/comment reporting filter is retained; no other symbols are silently mixed in and management ownership is unchanged. The display timer refreshes statistics between ticks as well.

Regression scenarios include four positions plus thirteen mixed stop/limit pending orders, a pending order triggering into a market position, preservation of HUD objects, hiding newly-created native lines, and restoration of original drawing visibility masks. Compile and verify against the MT4 Trade tab on a demo account; these tests use terminal stubs rather than native MT4.


## v6.620 — open positions first in TRADES

The TRADES money table no longer interleaves active positions and pending orders by ticket age. All open BUY/SELL positions come first, with pending orders on separate pages. At normal panel height, four open positions therefore fill the first page even if there are many older pending tickets.

The table header shows explicit `OPEN` and `PENDING` totals. A compact `OPEN 1/1` or `PEND 1/4` indicator identifies the section/page (not an order limit). Click the table to move through pages; **LIVE** returns both the chart and table to their starting live/open view. No footer text or paging button has been reintroduced.

The per-ticket live P/L, TP and SL amounts and reporting filter are unchanged. Regression coverage includes four newer active tickets with thirteen older pending tickets, pending-only and empty accounts, paging and returning to LIVE.


## v6.630 — one continuous open-first list (supersedes separate pages)

TRADES now renders one list in this order: **all matching open BUY/SELL positions, then all matching pending orders**. There is no forced page break between the groups. Thus four open positions followed by older pending orders appear as four open rows first, then pending rows on the same page when space permits.

`chartTradeRows` defaults to **8** and can be set from 1 to 40. The table uses fewer rows for a short list and caps its height to preserve at least 100 pixels of candle plot when enough space is available. More table rows leave less room for candles. If the list cannot fit, clicking the table advances through the remaining rows; the header shows `PAGE n/m`, plus separate OPEN and PENDING totals. LIVE returns to page one. Reporting filters and trading logic are unchanged.

Tests verify the rendered ticket sequence with four newer open tickets and thirteen older pending tickets, not merely the totals. MetaEditor compilation and terminal verification are still required.


## v6.640 — TRAIL cash column

TRADES now includes a sixth column, **TRAIL $** (or the account's actual currency).

- `ON +2.50` means this EA confirmed a successful trailing-stop change and the current SL is that recorded stop. The amount is the estimated net result at that stop, calculated from entry with current lots, tick value, accrued swap and the existing commission estimate.
- `ON -1.20` is possible: trailing can tighten risk while the stop is still below breakeven. It is not a guarantee of protected profit.
- `-` means no currently matching, confirmed trailing update is known. Pending orders, removed SLs and stops changed to another price do not display ON.
- `ON N/A` means trailing was confirmed but broker tick metadata is unavailable for the money estimate.

Confirmation is recorded only in the successful OrderModify branch when the trailing candidate actually tightens SL. Failed changes, TP-only edits and breakeven-only changes do not activate the indicator. Entry/exit/risk rules are unchanged; the new hook stores display metadata only.

Tracking is session-local: after EA reload/restart, an existing SL is not guessed to be trailing. The column will show `-` until the next confirmed trailing change. Closed-ticket records are removed as the table refreshes. The amount updates with the position's current lot size and accrued swap.

Eight automated tests pass, including BUY/SELL money signs, stop changes/removal, pending exclusion, missing tick data, closed-ticket cleanup and success-branch wiring. Full MetaEditor compilation and demo validation are still required. Check that a real successful trailing update changes the displayed column on the next display refresh.


## v6.650 — closed-trade-only equity curve

The curve no longer takes periodic live AccountEquity samples. It is a cumulative closed-result curve: one starting balance anchor plus one point per matching closed BUY/SELL history record, ordered by close time and ticket. Net results retain the existing profit + swap − dashboard commission estimate convention.

Open positions, floating P/L, ticks and deposit/withdrawal records do not add points. Breakeven closures still add a point; partial closes count when MT4 exposes them as closed history records. Repeated refreshes of unchanged history do not append duplicates. New matching closures update the curve on the next dashboard refresh. History loading/filter changes or broker corrections to closed results rebuild the curve from the available matching history.

The initial balance anchor stays fixed during the running session so changes in live balance alone cannot move old points. On restart it is seeded again from the loaded history and current balance. MT4 Account History → All History controls which historical records are available. This display works even when `drawResultTags` is disabled.

Live account equity, open P/L, daily drawdown and the equity-curve risk breaker are **unchanged**; they continue to use live equity for protection. Repainting on resize/theme changes is allowed but does not change curve data.

Ten automated tests pass, including unchanged floating values, repeated refreshes, unordered history, ignored pending/deposit/unrelated records, zero-net closures, partial closes, incomplete history scans and ring-buffer capacity. Native MetaEditor compilation/demo checks remain necessary.


## v6.660 — continuous EMA-style curve and optional DD line

The disconnected rectangle marks have been replaced with a connected, two-pixel-wide canvas curve. Each adjacent pixel is joined, with bounded smooth interpolation between EMA samples (no interpolation overshoot).

New Inputs:

- `eqCurveEmaPeriod = 3`: EMA smoothing over closed-result samples, including the starting anchor. Set **1** for the unsmoothed closed-result values rendered as a continuous curve; allowed effective range 1–100. Smoothing is visual and does not change reported P/L, closed statistics or risk controls.
- `showEquityDDLine = false`: enable to overlay a red drawdown line.
- `equityDDLineColor`: choose the DD line color.

Both series still advance **only with closed-result history**. EMA and running-peak DD are computed before ring-buffer truncation, so selecting fewer visible samples does not restart the calculations. DD is calculated from **raw closed-result equity**, not its EMA: `(running peak - closed equity) / running peak × 100`, with zero used when the peak is non-positive. It is not the live daily drawdown guard.

The DD legend explicitly shows a separate percentage scale: 0% at the top and the labelled maximum at the bottom. Hover for the current EMA/DD values and scale explanation. The equity line uses its own monetary range; the two lines are not on a shared unit scale. The risk guard continues to use live equity unchanged.

Renderer tests check contiguous pixel segments, DD enabled/disabled, EMA and DD arithmetic, empty/one-point/flat data, sample limits, cleanup and canvas bounds. Ten automated tests pass. Native MT4 compilation and visual verification are still required.
