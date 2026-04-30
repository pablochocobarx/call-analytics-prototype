# Call Analytics Dashboard — Status Report
_Last updated: 2026-04-29_

---

## What Was Built

### Files
| File | Purpose |
|---|---|
| `prototype_full.py` | Approved stakeholder mockup — mock data, persona switcher |
| `live_app.py` | Production app — all 3 personas, wired to live MongoDB |
| `_queries.py` | All MongoDB aggregation functions (cached, TTL 5 min) |
| `_pricing.py` | Project → client / AM / QL rate lookup from `projects.json` |
| `requirements.txt` | `streamlit`, `pandas`, `altair`, `pymongo[srv]`, `dnspython` |

### GitHub
Repo: `https://github.com/pablochocobarx/call-analytics-prototype`  
Branch: `main` — Streamlit Cloud auto-deploys on push.

---

## 3 Personas — What Each Gets

### 🤖 Anunay (Bot Team)
- Full funnel KPIs: Connect % / Interact % / Complete % / Qualify %
- Horizontal funnel bar chart (lead-level counts)
- Per-bot breakdown table with Stack, Channel, Owner, Bot Status, all funnel rates
- Talk time: Avg + distribution buckets (0-10s, 10-20s, 20-30s, 30-40s, 40s+)
- Drill-down: pick any bot → daily trend line chart (Connect / Interact / Complete / Qualify %)
- Filters: Client, Bot Owner, Stack, Channel, Subtype, Bot Status, Date range

### 💼 Jitesh (Marketing)
- Revenue / Cost / Profit / SQL-QL%
- Lead status row: Qualified / IQL / DQL / Followup / Customer FU
- Avg dials to reach each stage, split by Inbound vs Outbound (grouped bar)
- Talk time distribution
- Per-bot table: Qualified, IQL, DQL, SQL, SQL/QL%, Revenue, Cost, Profit, Avg Talk
- Filters: Client, AM, Stack, Channel, Date range

### 👑 Harsha & Darshan (Founders)
- Active bots / Revenue / Profit / Total Qualified
- Per bot-owner rollup: # bots, active, qualified, revenue, cost, profit
- Top 5 / Bottom 5 by Qualify% (global + per owner)
- Bot health table: Inbound and Outbound with health zones
- Filters: Client, Bot Owner, Stack, Date range

---

## Data Sources & How Each Metric Is Computed

### Funnel (lead-level deduplicated)
All funnel numbers are **unique lead counts**, not call counts.  
The aggregation does `$group by {agent_identifier, lead_id}` first, then re-aggregates per agent.

| Metric | Logic |
|---|---|
| Dialled | count distinct `lead_id` per agent in `call_log` |
| Connected | distinct leads where any call has `status == "ended"` |
| Interacted | distinct leads where any call has `status == "ended"` AND `call_duration >= 30` |
| Completed | distinct leads where any call has `report.call_status == "call_completed_normally"` |
| Qualified | distinct leads where `report_detailed.lead_status == "Qualified"` |
| IQL | `report_detailed.lead_status == "Intent Qualified"` |
| DQL | `report_detailed.lead_status == "Disqualified"` |
| Followup | `report_detailed.lead_status == "Follow up"` |
| CFU | `report_detailed.lead_status == "Customer Follow up"` |
| SQL | leads where `campaign_lead.sql == True`, matched on `lead_id` |

### Cost
`SUM(call_log.call_cost)` per agent — real telephony cost from DB.

### Revenue
`Qualified count × qualified_lead_rate` from `projects.json`.  
**Caveat:** `projects.json` has 3 pricing models: `ql`, `site_visit`, `budget`.  
Currently using `qualified_lead_rate` for all — **budget model clients are undervalued** (their revenue is contract-based, not per-QL). See missing items below.

### Channel (Inbound / Outbound)
Derived from `campaign.type`, joined via `campaign.ai_agent → ai_agents._id`.  
If an agent isn't linked to any campaign → shows "—".

### Bot Stack (LGS / LQS)
Derived from `ai_agents.template`:
- `qualifying_agent` → LQS
- `blank_agent` → LGS
- `null` → "—"

This is a **proxy**, not a proper field. See eng requirements.

### Bot Owner
`ai_agents.owner` — only **13 out of ~213 agents** have this populated.  
Most show "—". Needs backfill.

### Client & AM
Fuzzy substring match: `agent_identifier` (e.g. `assetz_zen_outbound`) against `projects.json` top-level keys.  
Works for known clients. Unknown agents → "Unknown" / "—".

