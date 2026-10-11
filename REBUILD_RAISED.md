# Independent MT4 Fractals rebuild + Raised Solid / v1.122

**File: [gold_x9_Rebuild_Raised.mq4](gold_x9_Rebuild_Raised.mq4)**

This is an independent reconstruction using the user's supplied Fractals/pending entry approach. It is **not the original video's source code**. The existing MT4 v6.750 interface and percentage manager are reused, but the old X9 entry strategy is not active or included as an alternate entry engine. The existing `gold_x9_FIXED.mq4`, TXT copy and MT5 port remain unchanged.

## اختيار طريقة الإدارة

من **Inputs → ManagementMode** اختر:

| الخيار | الإعدادات المستخدمة |
|---|---|
| `MANAGEMENT_POINTS` | الهدف والستوب والتعادل والتريلينغ بالنقاط، كما في الكود المرسل. |
| `MANAGEMENT_PERCENT` | دخول فردي وإدارة بالنسب من نسخة MT4 السابقة. |
| `MANAGEMENT_MULTI_POINTS` — الافتراضي الجديد | أوامر متعددة عند مستويات Fractals مختلفة، وإدارة بالنقاط. |
| `MANAGEMENT_MULTI_PERCENT` | أوامر متعددة عند مستويات Fractals مختلفة، وإدارة بالنسب. |

**قاعدة الدخول في الخيارات الأربعة:** Fractals + `EntryBufferPoints` وأوامر BUY STOP / SELL STOP وفلتر السبريد. الخياران الفرديان يحتفظان بأمر معلّق واحد لكل اتجاه. الخياران MULTI يفحصان مستويات مختلفة حتى الحد المحدد، ويسمحان بالاتجاهين معًا دون OCO. لا يتم استخدام دخول النسخة السابقة أو فلاتر ساعاتها/إيقافها على أساس DD.

- `MaxMarketPositions`: الحد الذي يمنع إنشاء أوامر جديدة عندما يصل عدد الصفقات المفتوحة إليه.
- `MaxPendingOrders`: الحد الإجمالي للأوامر المعلقة التابعة لهذا الرمز والـMagic، وليس حدًا لكل اتجاه.
- `UseBreakEven` و`UseTrailingStop`: يعملان في الخيارين.
- `FixedLots` أو `UseRiskPercent` مع `RiskPercent`: نفس طريقة تحديد الحجم في الخيارين؛ حساب المخاطرة يستعمل المسافة الفعلية إلى SL بعد تقريب السعر.
- عند تغيير الإدارة من Inputs، **تُدار الصفقات المفتوحة التابعة للإكسبرت بالطريقة الجديدة**. لا تُعاد كتابة مستويات SL/TP الأولية تلقائيًا للأوامر المعلقة القديمة. يُفضّل التبديل دون صفقات/أوامر مفتوحة على حساب تجريبي.

## Interface and tracking

- Full Focus **Raised Solid**, four themes: Graphite / Light / Midnight / Emerald.
- Broker-data candles with MOVE, CENTER, +/−, Y+/Y−, history navigation, LIVE and BARS/ALL.
- Open-position count **current / MaxMarketPositions** and pending count **current / MaxPendingOrders**.
- Open-first, pageable table: ticket, type, lots, live P/L, estimated TP, SL and successfully confirmed trailing-stop amount.
- Small colored level labels with grouping/collision avoidance, no diagonal label leaders and no closed-result boxes.
- Separate TRADE TRACKER, live row, recent closed days, statistics and closed-result EMA/DD curve.
- The active mode and engine state appear in the top status area (hover for the complete text).
- Compact layout for chart-client areas down to **800×400**. Below that the existing resize fallback remains.
- `ShowStatusComment=false` by default so native chart text does not overlap the dashboard. Set true only if the extra text is wanted.
- Reporting defaults to **strict magic** (`MATCH_MAGIC_ONLY`) so dashboard counts match the strategy's owned-trade limits. Broader reporting filters do not grant permission to manage unrelated trades.

## Mode settings

### POINTS / MULTI POINTS

Defaults match the supplied code:

