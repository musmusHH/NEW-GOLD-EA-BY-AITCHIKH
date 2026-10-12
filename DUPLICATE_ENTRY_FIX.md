# Duplicate-entry fix — "two trades at the same price with the same SL"

Applies to: the independent MT4 fractal rebuild (`gold_x9_mt4_rebuild_v1.122.mq4` → **`gold_x9_mt4_rebuild_v1.123.mq4`**)

---

## 1. What was actually happening

Reported symptom: *sometimes two trades open on the same side (both BUY or both SELL) at the
same price with the same stop loss.*

Three separate holes in v1.122 produced that. They compound, which is why it looked random.

**Cause 1 — the duplicate check was a half-tick only, and only in MULTI mode**

```mq4
// v1.122
bool RebuildHasEntryPrice(double entry)
  {
   double tolerance=RebuildTickSize()*0.5+1e-9;   // <-- 0.005 on a 2-digit gold feed
   ...
  }

// ...and it was only consulted here:
if(RebuildMultiMode() && RebuildHasEntryPrice(entry))return;
```

Two fractal highs 5 points apart (e.g. 4000.00 and 4000.05) produced two pending orders at
4000.30 and 4000.35. Both passed the check, both triggered, and each got an SL at
`StopLossPoints` distance — i.e. **same price to the naked eye, same stop loss**.

**Cause 2 — single-level modes never compared prices at all**

```mq4
// v1.122
if(!RebuildMultiMode() && HasPendingType(type))return;   // "is there already a BUYSTOP?"
```

That only asks whether a pending order of the same *type* exists. Nothing compared the price,
and the check never looked at **open positions**. So: BUYSTOP at 4000.30 fills → becomes OP_BUY →
the guard above is now `false` (no BUYSTOP exists any more) → the EA arms a fresh BUYSTOP at the
**same fractal level, same price, same SL** → triggers again. Classic double entry.

**Cause 3 — order-pool refresh races**

When a scan walks every fractal (`RebuildScanMultipleLevels`), several `OrderSend` calls happen in
one pass. If the terminal's trade pool has not refreshed the just-sent order yet, the next send in
the same pass cannot see it and duplicates it. v1.122 had no in-memory fallback.

---

## 2. What v1.123 changes

The rule is now: **a new entry may not be placed within `MinEntryDistancePoints` of any owned
live order of the same side — pending order or open position.**

| # | Change | Where |
|---|--------|-------|
| 1 | New input `MinEntryDistancePoints` (default **300** broker points; `0` = block exact duplicates only) | inputs block |
| 2 | New input `DeleteDuplicatePending` (default **true**) — cancels same-side *pending* levels that duplicate an older live order | inputs block |
| 3 | `RebuildLevelInUse()` — side-aware level lock over pendings **and** market positions | replaces `RebuildHasEntryPrice()` |
| 4 | Scan-pass memory (`g_scanBuyLevels/g_scanSellLevels`) — a level sent in this pass blocks a second send even if the order pool lags | `RebuildScanLevelTaken/Add/Reset` |
| 5 | The lock is applied in **all four** management modes, including the single-level ones | `PlacePending()` |
| 6 | The lock is re-checked before the error-147 (expiry-denied) fallback send | `PlacePending()` |
| 7 | The multi-level scan only marks the bar as used when an order was **really sent** (v1.122 marked it even for refused levels, losing the bar) | `RebuildScanMultipleLevels()` |
| 8 | The scan re-runs when a fill/expiry/OCO delete changes the pending or position count, instead of waiting for the next bar | `RebuildScanMultipleLevels()` |
| 9 | `RebuildDeleteDuplicatePendings()` — one-pass cleanup of pre-existing duplicates, run every tick | new function, called from `RebuildTick()` |
| 10 | Status/tooltip now report the lock (`LEVEL ALREADY USED`, `Min level gap N pts`) | `UpdateStatus()` |

### Safety rules baked into the cleanup (#9)

* **Only pending orders are ever deleted.** Open positions are never touched.
* **Same side only.** A buy and a sell at the same price are separate trades, not duplicates.
* **The oldest order (lowest ticket) always survives**, so the cleanup is idempotent — it cannot
  cascade into deleting a whole ladder.
* **Same-side only + oldest-wins** means a legitimate multi-level ladder (levels ≥ the gap apart)
  is untouched.

---

## 3. Choosing `MinEntryDistancePoints`

It is in **broker points**, not pips.

| Feed | 1 point | 100 | 300 (default) | 500 |
|------|---------|-----|---------------|-----|
| XAUUSD, 2 digits | 0.01 USD | 1.00 USD | 3.00 USD | 5.00 USD |
| XAUUSD, 3 digits | 0.001 USD | 0.10 USD | 0.30 USD | 0.50 USD |
| EURUSD, 5 digits | 0.00001 | 10 pips | 30 pips | 50 pips |

