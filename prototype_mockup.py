"""
Static prototype with hardcoded sample data.
For stakeholder approval — no DB connection needed.
"""
import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, timedelta

st.set_page_config(page_title="Call Analytics — Prototype", page_icon="📞", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="metric-container"] {
        background-color: #f7f9fc;
        border: 1px solid #e0e4ea;
        border-radius: 10px;
        padding: 16px 20px;
    }
    .section-title { font-size: 1.1rem; font-weight: 600; color: #333; margin-bottom: 0.5rem; }
    .proto-banner {
        background: #fff3cd; border: 1px solid #ffc107; padding: 8px 14px;
        border-radius: 6px; font-size: 0.85rem; color: #856404; margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ─── SAMPLE DATA (hardcoded) ──────────────────────────────────────────────────

OWNERS = ["shriya@revspot.ai", "rahul.soren@revspot.ai", "vaibhav@revspot.ai", "prathamesh@revspot.ai"]
CLIENTS = ["Godrej", "Kalpataru", "Bhavisha Homes", "Century", "Leverage Edu", "Assetz", "Prestige"]

AGENTS = [
    {"Agent": "godrej_aveline_sv",        "Owner": "shriya@revspot.ai",      "Client": "Godrej",         "Bot Status": "Running", "Dialled": 209,  "Connected": 140, "Interacted": 138, "Completed": 92, "Qualified": 14},
    {"Agent": "godrej_horizon_sv",        "Owner": "shriya@revspot.ai",      "Client": "Godrej",         "Bot Status": "Running", "Dialled": 944,  "Connected": 331, "Interacted": 190, "Completed": 122, "Qualified": 5},
    {"Agent": "godrej_ivara_outbound",    "Owner": "rahul.soren@revspot.ai", "Client": "Godrej",         "Bot Status": "Running", "Dialled": 4867, "Connected": 1881,"Interacted": 1721,"Completed": 1140,"Qualified": 14},
    {"Agent": "godrej_reserve_sv",        "Owner": "rahul.soren@revspot.ai", "Client": "Godrej",         "Bot Status": "Running", "Dialled": 1113, "Connected": 376, "Interacted": 243, "Completed": 168, "Qualified": 3},
    {"Agent": "kalpataru_vista_inbound",  "Owner": "vaibhav@revspot.ai",     "Client": "Kalpataru",      "Bot Status": "Paused",  "Dialled": 363,  "Connected": 258, "Interacted": 233, "Completed": 210, "Qualified": 33},
    {"Agent": "kalpataru_vista_outbound", "Owner": "vaibhav@revspot.ai",     "Client": "Kalpataru",      "Bot Status": "Paused",  "Dialled": 6892, "Connected": 5191,"Interacted": 4368,"Completed": 3850,"Qualified": 24},
    {"Agent": "bhavisha_zurich_outbound", "Owner": "prathamesh@revspot.ai",  "Client": "Bhavisha Homes", "Bot Status": "Running", "Dialled": 2996, "Connected": 1289,"Interacted": 1146,"Completed": 880, "Qualified": 16},
    {"Agent": "bhavisha_bilva_inbound",   "Owner": "prathamesh@revspot.ai",  "Client": "Bhavisha Homes", "Bot Status": "Running", "Dialled": 115,  "Connected": 90,  "Interacted": 88,  "Completed": 70,  "Qualified": 7},
    {"Agent": "century_mirai_outbound",   "Owner": "shriya@revspot.ai",      "Client": "Century",        "Bot Status": "Running", "Dialled": 1895, "Connected": 900, "Interacted": 888, "Completed": 580, "Qualified": 4},
    {"Agent": "century_winning",          "Owner": "shriya@revspot.ai",      "Client": "Century",        "Bot Status": "Running", "Dialled": 1596, "Connected": 690, "Interacted": 690, "Completed": 410, "Qualified": 24},
    {"Agent": "leverage_edu_outbound",    "Owner": "rahul.soren@revspot.ai", "Client": "Leverage Edu",   "Bot Status": "Running", "Dialled": 2657, "Connected": 1174,"Interacted": 1103,"Completed": 870, "Qualified": 47},
    {"Agent": "leverage_edu_inbound",     "Owner": "rahul.soren@revspot.ai", "Client": "Leverage Edu",   "Bot Status": "Running", "Dialled": 207,  "Connected": 134, "Interacted": 130, "Completed": 105, "Qualified": 13},
    {"Agent": "assetz_inbound",           "Owner": "vaibhav@revspot.ai",     "Client": "Assetz",         "Bot Status": "Running", "Dialled": 121,  "Connected": 56,  "Interacted": 36,  "Completed": 28,  "Qualified": 0},
    {"Agent": "prestige_spring_heights",  "Owner": "prathamesh@revspot.ai",  "Client": "Prestige",       "Bot Status": "Paused",  "Dialled": 317,  "Connected": 241, "Interacted": 235, "Completed": 220, "Qualified": 0},
]


def pct(n, d): return round(n / d * 100, 1) if d else 0.0


# ─── Sidebar filters ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📅 Date Range")
    preset = st.selectbox("Preset", ["Last 1 day", "Last 3 days", "Last 7 days", "Last 15 days", "Last 30 days", "All time", "Custom"], index=2)
    if preset == "Custom":
        st.date_input("Range", value=(date.today() - timedelta(days=7), date.today()))

    st.markdown("---")
    st.markdown("### 🔍 Filters")
    sel_client = st.selectbox("Client", ["All"] + CLIENTS)
    sel_owner  = st.selectbox("Bot Owner", ["All"] + OWNERS)
    sel_status = st.selectbox("Bot Status", ["All", "Running", "Paused"])

    df = pd.DataFrame(AGENTS)
    if sel_client != "All": df = df[df["Client"] == sel_client]
    if sel_owner  != "All": df = df[df["Owner"]  == sel_owner]
    if sel_status != "All": df = df[df["Bot Status"] == sel_status]

    sel_agent = st.selectbox("Bot / Agent (single → drill-down)", ["—"] + df["Agent"].tolist())

    st.button("🔄 Refresh Data")


# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("## 📞 Call Analytics Dashboard")
st.markdown('<div class="proto-banner">⚠ PROTOTYPE — sample data for stakeholder review. Not connected to live DB.</div>', unsafe_allow_html=True)

filt = [f"📅 **{preset}**"]
if sel_client != "All": filt.append(f"Client: **{sel_client}**")
if sel_owner  != "All": filt.append(f"Owner: **{sel_owner}**")
if sel_status != "All": filt.append(f"Status: **{sel_status}**")
st.info("Filters active — " + "  |  ".join(filt))


# ─── Aggregates ───────────────────────────────────────────────────────────────

ud = int(df["Dialled"].sum())
uc = int(df["Connected"].sum())
ui = int(df["Interacted"].sum())
ucp = int(df["Completed"].sum())
uq = int(df["Qualified"].sum())


# ─── Volume Metrics ───────────────────────────────────────────────────────────

st.markdown('<p class="section-title">📊 Volume Metrics</p>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Unique Dialled", f"{ud:,}")
c2.metric("Unique Connected", f"{uc:,}")
c3.metric("Unique Interacted", f"{ui:,}")
c4.metric("Unique Completed", f"{ucp:,}", help="Calls that ended normally (not abrupt, not voicemail)")
c5.metric("Unique Qualified", f"{uq:,}")

st.markdown("---")


# ─── Rate Metrics — lead-level funnel ────────────────────────────────────────

st.markdown('<p class="section-title">📈 Funnel Rates (lead-level)</p>', unsafe_allow_html=True)
r1, r2, r3, r4 = st.columns(4)
r1.metric("Connect %",  f"{pct(uc, ud)}%",  help="Unique connected ÷ unique dialled")
r2.metric("Interact %", f"{pct(ui, uc)}%",  help="Unique interacted ÷ unique connected")
r3.metric("Complete %", f"{pct(ucp, ui)}%", help="Unique completed ÷ unique interacted")
r4.metric("Qualify %",  f"{pct(uq, ucp)}%", help="Unique qualified ÷ unique completed")

# funnel visualization
funnel_df = pd.DataFrame({
    "Stage": ["Dialled", "Connected", "Interacted", "Completed", "Qualified"],
    "Leads": [ud, uc, ui, ucp, uq],
})
funnel_chart = (
    alt.Chart(funnel_df).mark_bar().encode(
        y=alt.Y("Stage:N", sort=None, title=None),
        x=alt.X("Leads:Q", title="Unique Leads"),
        color=alt.Color("Stage:N", legend=None,
                        scale=alt.Scale(scheme="blues", reverse=True)),
        tooltip=["Stage", "Leads"],
    ).properties(height=200)
)
st.altair_chart(funnel_chart, use_container_width=True)

st.markdown("---")


# ─── Per-Agent Table ──────────────────────────────────────────────────────────

st.markdown('<p class="section-title">🗂️ Per-Agent Breakdown</p>', unsafe_allow_html=True)
table = df.copy()
table["Connect %"]  = table.apply(lambda r: f"{pct(r['Connected'],   r['Dialled'])}%", axis=1)
table["Interact %"] = table.apply(lambda r: f"{pct(r['Interacted'],  r['Connected'])}%", axis=1)
table["Complete %"] = table.apply(lambda r: f"{pct(r['Completed'],   r['Interacted'])}%", axis=1)
table["Qualify %"]  = table.apply(lambda r: f"{pct(r['Qualified'],   r['Completed'])}%", axis=1)
cols = ["Agent", "Owner", "Client", "Bot Status",
        "Dialled", "Connected", "Interacted", "Completed", "Qualified",
        "Connect %", "Interact %", "Complete %", "Qualify %"]
st.dataframe(table[cols], use_container_width=True, hide_index=True)

st.markdown("---")


# ─── Per-Bot Drill-down ───────────────────────────────────────────────────────

st.markdown('<p class="section-title">🔍 Per-Bot Drill-down</p>', unsafe_allow_html=True)

if sel_agent != "—":
    bot = df[df["Agent"] == sel_agent].iloc[0]
    h1, h2, h3, h4 = st.columns(4)
    h1.markdown(f"**Bot:** `{sel_agent}`")
    h2.markdown(f"**Owner:** {bot['Owner']}")
    h3.markdown(f"**Client:** {bot['Client']}")
    h4.markdown(f"**Status:** {bot['Bot Status']}")

    # per-bot date filter (independent)
    st.selectbox("Drill-down date range", ["Last 7 days", "Last 15 days", "Last 30 days", "Custom"], key="drill_date")

    # fake daily trend
    import random
    random.seed(hash(sel_agent) % 1000)
    base_connect = pct(bot["Connected"], bot["Dialled"])
    base_inter   = pct(bot["Interacted"], bot["Connected"])
    base_comp    = pct(bot["Completed"], bot["Interacted"])
    base_qual    = pct(bot["Qualified"], bot["Completed"])

    days = pd.date_range(end=date.today(), periods=14)
    trend = pd.DataFrame({
        "Date": days,
        "Connect %":  [max(0, min(100, base_connect + random.uniform(-8, 8)))  for _ in days],
        "Interact %": [max(0, min(100, base_inter   + random.uniform(-8, 8)))  for _ in days],
        "Complete %": [max(0, min(100, base_comp    + random.uniform(-8, 8)))  for _ in days],
        "Qualify %":  [max(0, min(100, base_qual    + random.uniform(-3, 3)))  for _ in days],
    })

    long = trend.melt("Date", var_name="Metric", value_name="Percentage")
    chart = (
        alt.Chart(long).mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("Date:T"),
            y=alt.Y("Percentage:Q", title="Rate (%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Metric:N", sort=["Connect %", "Interact %", "Complete %", "Qualify %"]),
            tooltip=["Date:T", "Metric:N", alt.Tooltip("Percentage:Q", format=".1f")],
        ).properties(height=380)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Multi-line trend — showing how each funnel rate evolves day-by-day for this bot.")
else:
    st.caption("👉 Pick a single bot in the sidebar to see daily trends.")


st.caption("Prototype — built 2026-04-25 — for review by leadership before wiring live MongoDB queries.")