### Talk Time
`AVG(call_log.call_duration)` per agent for the selected period.  
Median = same as Avg right now (MongoDB doesn't have a native median aggregation without `$percentile` which requires Atlas).

### Daily Trend (Drill-down)
Same lead-dedup logic but grouped by `$dateToString(created_at)` per agent.  
Live query per bot — fires on drill-down selection.

### Talk Buckets
`$bucket` aggregation on `call_duration` with boundaries `[0, 10, 20, 30, 40]`.  
Fires against full filtered call_log.

---

## What Is Currently Showing "—" (Missing From DB)

| Field | Where Shown | Root Cause |
|---|---|---|
| **Bot Subtype** | Anunay per-bot table, filters | No `subtype` field on `ai_agents` |
| **Bot Revisions** | Founders per-owner table | No revisions counter anywhere in DB |
| **Bot Requests** | Founders per-owner table | No requests/tickets counter in DB |
| **Bot Owner** | All 3 views | `ai_agents.owner` sparse — 13/213 populated |
| **Median Talk** | Anunay + Jitesh | Same as Avg — no median aggregation |
| **Channel** (some bots) | Per-bot table | Some agents not linked to any campaign |

---

## What Engineering Needs to Add

### Priority 1 — Backfills (no schema change, just data)

#### `ai_agents.owner`
- ~200 agents have no owner (only 13/221 populated)
- Backfill with bot owner's email (same format: `rahul.soren@revspot.ai`)
- Dashboard filters and founder rollup depend on this entirely
- **Who fills it:** Bot team / ops leads

---

### Priority 2 — New Fields on `ai_agents` (Bot Team Backfill)

All three fields below show "—" in the dashboard. No inference attempted — wrong data is worse than no data. Dashboard will auto-populate once fields are backfilled.

#### `ai_agents.stack` (enum: `"LQS"` | `"LGS"`)
- Not in DB. Template field (`qualifying_agent` / `blank_agent`) is NOT a reliable proxy — most LQS bots are built on `blank_agent`.
- **Who knows:** Bot team. They know which bots qualify leads (LQS) vs generate/reach leads (LGS).
- **Task:** Add field + backfill all 144 active agents. Bot owners tag their own bots.

#### `ai_agents.subtype` (enum: `"Standard"` | `"Bully"` | `"Proto"` | `"BPCL"` | `"Site Visit"` | `"Reactivation"`)
- Completely absent from DB.
- **Who knows:** Bot team. Definition is clear internally — Bully, Standard, Proto etc. are distinct bot behaviors.
- **Task:** Add field + backfill all 144 active agents.

#### `ai_agents.project_name` (string, normalized)
- Exists on some agents inconsistently.
- Needs to match keys in `projects.json` exactly (e.g. `"Assetz Zen & Sato"`).
- Used for reliable client/AM/revenue lookups instead of fuzzy string matching.

#### `ai_agents.project_name` (string, normalized)
Exists on some agents as a field but not consistently.  
Needs to match the keys in `projects.json` exactly (e.g. `"Assetz Zen & Sato"`).  
Used for reliable client/AM/revenue lookups instead of fuzzy matching.

---

### Priority 3 — Counters (new fields or separate collection)

#### Bot Revisions Counter
Track how many times a bot's prompt/config has been changed.  
Options:
- Add `ai_agents.revision_count: int` — increment on every bot edit
- Or add a `bot_revisions` collection with `{agent_id, revised_at, revised_by}`

#### Bot Requests Counter
Track inbound requests (feature asks, fixes) per bot.  
Options:
- Add `ai_agents.open_requests: int`
- Or a `bot_requests` collection with `{agent_id, requested_at, status}`

---

### Priority 4 — Revenue Model Fix

Currently: `Revenue = Qualified × ql_rate` for all clients.  
Actual pricing models:
- **`ql`** → `Qualified × qualified_lead_rate` ✅ correct
- **`site_visit`** → `Qualified × qualified_lead_rate` ✅ correct (site visit = qualified here)
- **`budget`** → Fixed contract amount, not per-QL. Revenue tracking needs contract value + actual delivered count.

For budget clients (Bhavisha, Lanco, Orchids, Sattva, etc.) the revenue shown is **wrong**.  
Fix options:
- Add `contract_value` to `projects.json` for budget clients
- Or track invoiced amount separately

---

### Priority 5 — Performance (nice to have now, required at scale)

The main aggregation runs a 2-stage `$group` on `call_log` (15M+ docs).  
With a 30-day date filter this is manageable (~500K–1M docs scanned).  
For "All time" it will be slow.

**Recommended indexes on `call_log`:**
```
{ created_at: 1 }
{ agent_identifier: 1, created_at: 1 }
{ lead_id: 1 }
```
If these don't exist, ask the DB admin to add them. Without them, every "All time" query does a full collection scan.

**SQL count query** — `load_sql_counts()` fetches all `campaign_lead.sql == True` doc IDs in 10K batches then passes them as `$in` to `call_log`. If SQL lead count grows past ~100K, this will be slow. Better fix: add `agent_identifier` directly to `campaign_lead` so we can aggregate without the join.

---

## Summary Table

| Area | Status |
|---|---|
| Live DB connection | ✅ Connected, 5-min TTL cache |
| Funnel metrics (Dialled→Qualified) | ✅ Live, lead-deduplicated |
| Lead status (IQL/DQL/Followup/CFU) | ✅ Live |
| SQL counts | ✅ Live (via campaign_lead.sql join) |
| Cost | ✅ Live (call_log.call_cost) |
| Revenue | ⚠️ Live but wrong for budget-model clients |
| Channel (Inbound/Outbound) | ⚠️ Live but ~some agents unlinked |
| Bot Stack | ⚠️ Proxied from template, not real field |
| Bot Owner | ⚠️ 13/213 populated — needs backfill |
| Bot Subtype | ❌ Not in DB |
| Revisions / Requests | ❌ Not in DB |
| Median talk time | ❌ Same as Avg — needs Atlas $percentile |
| Client / AM mapping | ⚠️ Fuzzy match — works, can mismatch unknown agents |
| Daily trend drill-down | ✅ Live |
| Talk time buckets | ✅ Live |
| 3-persona UI | ✅ Complete |
| Date filter | ✅ Working |
| All sidebar filters | ⚠️ Stack/Subtype/Owner filters work but sparse data |
