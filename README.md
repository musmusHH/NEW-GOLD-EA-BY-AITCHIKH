# NEW GOLD EA BY AITCHIKH — X9 Full Focus

Current source: **[gold_x9_FIXED.mq4](gold_x9_FIXED.mq4)** — v6.720.

Selected layout: **design 4 / Graphite Full Focus**, with a full-width real-price chart, open-first trade table, closed-result EMA/DD curve and independent TRADE TRACKER.

**Four themes:** Graphite, Light, Midnight and Emerald. Use the **THEME** button in the header to switch immediately, or choose the initial `hudTheme` in Inputs.

**Chart controls:** MOVE enables drag-to-pan; CENTER centers the newest visible candle; + / − change horizontal zoom; Y+ / Y− expand/compress the vertical price scale; LIVE restores live history and automatic scaling. Symbol and controls now sit in the upper header, with 20% right-hand candle space by default.

**v6.720:** Removed all EA result boxes and their drawing code. Opening Tester/Terminal now uses a compact Full Focus layout at chart heights of 400–559 pixels; minimum supported client area is 800×400. Legacy EA result boxes are cleaned up on attachment.

The new interface is drawn at runtime: no external GX9 bitmap images are required. A current MT4 standard `Canvas/Canvas.mqh` library is required.

See **[FOCUS_DESIGN.md](FOCUS_DESIGN.md)** for installation, resizing behavior and demo-account checks. Earlier feature notes are retained in `LIVE_CHART_PANEL.md` and `PERFORMANCE_FIX.md`.

Run regression tests with:

```sh
python -m unittest discover -s tests -v
```

Python and g++ are required for the test stubs. Native MetaEditor compilation and MT4 demo validation are still required; the tests do not execute the EA against a live terminal. Test on demo before live use.
