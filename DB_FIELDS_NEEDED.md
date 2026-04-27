# DB Fields Required for V_FULL Dashboard

Two prototype versions exist:
- **V_NOW** (`prototype_now.py`) — uses only fields currently in DB
- **V_FULL** (`prototype_full.py`) — includes everything stakeholders asked for

This doc lists what tech needs to add to reach V_FULL.

---

## 1. New fields on `ai_agents` collection

| Field | Type | Purpose | Stakeholder |
|---|---|---|---|
| `owner` | string (email) | Bot maker / responsible person — KPI tied to bot perf | All |
| `stack` | enum: `LGS` / `LQS` | Lead Gen vs Lead Qualification stack | Anunay |
| `subtype` | enum: `BPCL` / `Bully` / `Proto` / `Standard` / … | Bot type variant | Anunay |
| `channel` | enum: `Inbound` / `Outbound` | Direct field instead of inferring from campaign | Anunay |
| `project` | string | Direct project name (replaces fuzzy match from agent_identifier) | All |

⚠ `owner` exists today but only 13/214 docs populated → **backfill all 214**.

---

## 2. Activate `agent_versions` collection (currently 0 docs)

| Field | Type | Purpose |
|---|---|---|
| `agent_identifier` | string | FK to ai_agents |
| `version` | int | v1, v2, v3, … |
| `created_at` | datetime | when revision created |
| `created_by` | string (email) | who revised |
| `change_summary` | string | what changed (optional) |

Each bot edit / iteration = new doc. Powers Founders' "# revisions per bot" metric.

---

## 3. New collection: `bot_requests`

| Field | Type | Purpose |
|---|---|---|
| `_id` | ObjectId | |
| `requested_by` | string (email) | AM / leadership requesting |
| `requested_for_client` | string | client / project |
| `requested_at` | datetime | |
| `status` | enum: `requested` / `in_dev` / `launched` / `cancelled` | workflow state |
| `assigned_owner` | string (email) | bot maker assigned |
| `linked_agent_identifier` | string \| null | populated when bot is launched |

Powers "# bot requests" metric for Founders. New workflow tracker.

---

## 4. ~~SQL flag~~ ✅ ALREADY EXISTS

Field: `campaign_lead.sql` (boolean, top-level).
Distribution: 3,352 true / 2,452 false / 3.77M null (not evaluated).
Join: `call_log.lead_id → campaign_lead.lead_id`.

⚠ Coverage is sparse (~0.15% of campaign_lead docs evaluated). Backfill / improve CRM sync coverage to make SQL/QL% meaningful at scale.

---

## 5. Move `projects.json` into DB

Create collection: `client_projects`

| Field | Type |
|---|---|
| `client_key` | string (matches `campaign.client`, e.g. `godrej-blr`) |
| `project_name` | string (e.g. `Aveline`) |
| `account_manager_name` | string |
| `account_manager_email` | string |
| `pricing_model` | enum: `ql` / `site_visit` / `budget` |
| `qualified_lead_rate` | number \| null |
| `enriched_lead_rate` | number \| null |
| `raw_lead_rate` | number \| null |
| `lead_commitment` | number \| null |
| `active` | bool |

Today: static file maintained manually. Should be a DB collection so dashboard reads live, AMs can edit via admin UI later.

---

## 6. Optional: clean up `campaign.owner` data quality

- 397 / 1174 (34%) campaigns have `owner = null`
- Typo: `naina@revpsot.ai` should be `naina@revspot.ai`
- Casing dup: `Vikram@revspot.ai` vs `vikram@revspot.ai`

Backfill + normalize for accurate per-owner aggregations.

---

## Tech bandwidth estimate

| Item | Effort | Blocker for |
|---|---|---|
| Backfill `ai_agents.owner` (200 docs) | 1d | All 3 personas |
| Add `stack`, `subtype`, `channel`, `project` to `ai_agents` + UI to edit | 3-5d | Anunay tab |
| Activate `agent_versions` (versioning system) | already in roadmap per user | Founders tab |
| Build `bot_requests` workflow + UI | 5-7d | Founders tab |
| SQL flag — backfill `campaign_lead.sql` coverage (currently 0.15%) | 2-3d | Jitesh tab |
| Migrate `projects.json` → `client_projects` collection | 1d | Live revenue |
| Data quality cleanup | 1d | Per-owner accuracy |

**Total: ~2-3 weeks of focused work** to reach full V_FULL.

V_NOW dashboard can ship today with mock-then-live wiring in 2-3 days (just write the MongoDB aggregation queries).
