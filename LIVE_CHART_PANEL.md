# Live broker-data chart panel — v6.560

## Install

Use `gold_x9_FIXED.mq4` in `MQL4/Experts`, compile with a current MT4 MetaEditor, and reattach it. The text-source copy is kept identical for compatibility.

Requirements:
- The standard MT4 library `MQL4/Include/Canvas/Canvas.mqh` (installed with current MT4).
- The existing GX9 dashboard bitmap resources in `MQL4/Images/GX9`. These images are not included in this repository.

The new `showLiveChartPanel` input defaults to **true** and requires `showDashboardPanel`. Set it to **false** to return to the native chart. No additional DLLs, web service or price feed is used.

## What is real and what is custom

This is a custom display over the center of the native MT4 chart, not simulated prices. `CopyRates` supplies broker OHLC for the attached symbol/timeframe, including the forming candle; `SymbolInfoTick` supplies the latest bid/ask and quote timestamp. Refreshes are limited to five per second on ticks, with a one-second display-only timer. It cannot produce new prices while the broker feed is disconnected or the market is closed.

The blue line/badge shows **bid**. The footer shows the last broker quote time and a STALE indication after no fresh quote timestamp has been observed for a minute. Missing history produces a waiting message instead of synthetic candles.

The panel displays matching open positions (including carryovers), pending stop/limit orders, and each order's SL/TP. Matching uses the same symbol/magic/comment reporting identity as performance. Live P/L uses the existing dashboard commission estimate plus broker profit/swap, not a newly introduced accounting formula. Labels include tickets so levels can be associated with the correct position.

All order lines remain at their actual prices. Nearby labels occupy separate rows with connectors. Very long labels are shortened with `...`; hover over the panel for full order/price details. `TAG>` cycles label pages if there are too many levels to fit. All in-range level lines remain visible on every page.

Up to four non-overlapping closed-result badges are drawn at their candle/close-price coordinates from the existing result-tag cache. `drawResultTags`, the historical tag lookback and the existing cache still govern available results. Badges that would collide with the order-label region are omitted rather than piled on top of it.

## Controls

| Control | Action |
|---|---|
| `+` / `-` | Zoom to fewer/more candles (16–240) |
| `<` / `>` | Browse older/newer bars by half a window |
| `LIVE` | Return to the forming candle |
| `ALL` / `BARS` | Toggle price scaling: candles plus all order levels, or candles only (plus current quote in live view) |
| `TAG>` | Show the next page of order-level labels |

`ALL` makes distant stops/targets visible but can compress the candles. In `BARS`, off-scale levels retain labelled prices with `^`/`v` indicators; they are not falsely drawn at a different price. Order P/L remains **current**, including while browsing historical candles. This is not a historical account replay.

The custom panel is read-only: it does not support dragging levels to modify orders. MT4 remains responsible for execution. Native trade-level lines and old result boxes are hidden while the custom panel is active to avoid duplicate clutter. The prior native trade-level/foreground settings are restored on removal or fallback. Windows without at least 400×240 pixels of center space use the native chart instead. Existing side-panel minimum-width limitations remain unchanged.

## Validation and limitations

Run `python -m unittest discover -s tests -v` with Python and g++ installed. The tests execute extracted reporting and renderer code against MT4/C++ stubs. They cover quote/history input, level scaling, foreign-symbol exclusion, bounded pixel geometry across resizes, zoom/pan/live controls, new-bar anchoring, pagination, stale quotes, missing data, fallback, allocation failure and cleanup. Static checks also ensure the renderer never sends, closes or modifies orders.

**These are not native MQL4 compilation or broker integration tests.** This environment has no MetaEditor/MT4 and lacks the dashboard images. Compile and verify in a demo account before live use:

1. Compare visible OHLC/bid against MT4's Data Window and Market Watch on M5 and another timeframe.
2. Verify the four open positions, tickets, live P/L, pending buy/sell stops and each SL/TP against the Trade tab.
3. Zoom, browse history, return LIVE, and switch ALL/BARS; check that labels connect to the correct prices.
4. Trigger/cancel a pending order and close a position; confirm the next refresh updates the overlay without duplicates.
5. Resize, change themes/timeframes, detach/reattach, and disable `showLiveChartPanel`; check native chart settings and controls recover.
6. Test with missing history/disconnected quotes and with many closely spaced orders.

Trading signals, ownership of managed positions, order limits, stop management and risk controls are unchanged by this display feature.