Guidance:

* **Gold / XAUUSD (2 digits):** keep 300. With the default `EntryBufferPoints=30` (0.30 USD) and
  `StopLossPoints=5000` (50 USD), 300 points = 3 USD separates genuine levels while still filling.
* Set it **smaller** if levels feel too slow to appear (`100` = 1 USD on gold).
* Set it to `0` only if you want the old tolerance (exact duplicates only) — that re-opens the bug
  for near-identical fractals.
* Do not set it larger than roughly one third of `StopLossPoints * point`, or the ladder will
  starve.

---

## 4. How to confirm the fix is live

1. Compile and attach. The journal prints on `OnInit`:
   `Gold X9 Rebuild Raised v1.123 | MULTI POINTS | XAUUSD | duplicate-entry lock 300 pts | duplicate pending cleanup ON`
2. The `PENDING ORDERS` metric tooltip (hover) shows `| MIN LEVEL GAP 300 pts`.
3. When a level is refused because it is already held, the header status shows `LEVEL ALREADY USED`
   instead of `TRADING ACTIVE`.
4. When pre-existing duplicates are cancelled you get a journal line:
   `Rebuild duplicate level cancelled #… at 4000.30 - same-side order already holds that price (min gap 300 pts).`
5. Trade list check: no two owned BUY entries (or two owned SELL entries) should ever sit within
   `MinEntryDistancePoints` of one another again.

Positions that were **already** duplicated before this update are left alone (the EA never closes a
position on its own) — close or let them run as you prefer; the pending-order cleanup prevents new
ones from being added on top.

---

## 5. Manual patch (if you keep editing your own v1.122 file)

Add near the entry inputs:

```mq4
input int  MinEntryDistancePoints=300;     // min gap between same-side owned entries (broker pts; 0 = exact duplicates only)
input bool DeleteDuplicatePending=true;    // cancel same-side pending levels duplicating an older live order
```

Replace `RebuildHasEntryPrice()` with the block marked
`//--- v1.123 duplicate-entry lock ...` in `gold_x9_mt4_rebuild_v1.123.mq4`
(`RebuildBuySideType`, `RebuildMinEntryDistance`, `RebuildLevelInUse`, `RebuildScanLevelsReset`,
`RebuildScanLevelTaken`, `RebuildScanLevelAdd`, `RebuildDeleteDuplicatePendings`), then:

* `void PlacePending(...)` → `bool PlacePending(...)`, and replace the old dedupe line with
  `if(RebuildLevelInUse(buySide,entry) || RebuildScanLevelTaken(buySide,entry)){g_rebuildStatus="LEVEL ALREADY USED";return false;}`
  placed **after** `entry=RebuildPrice(entry,buySide);`; add `RebuildScanLevelAdd(buySide,entry);`
  after a successful send.
* In `RebuildScanMultipleLevels()`: reset the scan memory at the top, only set
  `g_lastBarTime` when an order was really placed, and reset the memory again at the end.
* Call `RebuildDeleteDuplicatePendings();` in `RebuildTick()` next to the OCO cleanup.

Everything else (HUD, broker-data chart panel, percentage manager M1–M4, equity curve) is
byte-for-byte the v1.122 behaviour.

---

## 6. Known inherited item (not touched by this fix)

While auditing the entry path I noticed a gap that already exists in v1.122: several HUD fields are
**written but never created**, so `HudSetText()` silently skips them (`HudFind()` returns `-1`).

* Working labels: the six metric-ribbon cells (`top_eq`, `top_balance`, `acc_W3`, `top_dd`,
  `top_pos`, `top_pending`), `brand`, `symbol`, `market_info`, `top_status`, and all `trk_*`
  tracker cells.
* Never created, therefore blank: the ACCOUNT rows (`acc_V0..acc_V4`, `acc_W0..W2`, `acc_tV`,
  `acc_nV`, `acc_dV`, `acc_bar`), the STRATEGY MATRIX (`str_cV`, `str_infoV0..9`), the LIVE strip
  (`liv_V0..V5`), the equity dock (`eq_n`, `eq_V0..V3`), and `top_net`, `top_spread`, `top_next`,
  `top_status_bg`.

No layout was invented here on purpose — the approved HUD geometry is untouched. Everything the fix
needs (the header status line and the pending/position tooltips) does work, because `top_status`,
`top_pending` and `top_pos` are created. Say the word if you want those remaining panels wired up
with labels placed inside the existing header/ribbon geometry.