- `StopLossPoints=5000`, `TakeProfitPoints=10000`.
- BE: trigger `4000`, lock `200` points.
- Trailing: start `1200`, distance `800`, step `200` points.
- Management on every tick, even while spread prevents new entries.

Points are broker points, not pips. For example, 5000 points is a price distance of 5.000 on a 0.001-point symbol, but 50.00 on a 0.01-point symbol. Check the actual symbol specifications.

### PERCENT / MULTI PERCENT

- Initial SL distance = pending entry price × `stopLossPct / 100` (default 2%).
- Initial TP distance = pending entry price × `takeProfitPct / 100` (default 0.7%).
- BE trigger 0.1%, lock 0.025% of the open price.
- Trail trigger 0.2%, base distance 0.2%, max trailing range 1% favorable movement, as in the previous manager.
- Two-stage trailing is on by default: 0.30% below the 0.35% midpoint, 0.15% above it. Trailing distance uses the current exit quote.
- Salvage trigger 1%, salvage target offset 0.15%; set `salvageTriggerPct=0` to disable that trigger.
- Aged-loss handling defaults on: age 4 hours, minimum adverse move 0.05%. **It can alter TP and close a losing position** after the conditions are met. Disable `enableAgedLossCut` if not wanted.
- Optional half-volume partial pay defaults off (`enablePartialPay=false`).
- `exitTimeFrame=PERIOD_M1` determines the management interval. It does not change the Fractals entry timeframe, which remains the attached chart period.
- POINTS-only inputs are ignored in this mode, and vice versa. Pending expiry and per-side quotas now apply in all modes; see v1.120 below.

## Deliberate corrections to the supplied reconstruction

1. **Single-level modes only: OCO cleanup no longer recreates the opposite pending order later in the same tick.** It checks all owned market directions. With both BUY and SELL positions open, both pending entry directions are blocked while OCO is enabled. Opposite STOP/LIMIT orders are cleaned up, not manual/unrelated magic orders.
2. Pending/open limits and per-type duplicates are rechecked immediately before **each** send. With `MaxPendingOrders=1`, a buy created earlier in the tick consumes the slot and prevents an additional sell.
3. Entries require valid quotes/history and both Fractals. Missing history does not consume the current bar's evaluation.
4. Initial and managed prices respect the symbol tick size. Too-small SL/TP distances are rejected rather than silently widened. Stop/freeze distances and no-loosening checks protect management; broker errors are logged.
5. Volume rounding follows the broker step (including 0.001). Risk sizing uses the actual normalized entry-to-SL distance and tick-size price increment. If the risk-based lot is below broker minimum, the order is **skipped**, rather than raising the risk to meet minimum volume. Fixed-lot sizing retains minimum/maximum clamping.
6. Margin is checked before sending. A trailing amount is recorded only after successful `OrderModify` in either mode.
7. Percentage management keeps the prior manager with shared BE/trailing switches, configured slippage, broker volume precision and a stop-no-loosening safeguard after broker-distance adjustments.

**Limits are local EA checks, not broker-side reservations.** Existing pending orders can fill concurrently and push open positions above `MaxMarketPositions`; lowering a limit does not close existing trades or cancel all pending orders. In the SINGLE modes, optional OCO is client-side, requires a running terminal/ticks, and cannot guarantee atomic cancellation before another fill. Do not run multiple EAs managing the same symbol/magic.

`OneEntryPerBar` means **one entry evaluation per bar**, as in the supplied code; that evaluation may submit both a buy and a sell when allowed. In SINGLE modes only, at most one owned pending order of each STOP type is created. MULTI modes can submit several distinct levels per evaluation, always rechecking the combined pending limit and open-position limit before each send.

## Reporting and state caveats

