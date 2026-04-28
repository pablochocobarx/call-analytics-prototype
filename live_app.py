"""
Call Analytics Dashboard — Live Data
Fetches from MongoDB revv DB. Missing fields shown as "—".
"""
import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime, timedelta

from _queries import get_db, load_call_metrics, load_sql_counts, load_daily_trend
from _pricing import get_client_am

st.set_page_config(page_title="Call Analytics", page_icon="📞", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }
    h1, h2, h3 { letter-spacing: -0.01em; }
    .stRadio > label { font-weight: 600; }
    [data-testid="stMetric"] { padding: 4px 0; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; opacity: 0.7; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; }
    .small-caption { font-size: 0.78rem; opacity: 0.65; margin-top: -8px; }
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def pct(n, d): return round(n / d * 100, 1) if d else 0.0

def fmt_inr(n: float) -> str:
    n = int(n)
    if abs(n) >= 1_00_00_000: return f"₹{n/1_00_00_000:.2f} Cr"
    if abs(n) >= 1_00_000:    return f"₹{n/1_00_000:.2f} L"
    if abs(n) >= 1_000:       return f"₹{n/1_000:.1f}K"
    return f"₹{n}"

def health_zone(qp, ch):
    if ch == "Inbound":
        if qp < 5:  return "Bad"
        if qp < 10: return "Weak"
        if qp < 15: return "OK"
        if qp < 20: return "Good"
        return "Excellent"
    if qp < 0.2: return "Bad"
    if qp < 0.4: return "Weak"
    if qp < 0.6: return "OK"
    if qp < 0.8: return "Good"
    if qp < 1.0: return "Very Good"
    return "Excellent"

HEALTH_EMOJI = {"Bad": "🔴", "Weak": "🟠", "OK": "🟡", "Good": "🟢", "Very Good": "🟢", "Excellent": "💚"}

