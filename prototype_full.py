"""
Call Analytics Dashboard — Prototype v3
Static mock data. 4 tabs for 3 stakeholder personas.
For stakeholder approval before wiring live MongoDB.
"""
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import date, timedelta

st.set_page_config(page_title="Call Analytics — Prototype", page_icon="📞", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background-color: #f7f9fc;
        border: 1px solid #e0e4ea;
        border-radius: 10px;
        padding: 14px 18px;
    }
    .section-title { font-size: 1.05rem; font-weight: 600; color: #333; margin-bottom: 0.5rem; }
    .proto-banner {
        background: #fff3cd; border: 1px solid #ffc107; padding: 8px 14px;
        border-radius: 6px; font-size: 0.85rem; color: #856404; margin-bottom: 12px;
    }
    .health-cell { padding: 4px 10px; border-radius: 4px; color: white; font-weight: 600; text-align:center; }
</style>
""", unsafe_allow_html=True)


# ─── MOCK DATA ────────────────────────────────────────────────────────────────

OWNERS  = ["shriya@revspot.ai", "rahul.soren@revspot.ai", "vaibhav@revspot.ai", "prathamesh@revspot.ai", "ritesh@revspot.ai"]
CLIENTS = ["Godrej", "Kalpataru", "Bhavisha Homes", "Century", "Leverage Edu", "Assetz", "Prestige"]
STACKS  = ["LGS", "LQS"]
CHANNELS  = ["Inbound", "Outbound"]
SUBTYPES  = ["BPCL", "Bully", "Proto", "Standard"]

np.random.seed(42)

AGENTS_RAW = [
    ("godrej_aveline_sv",        "shriya@revspot.ai",     "Godrej",        "LQS","Inbound", "BPCL",     "Running", 209, 140, 138,  92,   14),
    ("godrej_horizon_sv",        "shriya@revspot.ai",     "Godrej",        "LQS","Outbound","Bully",    "Running", 944, 331, 190, 122,    5),
    ("godrej_ivara_outbound",    "rahul.soren@revspot.ai","Godrej",        "LGS","Outbound","Standard", "Running",4867,1881,1721,1140,   14),
    ("godrej_reserve_sv",        "rahul.soren@revspot.ai","Godrej",        "LQS","Inbound", "BPCL",     "Running",1113, 376, 243, 168,    3),
    ("kalpataru_vista_inbound",  "vaibhav@revspot.ai",    "Kalpataru",     "LQS","Inbound", "BPCL",     "Paused",  363, 258, 233, 210,   33),
    ("kalpataru_vista_outbound", "vaibhav@revspot.ai",    "Kalpataru",     "LGS","Outbound","Standard", "Paused", 6892,5191,4368,3850,   24),
    ("bhavisha_zurich_outbound", "prathamesh@revspot.ai", "Bhavisha Homes","LGS","Outbound","Bully",    "Running",2996,1289,1146, 880,   16),
    ("bhavisha_bilva_inbound",   "prathamesh@revspot.ai", "Bhavisha Homes","LQS","Inbound", "Proto",    "Running", 115,  90,  88,  70,    7),
    ("century_mirai_outbound",   "shriya@revspot.ai",     "Century",       "LGS","Outbound","Standard", "Running",1895, 900, 888, 580,    4),
    ("century_winning",          "shriya@revspot.ai",     "Century",       "LGS","Outbound","Bully",    "Running",1596, 690, 690, 410,   24),
    ("leverage_edu_outbound",    "rahul.soren@revspot.ai","Leverage Edu",  "LGS","Outbound","Standard", "Running",2657,1174,1103, 870,   47),
    ("leverage_edu_inbound",     "rahul.soren@revspot.ai","Leverage Edu",  "LQS","Inbound", "BPCL",     "Running", 207, 134, 130, 105,   13),
    ("assetz_inbound",           "vaibhav@revspot.ai",    "Assetz",        "LQS","Inbound", "Proto",    "Running", 121,  56,  36,  28,    0),
    ("prestige_spring_heights",  "prathamesh@revspot.ai", "Prestige",      "LQS","Inbound", "BPCL",     "Paused",  317, 241, 235, 220,    0),
    ("prestige_vaishnaoi",       "ritesh@revspot.ai",     "Prestige",      "LQS","Inbound", "Standard", "Running", 280, 201, 195, 180,   18),
    ("godrej_bannerghatta",      "ritesh@revspot.ai",     "Godrej",        "LGS","Outbound","Bully",    "Running", 286, 167, 150, 110,   28),
]

cols_a = ["Agent","Owner","Client","Stack","Channel","Subtype","Bot Status","Dialled","Connected","Interacted","Completed","Qualified"]
agents_df = pd.DataFrame(AGENTS_RAW, columns=cols_a)

# derived: IQL / DQL / Followup / Customer Followup / SQL — mock realistic distributions
def derive_lead_breakdown(row):
    interacted = row["Interacted"]
    qualified  = row["Qualified"]
    iql = int(qualified * np.random.uniform(0.4, 0.8))
    dql = int(interacted * np.random.uniform(0.10, 0.20))
    fup = int(interacted * np.random.uniform(0.15, 0.30))
    cfup = int(interacted * np.random.uniform(0.04, 0.10))
    sql = int(qualified * np.random.uniform(0.35, 0.65))
    return pd.Series([iql, dql, fup, cfup, sql])

agents_df[["IQL","DQL","Followup","Customer Followup","SQL"]] = agents_df.apply(derive_lead_breakdown, axis=1)

# revenue mock — ₹/QL by client (simplistic)
PRICE_PER_QL = {"Godrej":1200, "Kalpataru":1500, "Bhavisha Homes":900, "Century":1000, "Leverage Edu":600, "Assetz":1100, "Prestige":1400}
agents_df["Revenue (₹)"] = agents_df.apply(lambda r: r["Qualified"] * PRICE_PER_QL.get(r["Client"], 1000), axis=1)

# talk time mock — avg & median seconds
agents_df["Avg Talk (s)"]    = np.random.randint(35, 110, len(agents_df))
agents_df["Median Talk (s)"] = (agents_df["Avg Talk (s)"] * np.random.uniform(0.7, 1.0, len(agents_df))).astype(int)

# bot maker mock — for founders tab
agents_df["Revisions"] = np.random.randint(1, 8, len(agents_df))
agents_df["Requests"]  = np.random.randint(1, 5, len(agents_df))


def pct(n, d): return round(n / d * 100, 1) if d else 0.0

agents_df["Connect %"]  = (agents_df["Connected"]  / agents_df["Dialled"]   * 100).round(1)
agents_df["Interact %"] = (agents_df["Interacted"] / agents_df["Connected"] * 100).round(1)
agents_df["Complete %"] = (agents_df["Completed"]  / agents_df["Interacted"]* 100).round(1)
agents_df["Qualify %"]  = (agents_df["Qualified"]  / agents_df["Completed"] * 100).round(1)
agents_df["SQL/QL %"]   = (agents_df["SQL"]        / agents_df["Qualified"].replace(0,np.nan) * 100).round(1).fillna(0)


def health_zone(qualify_pct, channel):
    """Returns (label, color) for bot health based on qualify %."""
    if channel == "Inbound":
        if qualify_pct < 5:  return ("Bad", "#d9534f")
        if qualify_pct < 10: return ("Weak", "#f0ad4e")
        if qualify_pct < 15: return ("OK", "#ffc107")
        if qualify_pct < 20: return ("Good", "#5cb85c")
        return ("Excellent", "#28a745")
    else:  # Outbound
        if qualify_pct < 0.2: return ("Bad", "#d9534f")
        if qualify_pct < 0.4: return ("Weak", "#f0ad4e")
        if qualify_pct < 0.6: return ("OK", "#ffc107")
        if qualify_pct < 0.8: return ("Good", "#5cb85c")
        if qualify_pct < 1.0: return ("Very Good", "#28a745")
        return ("Excellent", "#1e7e34")

# qualify% for health = qualified / dialled (overall funnel %)
agents_df["Health Qualify %"] = (agents_df["Qualified"] / agents_df["Dialled"] * 100).round(2)
agents_df["Health"] = agents_df.apply(lambda r: health_zone(r["Health Qualify %"], r["Channel"])[0], axis=1)
agents_df["Health Color"] = agents_df.apply(lambda r: health_zone(r["Health Qualify %"], r["Channel"])[1], axis=1)


# ─── Sidebar (global filters) ─────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📅 Date Range")
    preset = st.selectbox("Preset", ["Last 1 day","Last 3 days","Last 7 days","Last 15 days","Last 30 days","All time","Custom"], index=2)
    if preset == "Custom":
        st.date_input("Range", value=(date.today() - timedelta(days=7), date.today()))

    st.markdown("---")
    st.markdown("### 🔍 Filters")
    sel_client = st.selectbox("Client", ["All"] + CLIENTS)
    sel_owner  = st.selectbox("Bot Owner", ["All"] + OWNERS)
    sel_stack  = st.selectbox("Bot Stack", ["All"] + STACKS,    help="LGS = Lead Gen Stack; LQS = Lead Qualification Stack")
    sel_channel= st.selectbox("Channel",   ["All"] + CHANNELS)
    sel_subtype= st.selectbox("Bot Subtype",["All"] + SUBTYPES)
    sel_status = st.selectbox("Bot Status",["All","Running","Paused"])

    df = agents_df.copy()
    if sel_client  != "All": df = df[df["Client"]     == sel_client]
    if sel_owner   != "All": df = df[df["Owner"]      == sel_owner]
    if sel_stack   != "All": df = df[df["Stack"]      == sel_stack]
    if sel_channel != "All": df = df[df["Channel"]    == sel_channel]
    if sel_subtype != "All": df = df[df["Subtype"]    == sel_subtype]
    if sel_status  != "All": df = df[df["Bot Status"] == sel_status]

    st.button("🔄 Refresh Data")


# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("## 📞 Call Analytics Dashboard")
st.markdown('<div class="proto-banner">⚠ PROTOTYPE — mock data for stakeholder review. Not connected to live DB.</div>', unsafe_allow_html=True)

filt = [f"📅 **{preset}**"]
for label, val in [("Client",sel_client),("Owner",sel_owner),("Stack",sel_stack),("Channel",sel_channel),("Subtype",sel_subtype),("Status",sel_status)]:
    if val != "All": filt.append(f"{label}: **{val}**")
st.info("Filters — " + "  |  ".join(filt))


# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab_overview, tab_bot, tab_mkt, tab_lead = st.tabs([
    "📊 Overview",
    "🤖 Bot Performance (Anunay)",
    "💼 Marketing & Revenue (Jitesh)",
    "👑 Leadership (Founders)",
])


# ===== TAB 1: OVERVIEW ========================================================
with tab_overview:
    ud = int(df["Dialled"].sum()); uc = int(df["Connected"].sum())
    ui = int(df["Interacted"].sum()); ucp = int(df["Completed"].sum()); uq = int(df["Qualified"].sum())

    st.markdown('<p class="section-title">Volume</p>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Unique Dialled", f"{ud:,}")
    c2.metric("Unique Connected", f"{uc:,}")
    c3.metric("Unique Interacted", f"{ui:,}")
    c4.metric("Unique Completed", f"{ucp:,}")
    c5.metric("Unique Qualified", f"{uq:,}")

    st.markdown('<p class="section-title">Funnel Rates (lead-level)</p>', unsafe_allow_html=True)
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Connect %",  f"{pct(uc, ud)}%")
    r2.metric("Interact %", f"{pct(ui, uc)}%")
    r3.metric("Complete %", f"{pct(ucp, ui)}%")
    r4.metric("Qualify %",  f"{pct(uq, ucp)}%")

    funnel_df = pd.DataFrame({"Stage":["Dialled","Connected","Interacted","Completed","Qualified"],"Leads":[ud,uc,ui,ucp,uq]})
    chart = alt.Chart(funnel_df).mark_bar().encode(
        y=alt.Y("Stage:N", sort=None, title=None),
        x=alt.X("Leads:Q"),
        color=alt.Color("Stage:N", legend=None, scale=alt.Scale(scheme="blues", reverse=True)),
        tooltip=["Stage","Leads"],
    ).properties(height=220)
    st.altair_chart(chart, use_container_width=True)


# ===== TAB 2: BOT PERFORMANCE (Anunay) =========================================
with tab_bot:
    st.markdown("### 🤖 Bot Performance — Anunay")
    st.caption("LGS/LQS, Inbound/Outbound, Subtype filters live in sidebar. Click a bot below for drill-down.")

    cols = ["Agent","Owner","Client","Stack","Channel","Subtype","Bot Status",
            "Dialled","Connected","Interacted","Completed","Qualified",
            "Connect %","Interact %","Complete %","Qualify %"]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🔍 Per-Bot Drill-down")
    sel_bot = st.selectbox("Select a bot", ["—"] + df["Agent"].tolist(), key="anunay_bot")
    if sel_bot != "—":
        bot = df[df["Agent"]==sel_bot].iloc[0]
        h1,h2,h3,h4,h5 = st.columns(5)
        h1.markdown(f"**Bot:** `{sel_bot}`")
        h2.markdown(f"**Stack:** {bot['Stack']}")
        h3.markdown(f"**Channel:** {bot['Channel']}")
        h4.markdown(f"**Subtype:** {bot['Subtype']}")
        h5.markdown(f"**Owner:** {bot['Owner']}")

        # mock 14-day trend
        np.random.seed(hash(sel_bot)%1000)
        days = pd.date_range(end=date.today(), periods=14)
        trend = pd.DataFrame({
            "Date": days,
            "Connect %":  np.clip(bot["Connect %"]  + np.random.uniform(-8,8,14), 0, 100),
            "Interact %": np.clip(bot["Interact %"] + np.random.uniform(-8,8,14), 0, 100),
            "Complete %": np.clip(bot["Complete %"] + np.random.uniform(-8,8,14), 0, 100),
            "Qualify %":  np.clip(bot["Qualify %"]  + np.random.uniform(-3,3,14), 0, 100),
        })
        long = trend.melt("Date", var_name="Metric", value_name="Percentage")
        chart = alt.Chart(long).mark_line(point=True, strokeWidth=2).encode(
            x="Date:T", y=alt.Y("Percentage:Q", scale=alt.Scale(domain=[0,100])),
            color="Metric:N",
            tooltip=["Date:T","Metric:N",alt.Tooltip("Percentage:Q", format=".1f")],
        ).properties(height=380)
        st.altair_chart(chart, use_container_width=True)


# ===== TAB 3: MARKETING & REVENUE (Jitesh) ====================================
with tab_mkt:
    st.markdown("### 💼 Marketing & Revenue — Jitesh")

    # lead-status totals
    ql = int(df["Qualified"].sum()); iql = int(df["IQL"].sum()); dql = int(df["DQL"].sum())
    fup = int(df["Followup"].sum()); cfup = int(df["Customer Followup"].sum())
    sql = int(df["SQL"].sum())
    rev = int(df["Revenue (₹)"].sum())

    st.markdown('<p class="section-title">Lead Status Breakdown</p>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Qualified (QL)",   f"{ql:,}")
    c2.metric("Intent Qualified (IQL)", f"{iql:,}")
    c3.metric("Disqualified (DQL)", f"{dql:,}")
    c4.metric("Follow-up", f"{fup:,}")
    c5.metric("Customer Follow-up", f"{cfup:,}")

    st.markdown('<p class="section-title">Revenue & SQL</p>', unsafe_allow_html=True)
    r1,r2,r3 = st.columns(3)
    r1.metric("Total Revenue (₹)", f"₹{rev:,}", help="Mock: QL × per-client price")
    r2.metric("SQL / QL %", f"{pct(sql, ql)}%", help="Site Qualified ÷ Qualified")
    r3.metric("Avg Revenue / Bot", f"₹{int(rev/max(len(df),1)):,}")

    # dials-to-stage (mock — avg # dials needed to hit each stage)
    st.markdown('<p class="section-title">Avg Dials to Reach Stage</p>', unsafe_allow_html=True)
    stages_df = pd.DataFrame({
        "Stage": ["First Connect","First Interact","Completed","Qualified"],
        "Avg Dials": [
            round(df["Dialled"].sum()/max(df["Connected"].sum(),1), 2),
            round(df["Dialled"].sum()/max(df["Interacted"].sum(),1), 2),
            round(df["Dialled"].sum()/max(df["Completed"].sum(),1), 2),
            round(df["Dialled"].sum()/max(df["Qualified"].sum(),1), 2),
        ],
    })
    chart = alt.Chart(stages_df).mark_bar().encode(
        x=alt.X("Stage:N", sort=None), y="Avg Dials:Q",
        color=alt.Color("Stage:N", legend=None, scale=alt.Scale(scheme="oranges")),
        tooltip=["Stage","Avg Dials"],
    ).properties(height=260)
    st.altair_chart(chart, use_container_width=True)

    # talk time stats + buckets
    st.markdown('<p class="section-title">Talk Time</p>', unsafe_allow_html=True)
    t1,t2 = st.columns(2)
    t1.metric("Overall Avg Talk Time",    f"{int(df['Avg Talk (s)'].mean())} s")
    t2.metric("Overall Median Talk Time", f"{int(df['Median Talk (s)'].median())} s")

    # talk-time bucket distribution (mock — synthesized from per-bot avgs)
    np.random.seed(7)
    total_calls = int(df["Dialled"].sum())
    buckets = pd.DataFrame({
        "Bucket": ["0-10s","10-20s","20-30s","30-40s","40s+"],
        "Calls":  [int(total_calls*p) for p in [0.18, 0.14, 0.12, 0.10, 0.46]],
    })
    chart = alt.Chart(buckets).mark_bar().encode(
        x=alt.X("Bucket:N", sort=None), y="Calls:Q",
        color=alt.Color("Bucket:N", legend=None, scale=alt.Scale(scheme="purples")),
        tooltip=["Bucket","Calls"],
    ).properties(height=240)
    st.altair_chart(chart, use_container_width=True)

    # per-bot revenue + lead status
    st.markdown('<p class="section-title">Per-Bot Lead Status & Revenue</p>', unsafe_allow_html=True)
    cols = ["Agent","Owner","Client","Qualified","IQL","DQL","Followup","Customer Followup","SQL","SQL/QL %","Revenue (₹)","Avg Talk (s)","Median Talk (s)"]
    st.dataframe(df[cols].sort_values("Revenue (₹)", ascending=False), use_container_width=True, hide_index=True)


# ===== TAB 4: LEADERSHIP (Founders) ===========================================
with tab_lead:
    st.markdown("### 👑 Leadership — Harsha & Darshan")

    # owner roll-up
    st.markdown('<p class="section-title">Per Bot Owner — Activity</p>', unsafe_allow_html=True)
    owner_summary = df.groupby("Owner").agg(
        **{
            "# Bots":      ("Agent",   "count"),
            "Active":      ("Bot Status", lambda s: (s=="Running").sum()),
            "Requests":    ("Requests", "sum"),
            "Revisions":   ("Revisions", "sum"),
            "Qualified":   ("Qualified", "sum"),
            "Revenue (₹)": ("Revenue (₹)", "sum"),
        }
    ).reset_index().sort_values("Qualified", ascending=False)
    st.dataframe(owner_summary, use_container_width=True, hide_index=True)

    # bot health heatmap
    st.markdown('<p class="section-title">Bot Health Zones</p>', unsafe_allow_html=True)
    st.caption("Inbound: based on % qualified leads. Outbound: tighter thresholds (0–1%+ scale).")

    health_df = df[["Agent","Channel","Health Qualify %","Health","Health Color"]].copy()
    chart = alt.Chart(health_df).mark_bar().encode(
        y=alt.Y("Agent:N", sort="-x", title=None),
        x=alt.X("Health Qualify %:Q", title="Qualified % of Dialled"),
        color=alt.Color("Health:N",
                        scale=alt.Scale(
                            domain=["Bad","Weak","OK","Good","Very Good","Excellent"],
                            range=["#d9534f","#f0ad4e","#ffc107","#5cb85c","#28a745","#1e7e34"]),
                        legend=alt.Legend(title="Zone")),
        tooltip=["Agent","Channel","Health Qualify %","Health"],
    ).properties(height=max(300, 24 * len(health_df)))
    st.altair_chart(chart, use_container_width=True)

    # zone bands explanation
    with st.expander("Health zone thresholds"):
        st.markdown("""
        | Zone | Inbound (Qualify %) | Outbound (Qualify %) |
        |---|---|---|
        | 🔴 Bad        | 0 – 5     | 0 – 0.2     |
        | 🟠 Weak       | 5 – 10    | 0.2 – 0.4   |
        | 🟡 OK         | 10 – 15   | 0.4 – 0.6   |
        | 🟢 Good       | 15 – 20   | 0.6 – 0.8   |
        | 🟢 Very Good  | —         | 0.8 – 1.0   |
        | 💚 Excellent  | 20+       | 1.0+        |
        """)

    # top/bottom 5 daily — overall
    st.markdown('<p class="section-title">Top 5 / Bottom 5 — Today</p>', unsafe_allow_html=True)
    cA, cB = st.columns(2)
    top5    = df.nlargest(5,  "Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]]
    bottom5 = df.nsmallest(5, "Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]]
    cA.markdown("**🏆 Top 5 (highest Qualify %)**")
    cA.dataframe(top5, use_container_width=True, hide_index=True)
    cB.markdown("**📉 Bottom 5 (lowest Qualify %)**")
    cB.dataframe(bottom5, use_container_width=True, hide_index=True)

    # top/bottom per owner
    st.markdown('<p class="section-title">Top 5 / Bottom 5 — Per Owner</p>', unsafe_allow_html=True)
    sel_o = st.selectbox("Owner", OWNERS, key="lead_owner")
    sub = df[df["Owner"]==sel_o]
    if sub.empty:
        st.info("No bots for this owner under current filters.")
    else:
        cA, cB = st.columns(2)
        cA.markdown(f"**🏆 Top 5 — {sel_o}**")
        cA.dataframe(sub.nlargest(5, "Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
        cB.markdown(f"**📉 Bottom 5 — {sel_o}**")
        cB.dataframe(sub.nsmallest(5, "Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)


st.caption("Prototype • mock data • for stakeholder review before live wiring")