- P/L, TP/SL and trailing money estimates retain the previous dashboard commission convention: estimated 0.07 per 0.01 lot in account currency, plus broker profit/swap. They are not a promise of exact broker realized costs.
- DD is displayed as an account-level metric; old entry-blocking DD/equity/dead-window gates are deliberately disabled to preserve the selected Fractals entry strategy.
- Chart view, successful-trailing evidence, partial-pay keys and DD session baseline are session-local. Restarting/changing inputs resets them; partial-pay behavior must be demo tested across restarts. The legacy partial-pay key uses entry time/price.
- `MagicNumber=630063` and comment prefix `GoldX9_MT4_Rebuild` match the supplied reconstruction, so existing same-symbol/same-magic trades may be managed when attaching this build. The old EA's default magic 123457 is different.
- A non-chart `TradeSymbol` is supported outside the tester, but entry/management still run on chart ticks. Prefer attaching to the traded symbol's chart. In the tester, leave `TradeSymbol` blank or equal to the tested symbol.

## Installation and required demo checks

1. Copy **gold_x9_Rebuild_Raised.mq4** into `MQL4/Experts`.
2. Compile in a current **MetaEditor 4** with standard `Canvas/Canvas.mqh`; no custom includes or images need installation. This file is MT4, not MT5.
3. First use a demo account / visual Strategy Tester, with the broker's gold symbol and intended timeframe.
4. Verify the Journal line: `Gold X9 Rebuild Raised v1.122 | MULTI POINTS` (or the selected mode).
5. Verify all four mode settings against actual entry/SL/TP prices, BE/trailing, and successful TRAIL updates. Test failed modifications and freeze restrictions.
6. Verify max pending=1, max open/pending=0, spread filtering while management continues, OCO with single/mixed directions, and unrelated magic isolation.
7. Test risk lots versus broker specs and below-minimum risk rejection. Test partial-pay/aged-loss only with controlled demo positions.
8. Check all four themes, table paging, Terminal/Tester resize, and that the closed curve changes only with closed results.

**No MetaEditor/MT4 broker terminal is available in this workspace.** Local tests are not native MQL compilation or execution validation. This is not a live-readiness or profitability claim.

## Reproducible build and tests

Editable inputs/engine: `rebuild/RebuildInputs.mqh` and `rebuild/RebuildEngine.mqh`. The generator copies the current MT4 interface, removes the old entry engine and embeds the independent engine into the standalone deliverable.

```sh
python tools/build_rebuild_mt4.py
python tools/build_rebuild_mt4.py --check
python -m unittest discover -s tests -v
```

The suite has 20 tests. New coverage executes the reconstruction engine and the actual reused percentage manager against C++ terminal stubs, tests both price formulas, mode routing, volume/risk sizing, OCO, combined limits, no-repeat-per-bar behavior, spread filtering, failed modification/trailing evidence, partial pay and symbol validation. The existing chart/four-theme geometry tests are also run against the generated rebuild source.

## v1.110 — multiple Fractal levels inside ManagementMode

- Enum values 0/1 retain the prior single-level POINTS/PERCENT behavior; values 2/3 add MULTI POINTS/MULTI PERCENT. New installations default to MULTI POINTS. Older saved presets may still select a single-level mode: explicitly choose the new mode in Inputs.
- MULTI scans bars from newest to oldest (shift 2 through the available lookback), trying upper and lower levels at each shift. This prevents scanning all buy levels before considering any sells; it does not guarantee a 50/50 split. Each level still must be on the valid side of the market, satisfy broker stop/spread/margin constraints, and pass risk sizing. Ten is a cap, not a target or ten orders per direction.
- Every MULTI send checks the normalized entry against all currently open/matching pending orders and market positions for the same symbol and magic. Levels within half a broker tick are duplicates, including repeated Fractals that round to the same tick. Unrelated magic/symbol orders do not block entry. No duplicate-by-type restriction applies in MULTI.
- Duplicate checking uses current broker entry prices, not historical or pre-slippage prices. Closed/deleted levels can be reused on a later evaluation. This is not a permanent ban on trading a price again.
- MULTI always bypasses opposite-side deletion/blocking, even if an old preset has `DeleteOppositePending=true`. That input now applies only to SINGLE modes and defaults to false. Both directions still respect `EnableBuy`/`EnableSell` and broker/account hedging restrictions.
- `OneEntryPerBar=true` limits scans, not order count: one scan can place multiple distinct levels. Live owned pending orders consume `MaxPendingOrders` slots across both directions. Open-position limits are rechecked per send, but existing pending orders can still fill concurrently beyond the open limit; there is no atomic broker-side reservation.
- **RiskPercent is per order, not for the basket.** Ten orders at 1% each may expose roughly 10% initial SL risk before costs/slippage. Reassess sizing on demo before enabling multi-level entry.
- Regression fixtures include ten distinct orders with both directions, normalized-price duplicates, open-position duplicate suppression, single-side levels, legacy OCO=true bypass, per-send caps, and both MULTI management variants. Native MetaEditor compilation and demo testing remain required.