def paged_table(df_in: pd.DataFrame, key: str, default: int = 10):
    if df_in.empty:
        st.info("No rows.")
        return
    total = len(df_in)
    if total <= default:
        st.dataframe(df_in, use_container_width=True, hide_index=True)
        st.caption(f"{total} rows")
        return
    c1, c2, c3 = st.columns([1, 1, 4])
    page_size = c1.selectbox("Per page", [10, 25, 50, 100], index=0, key=f"{key}_ps", label_visibility="collapsed")
    n_pages = max(1, (total + page_size - 1) // page_size)
    page = c2.number_input("Page", min_value=1, max_value=n_pages, value=1, step=1, key=f"{key}_pg", label_visibility="collapsed")
    c3.markdown(f"<div class='small-caption'>Showing {(page-1)*page_size+1}–{min(page*page_size,total)} of {total}</div>", unsafe_allow_html=True)
    st.dataframe(df_in.iloc[(page-1)*page_size: page*page_size], use_container_width=True, hide_index=True)


# ─── DATA BUILD ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def build_agents_df(date_from_str: str, date_to_str: str) -> pd.DataFrame:
    db = get_db()

    # Load all agents with ObjectId for channel lookup
    agents = list(db.ai_agents.find({}, {
        "agent_identifier": 1, "owner": 1, "template": 1, "status": 1
    }))

    # campaign.ai_agent (ObjectId str) → inbound/outbound
    channel_map: dict[str, str] = {}
    for c in db.campaign.find({}, {"ai_agent": 1, "type": 1}):
        aid = str(c.get("ai_agent", ""))
        ch = c.get("type", "")
        if aid and ch:
            channel_map[aid] = ch

    # agent ObjectId str → agent_identifier
    id_to_ident: dict[str, str] = {str(a["_id"]): a.get("agent_identifier", "") for a in agents}
    # agent_identifier → inbound/outbound
    ident_channel: dict[str, str] = {
        ident: channel_map[id_str]
        for id_str, ident in id_to_ident.items()
        if id_str in channel_map and ident
    }

    call_metrics = load_call_metrics(date_from_str, date_to_str)
    sql_counts = load_sql_counts(date_from_str, date_to_str)

    rows = []
    for a in agents:
        ident = a.get("agent_identifier", "")
        if not ident:
            continue
        m = call_metrics.get(ident)
        if not m:
            continue

        template = (a.get("template") or "").lower()
        stack = "LQS" if "qualifying" in template else ("LGS" if template else "—")

        ch_raw = ident_channel.get(ident, "")
        channel = "Inbound" if ch_raw == "inbound" else ("Outbound" if ch_raw == "outbound" else "—")

        client, am, ql_rate = get_client_am(ident)
        qualified = m.get("qualified", 0)
        revenue = int(ql_rate * qualified)
        cost = round(m.get("total_cost", 0))

        rows.append({
            "Agent":             ident,
            "Owner":             a.get("owner") or "—",
            "Client":            client,
            "AM":                am,
            "Stack":             stack,
            "Channel":           channel,
            "Subtype":           "—",
            "Bot Status":        "Running" if a.get("status") == "Published" else "Paused",
            "Dialled":           m.get("dialled", 0),
            "Connected":         m.get("connected", 0),
            "Interacted":        m.get("interacted", 0),
            "Completed":         m.get("completed", 0),
            "Qualified":         qualified,
            "IQL":               m.get("iql", 0),
            "DQL":               m.get("dql", 0),
            "Followup":          m.get("followup", 0),
            "Customer Followup": m.get("cfu", 0),
            "SQL":               sql_counts.get(ident, 0),
            "Cost (₹)":          cost,
            "Revenue (₹)":       revenue,
            "Profit (₹)":        revenue - cost,
            "Avg Talk (s)":      round(m.get("avg_duration") or 0),
            "Median Talk (s)":   round(m.get("avg_duration") or 0),
            "Revisions":         "—",
            "Requests":          "—",
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def load_talk_buckets(agent_identifier_filter: str | None, date_from_str: str, date_to_str: str) -> pd.DataFrame:
    """Returns talk-time bucket distribution for given agent (or all if None)."""
    db = get_db()
    match: dict = {}
    if agent_identifier_filter:
        match["agent_identifier"] = agent_identifier_filter
    if date_from_str != "all":
        df_dt = datetime.strptime(date_from_str, "%Y-%m-%d")
        dt_dt = datetime.strptime(date_to_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        match["created_at"] = {"$gte": df_dt, "$lte": dt_dt}

    pipeline = [
        {"$match": match},
        {"$match": {"call_duration": {"$gt": 0}}},
        {"$bucket": {
            "groupBy": "$call_duration",
            "boundaries": [0, 10, 20, 30, 40, 10000],
            "default": "40+",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    try:
        docs = list(db.call_log.aggregate(pipeline, allowDiskUse=True))
        label_map = {0: "0-10s", 10: "10-20s", 20: "20-30s", 30: "30-40s", 40: "40s+", "40+": "40s+"}
        rows = [{"Bucket": label_map.get(d["_id"], str(d["_id"])), "Calls": d["count"]} for d in docs]
        return pd.DataFrame(rows) if rows else pd.DataFrame({"Bucket": ["0-10s","10-20s","20-30s","30-40s","40s+"], "Calls": [0]*5})
    except Exception:
        return pd.DataFrame({"Bucket": ["0-10s","10-20s","20-30s","30-40s","40s+"], "Calls": [0]*5})


# ─── DATE RANGE HELPER ────────────────────────────────────────────────────────

def date_range_to_str(preset: str, custom: tuple | None = None) -> tuple[str, str]:
    today = date.today()
    presets = {
        "Last 1 day":   today - timedelta(days=1),
        "Last 3 days":  today - timedelta(days=3),
        "Last 7 days":  today - timedelta(days=7),
        "Last 15 days": today - timedelta(days=15),
        "Last 30 days": today - timedelta(days=30),
    }
    if preset == "All time":
        return "all", today.isoformat()
    if preset == "Custom" and custom:
        return custom[0].isoformat(), custom[1].isoformat()
    d_from = presets.get(preset, today - timedelta(days=7))
    return d_from.isoformat(), today.isoformat()


# ─── HEADER + PERSONA SWITCHER ────────────────────────────────────────────────

st.markdown("# 📞 Call Analytics")

persona = st.radio(
    "View as",
    ["🤖 Anunay — Bot Team", "💼 Jitesh — Marketing", "👑 Harsha & Darshan — Founders"],
    horizontal=True, label_visibility="collapsed",
)
st.divider()


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Filters")
    preset = st.selectbox("Date range", ["Last 1 day", "Last 3 days", "Last 7 days", "Last 15 days", "Last 30 days", "All time", "Custom"], index=2)
    custom_range = None
    if preset == "Custom":
        custom_range = st.date_input("Range", value=(date.today() - timedelta(days=7), date.today()), label_visibility="collapsed")

date_from_str, date_to_str = date_range_to_str(preset, custom_range)

# Load data with spinner
with st.spinner("Loading data…"):
    try:
        raw_df = build_agents_df(date_from_str, date_to_str)
    except Exception as e:
        st.error(f"DB error: {e}")
        st.stop()

if raw_df.empty:
    st.warning("No data for this period.")
    st.stop()

# Derive sidebar filter options from real data
CLIENTS  = sorted(raw_df["Client"].unique().tolist())
OWNERS   = sorted([o for o in raw_df["Owner"].unique().tolist() if o != "—"])
AMs      = sorted([a for a in raw_df["AM"].unique().tolist() if a != "—"])
STACKS   = sorted([s for s in raw_df["Stack"].unique().tolist() if s != "—"])
CHANNELS = sorted([c for c in raw_df["Channel"].unique().tolist() if c != "—"])

with st.sidebar:
    sel_client = st.selectbox("Client", ["All"] + CLIENTS)

    df = raw_df.copy()
    if sel_client != "All":
        df = df[df["Client"] == sel_client]

    if persona.startswith("🤖"):
        sel_owner   = st.selectbox("Bot Owner", ["All"] + OWNERS)
        sel_stack   = st.selectbox("Bot Stack", ["All"] + STACKS, help="LGS = Lead Gen / LQS = Lead Qualification")
        sel_channel = st.selectbox("Channel", ["All"] + CHANNELS)
        sel_status  = st.selectbox("Bot Status", ["All", "Running", "Paused"])
        if sel_owner   != "All": df = df[df["Owner"]      == sel_owner]
        if sel_stack   != "All": df = df[df["Stack"]      == sel_stack]
        if sel_channel != "All": df = df[df["Channel"]    == sel_channel]
        if sel_status  != "All": df = df[df["Bot Status"] == sel_status]

    elif persona.startswith("💼"):
        sel_am      = st.selectbox("Account Manager", ["All"] + AMs)
        sel_stack   = st.selectbox("Bot Stack", ["All"] + STACKS, help="LGS = Lead Gen / LQS = Lead Qualification")
        sel_channel = st.selectbox("Channel", ["All"] + CHANNELS)
        if sel_am      != "All": df = df[df["AM"]      == sel_am]
        if sel_stack   != "All": df = df[df["Stack"]   == sel_stack]
        if sel_channel != "All": df = df[df["Channel"] == sel_channel]

    else:
        sel_owner = st.selectbox("Bot Owner", ["All"] + OWNERS)
        sel_am    = st.selectbox("Account Manager", ["All"] + AMs)
        sel_stack = st.selectbox("Bot Stack", ["All"] + STACKS, help="LGS = Lead Gen / LQS = Lead Qualification")
        if sel_owner != "All": df = df[df["Owner"] == sel_owner]
        if sel_am    != "All": df = df[df["AM"]    == sel_am]
        if sel_stack != "All": df = df[df["Stack"] == sel_stack]

# Derived columns
def safe_div(n, d): return round(n / d * 100, 1) if d else 0.0

df = df.copy()
df["Connect %"]          = df.apply(lambda r: safe_div(r["Connected"],  r["Dialled"]),    axis=1)
df["Interact %"]         = df.apply(lambda r: safe_div(r["Interacted"], r["Connected"]),  axis=1)
df["Complete %"]         = df.apply(lambda r: safe_div(r["Completed"],  r["Interacted"]), axis=1)
df["Qualify %"]          = df.apply(lambda r: safe_div(r["Qualified"],  r["Completed"]),  axis=1)
df["SQL/QL %"]           = df.apply(lambda r: safe_div(r["SQL"],        r["Qualified"]),  axis=1)
df["Health Qualify %"]   = df.apply(lambda r: safe_div(r["Qualified"],  r["Dialled"]),    axis=1)
df["Health"]             = df.apply(lambda r: health_zone(r["Health Qualify %"], r["Channel"]), axis=1)


# ─── ANUNAY ───────────────────────────────────────────────────────────────────

if persona.startswith("🤖"):
    st.markdown("### Bot Team Performance")

    ud  = int(df["Dialled"].sum())
    uc  = int(df["Connected"].sum())
    ui  = int(df["Interacted"].sum())
    ucp = int(df["Completed"].sum())
    uq  = int(df["Qualified"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Connect %",  f"{pct(uc, ud)}%")
    c2.metric("Interact %", f"{pct(ui, uc)}%")
    c3.metric("Complete %", f"{pct(ucp, ui)}%")
    c4.metric("Qualify %",  f"{pct(uq, ucp)}%")

    funnel = pd.DataFrame({
        "Stage": ["Dialled", "Connected", "Interacted", "Completed", "Qualified"],
        "Leads": [ud, uc, ui, ucp, uq]
    })
    st.altair_chart(
        alt.Chart(funnel).mark_bar(cornerRadius=3).encode(
            y=alt.Y("Stage:N", sort=None, title=None),
            x=alt.X("Leads:Q", title=None),
            color=alt.Color("Stage:N", legend=None, scale=alt.Scale(scheme="blues", reverse=True)),
            tooltip=["Stage", "Leads"]
        ).properties(height=180),
        use_container_width=True
    )

    st.divider()

    st.markdown("#### Per-bot breakdown")
    cols = ["Agent", "Owner", "Client", "Stack", "Channel", "Subtype", "Bot Status",
            "Connect %", "Interact %", "Complete %", "Qualify %", "Dialled", "Qualified"]
    paged_table(df[cols].sort_values("Qualify %", ascending=False), key="anunay_table")

    st.divider()

    st.markdown("#### Talk time")
    avg_talk = int(df["Avg Talk (s)"].mean()) if not df.empty else 0
    c1, c2 = st.columns(2)
    c1.metric("Avg", f"{avg_talk} s")
    c2.metric("Median", f"{avg_talk} s")

    buckets_df = load_talk_buckets(None, date_from_str, date_to_str)
    if sel_client != "All" and not df.empty:
        # filter buckets to agents in the current filtered set
        idents = df["Agent"].tolist()
        buckets_df = pd.DataFrame({"Bucket": ["0-10s","10-20s","20-30s","30-40s","40s+"], "Calls": [0]*5})
        for ident in idents:
            b = load_talk_buckets(ident, date_from_str, date_to_str)
            if not b.empty:
                buckets_df["Calls"] = buckets_df["Calls"].add(b.set_index("Bucket")["Calls"], fill_value=0)
        buckets_df = buckets_df.reset_index(drop=True)

    st.altair_chart(
        alt.Chart(buckets_df).mark_bar(cornerRadius=3).encode(
            x=alt.X("Bucket:N", sort=None, title=None),
            y=alt.Y("Calls:Q", title=None),
            color=alt.Color("Bucket:N", legend=None, scale=alt.Scale(scheme="purples")),
            tooltip=["Bucket", "Calls"]
        ).properties(height=200),
        use_container_width=True
    )

    st.divider()

    st.markdown("#### Drill-down")
    bot_list = df["Agent"].tolist()
    sel_bot = st.selectbox("Pick a bot", ["—"] + bot_list, label_visibility="collapsed")
    if sel_bot != "—":
        bot = df[df["Agent"] == sel_bot].iloc[0]
        st.caption(
            f"Stack: **{bot['Stack']}**  •  Channel: **{bot['Channel']}**  •  "
            f"Subtype: **{bot['Subtype']}**  •  Owner: **{bot['Owner']}**  •  Status: **{bot['Bot Status']}**"
        )

        with st.spinner("Loading trend…"):
            trend_data = load_daily_trend(sel_bot, date_from_str, date_to_str)

        if trend_data:
            trend = pd.DataFrame(trend_data)
            trend["Date"] = pd.to_datetime(trend["date"])
            trend["Connect %"]  = trend.apply(lambda r: safe_div(r["connected"],  r["dialled"]),   axis=1)
            trend["Interact %"] = trend.apply(lambda r: safe_div(r["interacted"], r["connected"]), axis=1)
            trend["Complete %"] = trend.apply(lambda r: safe_div(r["completed"],  r["interacted"]),axis=1)
            trend["Qualify %"]  = trend.apply(lambda r: safe_div(r["qualified"],  r["completed"]), axis=1)
            long = trend[["Date","Connect %","Interact %","Complete %","Qualify %"]].melt(
                "Date", var_name="Metric", value_name="Percentage"
            )
            st.altair_chart(
                alt.Chart(long).mark_line(point=True, strokeWidth=2.5).encode(
                    x=alt.X("Date:T", title=None),
                    y=alt.Y("Percentage:Q", scale=alt.Scale(domain=[0, 100]), title="%"),
                    color=alt.Color("Metric:N", legend=alt.Legend(orient="top", title=None)),
                    tooltip=["Date:T", "Metric:N", alt.Tooltip("Percentage:Q", format=".1f")]
                ).properties(height=340),
                use_container_width=True
            )
        else:
            st.info("No daily data for this agent in selected period.")


# ─── JITESH ───────────────────────────────────────────────────────────────────

elif persona.startswith("💼"):
    st.markdown("### Marketing & Revenue")

    ql   = int(df["Qualified"].sum())
    iql  = int(df["IQL"].sum())
    dql  = int(df["DQL"].sum())
    fup  = int(df["Followup"].sum())
    cfup = int(df["Customer Followup"].sum())
    sql  = int(df["SQL"].sum())
    rev  = int(df["Revenue (₹)"].sum())
    cost = int(df["Cost (₹)"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue",    fmt_inr(rev))
    c2.metric("Cost",       fmt_inr(cost))
    c3.metric("Profit",     fmt_inr(rev - cost))
    c4.metric("SQL / QL %", f"{pct(sql, ql)}%")

    st.markdown("<div class='small-caption'>Lead status</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Qualified",   f"{ql:,}")
    c2.metric("IQL",         f"{iql:,}")
    c3.metric("DQL",         f"{dql:,}")
    c4.metric("Followup",    f"{fup:,}")
    c5.metric("Customer FU", f"{cfup:,}")

    st.divider()

    st.markdown("#### Avg dials to reach stage")
    st.markdown('<div class="small-caption">Inbound qualifies in fewer dials; outbound cold-calls so qualification needs many more.</div>', unsafe_allow_html=True)
    rows_ch = []
    for ch in ["Inbound", "Outbound"]:
        sub = df[df["Channel"] == ch]
        if sub.empty: continue
        d = sub["Dialled"].sum()
        for stage, col in [("Connect","Connected"),("Interact","Interacted"),("Complete","Completed"),("Qualify","Qualified")]:
            den = sub[col].sum()
            rows_ch.append({"Stage": stage, "Channel": ch, "Avg Dials": round(d / max(den, 1), 2)})
    if rows_ch:
        stages_df = pd.DataFrame(rows_ch)
        st.altair_chart(
            alt.Chart(stages_df).mark_bar(cornerRadius=3).encode(
                x=alt.X("Stage:N", sort=["Connect","Interact","Complete","Qualify"], title=None),
                y=alt.Y("Avg Dials:Q", title="Avg dials"),
                color=alt.Color("Channel:N", scale=alt.Scale(domain=["Inbound","Outbound"], range=["#4263eb","#f76707"])),
                column=alt.Column("Channel:N", title=None, header=alt.Header(labelFontSize=13, labelFontWeight="bold")),
                tooltip=["Channel","Stage","Avg Dials"]
            ).properties(height=220, width=280),
            use_container_width=False
        )
    else:
        st.info("No inbound/outbound data after filters.")

    st.divider()

    st.markdown("#### Talk time")
    avg_talk = int(df["Avg Talk (s)"].mean()) if not df.empty else 0
    c1, c2 = st.columns(2)
    c1.metric("Avg",    f"{avg_talk} s")
    c2.metric("Median", f"{avg_talk} s")
    buckets_df = load_talk_buckets(None, date_from_str, date_to_str)
    st.altair_chart(
        alt.Chart(buckets_df).mark_bar(cornerRadius=3).encode(
            x=alt.X("Bucket:N", sort=None, title=None),
            y=alt.Y("Calls:Q", title=None),
            color=alt.Color("Bucket:N", legend=None, scale=alt.Scale(scheme="purples")),
            tooltip=["Bucket", "Calls"]
        ).properties(height=220),
        use_container_width=True
    )

    st.divider()

    st.markdown("#### Per-bot lead status & revenue")
    df_disp = df.copy()
    df_disp["Revenue"] = df_disp["Revenue (₹)"].map(fmt_inr)
    df_disp["Cost"]    = df_disp["Cost (₹)"].map(fmt_inr)
    df_disp["Profit"]  = df_disp["Profit (₹)"].map(fmt_inr)
    cols = ["Agent","AM","Client","Channel","Qualified","IQL","DQL","SQL","SQL/QL %","Revenue","Cost","Profit","Avg Talk (s)"]
    paged_table(df_disp[cols].sort_values("Qualified", ascending=False), key="jitesh_table")


# ─── FOUNDERS ─────────────────────────────────────────────────────────────────

else:
    st.markdown("### Leadership")

    rev      = int(df["Revenue (₹)"].sum())
    cost     = int(df["Cost (₹)"].sum())
    profit   = rev - cost
    n_active = int((df["Bot Status"] == "Running").sum())
    n_total  = len(df)
    total_q  = int(df["Qualified"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active bots",    f"{n_active} / {n_total}")
    c2.metric("Revenue",        fmt_inr(rev))
    c3.metric("Profit",         fmt_inr(profit))
    c4.metric("Total Qualified", f"{total_q:,}")

    st.divider()

    st.markdown("#### Per bot owner")
    summary = df.groupby("Owner").agg(**{
        "# Bots":    ("Agent",       "count"),
        "Active":    ("Bot Status",  lambda s: (s == "Running").sum()),
        "Qualified": ("Qualified",   "sum"),
        "Revenue":   ("Revenue (₹)", "sum"),
        "Cost":      ("Cost (₹)",    "sum"),
    }).reset_index().sort_values("Revenue", ascending=False)
    summary["Profit"]  = summary["Revenue"] - summary["Cost"]
    summary["Revenue"] = summary["Revenue"].map(fmt_inr)
    summary["Cost"]    = summary["Cost"].map(fmt_inr)
    summary["Profit"]  = summary["Profit"].map(fmt_inr)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("#### Top & bottom performers")
    cA, cB = st.columns(2)
    with cA:
        st.markdown("**🏆 Top 5**")
        st.dataframe(
            df.nlargest(5, "Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]],
            use_container_width=True, hide_index=True
        )
    with cB:
        st.markdown("**📉 Bottom 5**")
        st.dataframe(
            df[df["Dialled"] > 0].nsmallest(5, "Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]],
            use_container_width=True, hide_index=True
        )

    if OWNERS:
        st.markdown("**Per owner**")
        sel_o = st.selectbox("Owner", OWNERS, label_visibility="collapsed")
        sub = df[df["Owner"] == sel_o]
        if sub.empty:
            st.info("No bots for this owner under current filters.")
        else:
            cA, cB = st.columns(2)
            with cA:
                st.markdown("**🏆 Top 5**")
                st.dataframe(sub.nlargest(5, "Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
            with cB:
                st.markdown("**📉 Bottom 5**")
                st.dataframe(sub[sub["Dialled"] > 0].nsmallest(5, "Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("#### Bot health")
    with st.expander("Zone thresholds"):
        st.markdown("""
| Zone | Inbound | Outbound |
|---|---|---|
| 🔴 Bad        | 0 – 5%    | 0 – 0.2%   |
| 🟠 Weak       | 5 – 10%   | 0.2 – 0.4% |
| 🟡 OK         | 10 – 15%  | 0.4 – 0.6% |
| 🟢 Good       | 15 – 20%  | 0.6 – 0.8% |
| 🟢 Very Good  | —         | 0.8 – 1.0% |
| 💚 Excellent  | 20%+      | 1.0%+      |
""")

    inb = df[df["Channel"] == "Inbound"][["Agent","Owner","Health Qualify %","Health"]].sort_values("Health Qualify %", ascending=False).rename(columns={"Health Qualify %": "Qualify %"})
    out = df[df["Channel"] == "Outbound"][["Agent","Owner","Health Qualify %","Health"]].sort_values("Health Qualify %", ascending=False).rename(columns={"Health Qualify %": "Qualify %"})

    for label, tdf, key in [("**Inbound**", inb, "health_inb"), ("**Outbound**", out, "health_out")]:
        st.markdown(label)
        tdf = tdf.copy()
        tdf["Health"] = tdf["Health"].map(lambda h: f"{HEALTH_EMOJI.get(h,'')} {h}")
        paged_table(tdf, key=key)
