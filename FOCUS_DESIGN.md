# X9 Full Focus — design 4 / v6.700

Implements the selected **Graphite Full Focus** layout with four complete palettes:

1. **GRAPHITE** (default) — charcoal and soft silver-blue.
2. **LIGHT** — white/slate with blue accents and darker profit/loss colors for readability.
3. **MIDNIGHT** — navy with blue accents.
4. **EMERALD** — dark green with mint accents.

## Theme button

Click **THEME: GRAPHITE >** in the top-right header to cycle through all four. It recolors the chart, candles, order lines, table, controls, header, tracker and closed-equity curve. It does not invoke OnInit, reset trade/risk state, reset chart zoom/history offset, or place/modify/close orders.

`hudTheme` selects the initial theme when the EA is attached. The button selection survives resizing but is not persisted across reattaching/restarting; the input is reapplied. Old `.set` files used a six-theme numeric enum; select the new named value explicitly after loading an older settings file.

## Layout

- Compact header with status, live spread/bar countdown and theme button.
- Six summary cards: equity, balance, open P/L, daily DD, open positions and pending orders. Hover for account currency, margin details, direction breakdowns and DD limits.
- **Full-width broker-data chart**, no permanent left/right sidebars.
- Bottom-left trade dock: **ticket, type, lots, live P/L, TP, SL, TRAIL**, with all matching market positions before pending orders. Click inside the table to page; LIVE returns to the first page. Clicking the equity dock does not change the trade page.
- Bottom-right **closed equity** dock: continuous EMA-style line and optional DD line, still based only on closed-result history.
- A separate, full-width **TRADE TRACKER** at the bottom, retaining the live aggregate row and recent realized daily results. Wide windows include the five performance summaries; compact windows keep win rate and profit factor in the heading.

The chart uses actual broker candles/quotes. Net values retain the existing commission-estimate convention. TP/SL/TRAIL estimates, trailing-update confirmation, order matching, closed-only equity history, and native-chart hiding/restoration remain in effect.

## Screen sizes

The layout uses actual chart-client dimensions, not the full desktop resolution. It supports **800×560 and larger** chart areas. The trade dock limits its row count to leave at least 100 pixels of candle plot. Four rows are requested by default; small windows may display fewer, and `chartTradeRows` can request more. Pagination always keeps additional trades accessible.

At less than 800×560, the EA shows a resize notice and falls back to the native chart rather than drawing an overlapping fixed-size dashboard. Trading logic continues unchanged. Long values are shortened only for display; hover shows full text. Minimize/restore and theme changes rebuild visual resources, not strategy state.

## Installation

Use **gold_x9_FIXED.mq4** in `MQL4/Experts` and compile in a current MetaEditor. Only the standard MT4 `Canvas/Canvas.mqh` library is required. **GX9 BMP resources are no longer required.** `GOOOOLD X9 SETINGS.txt` is an identical source copy for compatibility.

Compile and test on a demo account first. This environment cannot run MetaEditor or a broker-connected MT4 terminal.

## Validation

`python -m unittest discover -s tests -v` requires Python and g++.

The 12 tests exercise extracted MQL-compatible code against C++ terminal/canvas stubs, including:

- All four palettes across 800/900/1024/1280/1366/1920 widths and 560/600/720/800/1080 heights.
- Object bounds, chart/trade/equity/tracker separation, text clipping, row capacities and small-window fallback.
- Four theme changes returning to the original palette without resetting sample trading/view state.
- Order table sequence, pending exclusion from open counts, carryovers, TP/SL/TRAIL values and native-object restoration.
- Closed-only history sampling, EMA/DD arithmetic, connected curve rendering and cleanup.

The entry, sizing, pending-expiry, open-position management, strategy-tick and drawdown functions were compared with the prior version and are unchanged. This test suite is **not** a substitute for native MQL compilation or on-terminal visual checks.

### Demo acceptance checklist

1. Compile with no missing image-resource errors.
2. Cycle GRAPHITE → LIGHT → MIDNIGHT → EMERALD → GRAPHITE; verify readable labels and order colors in each.
3. Resize the chart, including a compact 800×560 client area and a smaller fallback window; restore it.
4. Check all actual open and pending tickets, lot sizes and P/L against the Trade tab; page the table.
5. Verify TRADE TRACKER remains visible and the equity dock stays beside—not over—the table.
6. Verify no trade, stop, target, DD halt, trailing confirmation or chart navigation resets when switching themes.