## v1.120 — pending expiration and independent direction quotas

New inputs (apply to all four modes):

| Input | Default | Meaning |
|---|---|---|
| `PendingExpiryMinutes` | 60 | Lifetime measured from order creation, not each scan. 0 disables new native expiry and local age-based expiry. |
| `MaxPendingPerSide` | 5 | Independent cap for pending BUY STOP + BUY LIMIT, and separately SELL STOP + SELL LIMIT. 0 blocks all new pending orders. |

`MaxPendingOrders=10` is still the combined cap. With the default side cap, five sells cannot use the five unused buy slots. A side without a valid Fractal is not filled artificially. A smaller total cap always wins; a larger total cap does not automatically increase the side cap. Both caps are checked before each send, including expiry fallback. Hover the PENDING ORDERS card for BUY/SELL counts, side quota, total limit and expiry setting.

### Expiration behavior

- New orders request broker-side expiration at server time plus the chosen minutes. This can expire even while the EA is offline, subject to the broker's support/rules.
- Only explicit error **147** (expiration denied) triggers one retry without native expiration. Other errors, including ambiguous timeouts, are not retried via this fallback.
- The EA checks its own symbol/magic pending orders on every chart tick, before spread/entry filters. It deletes orders whose age reaches the configured lifetime, including existing GTC orders, or whose native expiry has passed. Failed deletions are logged and retried on later ticks. Market positions and unrelated orders are untouched.
- The local fallback requires a running EA, trading permission and incoming chart ticks. It cannot promise exact-minute expiry offline or when no ticks arrive. The display timer does not submit trade operations.
- A successful local expiration skips new entry creation in that same tick; with `OneEntryPerBar=true` it also consumes the current bar evaluation. Native broker expiration or later scans can still lead to a new order at a still-valid Fractal. Expiration cancels an order; it is **not a permanent ban on that signal/price**.
- On attachment or input change, existing matching orders are checked against the current lifetime. Turning expiry off does not remove broker expiration already embedded in existing orders.

### Existing imbalance

Installing this version does **not** immediately cancel nonexpired orders merely because one side exceeds its new quota. It blocks additional orders on that side; existing orders remain until fill, expiration or manual cancellation. Review existing same-magic orders before attaching. Increasing/decreasing the quotas does not close market positions. These are pending-direction limits, not guarantees of equal open BUY/SELL positions.

Tests now cover single-sided level sets, reserved direction capacity, pending LIMIT orders counting toward a side, native expiration timestamps, 147-only fallback, expiry despite high spread, disabled expiry, failed deletion retries and ownership isolation. Existing tests still verify both management systems and all four UI themes. Native MetaEditor compilation/demo checks are still required.

## v1.121 — expiration conversion warning

Made the final conversion from 64-bit expiration arithmetic to `datetime` explicit, removing the implicit conversion at the reported line. The validated expiry-minute limit, native expiry and local fallback behavior are unchanged. Native MetaEditor warning verification remains required.

## v1.122 — empty trade-table sorting

Guard both ArraySort calls in the trade table with ArraySize > 1. MT4 reports incorrect start position 0 when an empty market or pending list is sorted. Empty and single-item lists require no sorting; multi-item lists retain the previous ordering. Regression tests now reject empty/singleton sorts in the renderer stub and exercise empty, market-only, pending-only and mixed snapshots. This is a display-only correction; entry, trailing, expiry and quotas are unchanged. Native MT4 tester verification is still needed; no performance benchmark is claimed.
