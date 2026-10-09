# X9 Full Focus — design 4 / v6.750

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

## Chart navigation — v6.740

The symbol/timeframe and all ten chart controls are in the upper header, not over the candle plot. At widths of 1180 pixels or more, they share the first header row and free 32 pixels for candles. Narrower supported windows use a second header row without reducing the previous candle-plot height.

| Control | Action |
| --- | --- |
| **MOVE** | Toggle drag mode, then hold the left mouse button inside the candle area and drag horizontally or vertically. Click MOVE again to disable dragging. |
| **CENTER** | Put the newest candle in the loaded view at the horizontal midpoint, with its close centered vertically. Keeps the current history offset and price span. |
| **+ / −** | Expand/compress candle spacing by showing fewer/more bars. |
| **Y+ / Y−** | Expand/compress candles vertically without changing the number of bars. |
| **< / >** | Browse older/newer history. |
| **LIVE** | Return to latest bars, first trade page, default horizontal placement and automatic price scaling. |
| **BARS / ALL** | Toggle candle-only/all-order-level automatic price fitting; clears manual vertical scaling. |

`chartRightSpacePct` defaults to **20%**, clamped to 8–45%. It reserves blank space between the latest candles and the right price scale in the default view. Dragging keeps a minimum right gutter; offscreen candles are clipped rather than drawn across the price scale or trade dock. Nearby axis text is suppressed around the current-price badge to avoid overlapping price labels.

Manual vertical placement remains stable across quote updates until LIVE or BARS/ALL resets it. MOVE temporarily disables native mouse scrolling; disabling MOVE or removing/falling back from the panel restores the saved setting. All navigation is display-only: it never moves real orders, SL or TP.

## Screen sizes

The layout uses actual chart-client dimensions, not the full desktop resolution. It supports **800×400 and larger** chart areas. The trade dock limits its row count to leave at least 100 pixels of candle plot at normal heights, or 60 pixels in short-window mode. Four rows are requested by default; small windows may display fewer, and `chartTradeRows` can request more. Pagination always keeps additional trades accessible.

At less than 800×400, the EA shows a resize notice and falls back to the native chart rather than drawing an overlapping fixed-size dashboard. Trading logic continues unchanged. Long values are shortened only for display; hover shows full text. Minimize/restore and theme changes rebuild visual resources, not strategy state.

## Tester / Terminal resize and result-box removal — v6.740

The old 560-pixel minimum caused the native chart to replace Full Focus when opening the Tester or Terminal. For chart heights of **400–559 pixels**, Full Focus now uses shorter summary cards and an 80-pixel TRADE TRACKER with one row (OPEN LIVE when positions exist, otherwise the most recent closed day). The trade table reduces its row count and remains pageable. Larger heights automatically restore the full tracker. The equity curve is drawn only when its dock has enough room.

The minimum supported chart-client area is now **800×400**; making the Terminal/Tester so large that less remains still requires resizing it. This is the chart area, excluding MT4 toolbars and the Terminal/Tester.

**All EA result boxes are removed**, both native BUY/SELL profit/points cards and custom-chart result badges. Their rendering code, polling and visual inputs have been deleted. Initialization/removal cleans up the EA's old `GX9T_` objects regardless of previous keep-on-exit settings. Unrelated manual objects are not deleted. Reporting identity inputs, trade history, closed-equity sampling and live trade values remain unchanged.

After compiling, reattach the EA (or restart a visual test) to trigger cleanup. Test opening/closing and resizing both the Terminal and Tester, including a 1366×440 chart-client area.

## Installation

Use **gold_x9_FIXED.mq4** in `MQL4/Experts` and compile in a current MetaEditor. Only the standard MT4 `Canvas/Canvas.mqh` library is required. **GX9 BMP resources are no longer required.** `GOOOOLD X9 SETINGS.txt` is an identical source copy for compatibility.

Compile and test on a demo account first. This environment cannot run MetaEditor or a broker-connected MT4 terminal.

## Validation

`python -m unittest discover -s tests -v` requires Python and g++.

The 12 tests exercise extracted MQL-compatible code against C++ terminal/canvas stubs, including:

- Right candle space, header control bounds, centering, horizontal/vertical dragging, vertical zoom bounds, clipping, LIVE reset and native mouse-setting restoration.
- All four palettes across 800/900/1024/1280/1366/1920 widths and 400/440/500/559/560/600/720/800/1080 heights.
- Object bounds, chart/trade/equity/tracker separation, text clipping, row capacities and small-window fallback.
- Four theme changes returning to the original palette without resetting sample trading/view state.
- Order table sequence, pending exclusion from open counts, carryovers, TP/SL/TRAIL values and native-object restoration.
- Closed-only history sampling, EMA/DD arithmetic, connected curve rendering and cleanup.

The entry, sizing, pending-expiry, open-position management, strategy-tick and drawdown functions were compared with the prior version and are unchanged. This test suite is **not** a substitute for native MQL compilation or on-terminal visual checks.

### Demo acceptance checklist

1. Compile with no missing image-resource errors.
2. Cycle GRAPHITE → LIGHT → MIDNIGHT → EMERALD → GRAPHITE; verify readable labels and order colors in each.
3. Resize the chart, including a compact 800×400 client area and a smaller fallback window; restore it.
4. Check all actual open and pending tickets, lot sizes and P/L against the Trade tab; page the table.
5. Verify TRADE TRACKER remains visible and the equity dock stays beside—not over—the table.
6. Verify no trade, stop, target, DD halt, trailing confirmation or chart navigation resets when switching themes.

7. Enable MOVE, drag in all directions, try CENTER and both zoom axes. Verify the quote updates without resetting manual placement; LIVE restores auto scaling. Check the toolbar at wide and compact sizes and verify mouse scrolling is restored when MOVE/panel is disabled.

## Small price-level labels — v6.740

The right side of the candle plot now shows borderless, small type labels, before the price axis: BUY (green), SELL (red), PENDING BUY (amber), PENDING SELL (purple), TP (blue), SL (orange). Entry lines use type colors rather than floating-profit colors; live P/L colors in the trade table are unchanged. Light theme uses darker accents.

Labels use non-overlapping 16-pixel rows. Nearby same-type levels are grouped with an `xN` count; no diagonal connectors are drawn. Actual order lines remain at exact prices. Only in-range levels are labeled. If the available rows fill, `+N levels` explicitly indicates additional levels; the panel tooltip and trade table retain order details. Labels are not profit-result boxes and do not change orders or stops.

Regression checks cover coincident labels, six distinct colors, grouping, overflow, offscreen exclusion, bounds and row separation. Native MetaEditor compilation and visual demo testing remain required.

### v6.740 cleanup

Removed the diagonal label-to-price connectors that became visually tangled around clustered levels. Non-overlapping colored text, grouped counts, overflow indicators and exact horizontal price lines are unchanged.

## Raised solid panels — v6.750

All native HUD rectangles (header, summary cards, tracker and row bands) now use BORDER_RAISED, STYLE_SOLID and opaque fills. The candle panel, trade table and closed-equity dock receive two-pixel light/shadow bevels on their opaque canvas backgrounds. Colors follow the four themes, including a light-theme bevel. Geometry, price-level labels and horizontal order lines are unchanged; no diagonal label connectors or result boxes are restored.

Regression coverage checks raised/solid/filled HUD rectangles across all themes and supported sizes; the bounded canvas tests exercise the new section borders during resizing. Native MT4 compilation and visual demo validation are still required.
