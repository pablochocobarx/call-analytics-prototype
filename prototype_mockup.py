"""
Call Analytics Dashboard — V_FULL with Persona Switcher
3 personas, each sees only their own filters + metrics.
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
        background-color: #f7f9fc; border: 1px solid #e0e4ea;
        border-radius: 10px; padding: 14px 18px;
    }
    .section-title { font-size: 1.05rem; font-weight: 600; color: #333; margin-bottom: 0.5rem; }
    .proto-banner {
        background: #fff3cd; border: 1px solid #ffc107; padding: 8px 14px;
        border-radius: 6px; font-size: 0.85rem; color: #856404; margin-bottom: 12px;
    }
    .persona-card {
        background: #f0f4ff; border: 2px solid #4263eb; padding: 10px 16px;
        border-radius: 8px; font-weight: 600; color: #1c3faa; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


OWNERS  = ["shriya@revspot.ai","rahul.soren@revspot.ai","vaibhav@revspot.ai","prathamesh@revspot.ai","ritesh@revspot.ai"]
CLIENTS = ["Godrej","Kalpataru","Bhavisha Homes","Century","Leverage Edu","Assetz","Prestige"]
STACKS  = ["LGS","LQS"]
CHANNELS = ["Inbound","Outbound"]
SUBTYPES = ["BPCL","Bully","Proto","Standard"]
AMs     = ["Vikram","Abhay","Pooja","Sakshi","Bhoomika","Rohit","Naina"]

np.random.seed(42)
AGENTS_RAW = [
    ("godrej_aveline_sv",        "shriya@revspot.ai",     "Godrej",        "Vikram",  "LQS","Inbound", "BPCL",     "Running", 209, 140, 138,  92,   14),
    ("godrej_horizon_sv",        "shriya@revspot.ai",     "Godrej",        "Vikram",  "LQS","Outbound","Bully",    "Running", 944, 331, 190, 122,    5),
    ("godrej_ivara_outbound",    "rahul.soren@revspot.ai","Godrej",        "Vikram",  "LGS","Outbound","Standard", "Running",4867,1881,1721,1140,   14),
    ("godrej_reserve_sv",        "rahul.soren@revspot.ai","Godrej",        "Vikram",  "LQS","Inbound", "BPCL",     "Running",1113, 376, 243, 168,    3),
    ("kalpataru_vista_inbound",  "vaibhav@revspot.ai",    "Kalpataru",     "Pooja",   "LQS","Inbound", "BPCL",     "Paused",  363, 258, 233, 210,   33),
    ("kalpataru_vista_outbound", "vaibhav@revspot.ai",    "Kalpataru",     "Pooja",   "LGS","Outbound","Standard", "Paused", 6892,5191,4368,3850,   24),
    ("bhavisha_zurich_outbound", "prathamesh@revspot.ai", "Bhavisha Homes","Abhay",   "LGS","Outbound","Bully",    "Running",2996,1289,1146, 880,   16),
    ("bhavisha_bilva_inbound",   "prathamesh@revspot.ai", "Bhavisha Homes","Abhay",   "LQS","Inbound", "Proto",    "Running", 115,  90,  88,  70,    7),
    ("century_mirai_outbound",   "shriya@revspot.ai",     "Century",       "Bhoomika","LGS","Outbound","Standard", "Running",1895, 900, 888, 580,    4),
    ("century_winning",          "shriya@revspot.ai",     "Century",       "Bhoomika","LGS","Outbound","Bully",    "Running",1596, 690, 690, 410,   24),
    ("leverage_edu_outbound",    "rahul.soren@revspot.ai","Leverage Edu",  "Bhoomika","LGS","Outbound","Standard", "Running",2657,1174,1103, 870,   47),
    ("leverage_edu_inbound",     "rahul.soren@revspot.ai","Leverage Edu",  "Bhoomika","LQS","Inbound", "BPCL",     "Running", 207, 134, 130, 105,   13),
    ("assetz_inbound",           "vaibhav@revspot.ai",    "Assetz",        "Pooja",   "LQS","Inbound", "Proto",    "Running", 121,  56,  36,  28,    0),
    ("prestige_spring_heights",  "prathamesh@revspot.ai", "Prestige",      "Rohit",   "LQS","Inbound", "BPCL",     "Paused",  317, 241, 235, 220,    0),
    ("prestige_vaishnaoi",       "ritesh@revspot.ai",     "Prestige",      "Rohit",   "LQS","Inbound", "Standard", "Running", 280, 201, 195, 180,   18),
    ("godrej_bannerghatta",      "ritesh@revspot.ai",     "Godrej",        "Vikram",  "LGS","Outbound","Bully",    "Running", 286, 167, 150, 110,   28),
]
cols_a = ["Agent","Owner","Client","AM","Stack","Channel","Subtype","Bot Status","Dialled","Connected","Interacted","Completed","Qualified"]
agents_df = pd.DataFrame(AGENTS_RAW, columns=cols_a)

def derive_status(row):
    interacted = row["Interacted"]; qualified = row["Qualified"]
    iql = int(qualified * np.random.uniform(0.4,0.8))
    dql = int(interacted * np.random.uniform(0.10,0.20))
    fup = int(interacted * np.random.uniform(0.15,0.30))
    cfup = int(interacted * np.random.uniform(0.04,0.10))
    sql = int(qualified * np.random.uniform(0.35,0.65))
    return pd.Series([iql,dql,fup,cfup,sql])
agents_df[["IQL","DQL","Followup","Customer Followup","SQL"]] = agents_df.apply(derive_status, axis=1)

PRICE_PER_QL = {"Godrej":1200,"Kalpataru":1500,"Bhavisha Homes":900,"Century":1000,"Leverage Edu":600,"Assetz":1100,"Prestige":1400}
agents_df["Revenue (₹)"]  = agents_df.apply(lambda r: r["Qualified"] * PRICE_PER_QL.get(r["Client"],1000), axis=1)
agents_df["Cost (₹)"]     = (agents_df["Dialled"] * np.random.uniform(0.5,1.5,len(agents_df))).astype(int)
agents_df["Profit (₹)"]   = agents_df["Revenue (₹)"] - agents_df["Cost (₹)"]
agents_df["Avg Talk (s)"]    = np.random.randint(35,110,len(agents_df))
agents_df["Median Talk (s)"] = (agents_df["Avg Talk (s)"] * np.random.uniform(0.7,1.0,len(agents_df))).astype(int)
agents_df["Revisions"] = np.random.randint(1,8,len(agents_df))
agents_df["Requests"]  = np.random.randint(1,5,len(agents_df))

def pct(n,d): return round(n/d*100,1) if d else 0.0
agents_df["Connect %"]  = (agents_df["Connected"]  / agents_df["Dialled"]    * 100).round(1)
agents_df["Interact %"] = (agents_df["Interacted"] / agents_df["Connected"]  * 100).round(1)
agents_df["Complete %"] = (agents_df["Completed"]  / agents_df["Interacted"] * 100).round(1)
agents_df["Qualify %"]  = (agents_df["Qualified"]  / agents_df["Completed"]  * 100).round(1)
agents_df["SQL/QL %"]   = (agents_df["SQL"]        / agents_df["Qualified"].replace(0,np.nan) * 100).round(1).fillna(0)
agents_df["Health Qualify %"] = (agents_df["Qualified"] / agents_df["Dialled"] * 100).round(2)

def health_zone(qp, ch):
    if ch == "Inbound":
        if qp<5: return "Bad"
        if qp<10: return "Weak"
        if qp<15: return "OK"
        if qp<20: return "Good"
        return "Excellent"
    if qp<0.2: return "Bad"
    if qp<0.4: return "Weak"
    if qp<0.6: return "OK"
    if qp<0.8: return "Good"
    if qp<1.0: return "Very Good"
    return "Excellent"
agents_df["Health"] = agents_df.apply(lambda r: health_zone(r["Health Qualify %"], r["Channel"]), axis=1)


def paged_table(df_in: pd.DataFrame, key: str, page_size_default: int = 10):
    """Render a dataframe with page selector + page-size selector."""
    if df_in.empty:
        st.info("No rows.")
        return
    c1, c2, c3 = st.columns([1, 1, 4])
    page_size = c1.selectbox("Rows per page", [10, 25, 50, 100], index=[10,25,50,100].index(page_size_default), key=f"{key}_ps")
    total = len(df_in)
    n_pages = max(1, (total + page_size - 1) // page_size)
    page = c2.number_input(f"Page (1–{n_pages})", min_value=1, max_value=n_pages, value=1, step=1, key=f"{key}_pg")
    c3.caption(f"Showing {min((page-1)*page_size+1, total)}–{min(page*page_size, total)} of {total}")
    st.dataframe(df_in.iloc[(page-1)*page_size : page*page_size], use_container_width=True, hide_index=True)


# ─── PERSONA SWITCHER ─────────────────────────────────────────────────────────

st.markdown("## 📞 Call Analytics Dashboard")
st.markdown('<div class="proto-banner">⚠ PROTOTYPE — mock data for stakeholder review</div>', unsafe_allow_html=True)

persona = st.radio(
    "**View as**",
    ["🤖 Anunay (Bot Team Head)", "💼 Jitesh (Marketing Head)", "👑 Harsha & Darshan (Founders)"],
    horizontal=True,
)


# ─── SIDEBAR: persona-aware filters ───────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📅 Date Range")
    preset = st.selectbox("Preset", ["Last 1 day","Last 3 days","Last 7 days","Last 15 days","Last 30 days","All time","Custom"], index=2)
    if preset == "Custom":
        st.date_input("Range", value=(date.today()-timedelta(days=7), date.today()))

    st.markdown("---")
    st.markdown("### 🔍 Filters")
    sel_client = st.selectbox("Client", ["All"] + CLIENTS)

    df = agents_df.copy()
    if sel_client != "All": df = df[df["Client"] == sel_client]

    if persona.startswith("🤖"):
        st.markdown("**Bot Team filters**")
        sel_owner   = st.selectbox("Bot Owner", ["All"] + OWNERS)
        sel_stack   = st.selectbox("Bot Stack", ["All"] + STACKS, help="LGS = Lead Gen / LQS = Lead Qualification")
        sel_channel = st.selectbox("Channel", ["All"] + CHANNELS)
        sel_subtype = st.selectbox("Bot Subtype", ["All"] + SUBTYPES)
        sel_status  = st.selectbox("Bot Status", ["All","Running","Paused"])
        if sel_owner   != "All": df = df[df["Owner"]      == sel_owner]
        if sel_stack   != "All": df = df[df["Stack"]      == sel_stack]
        if sel_channel != "All": df = df[df["Channel"]    == sel_channel]
        if sel_subtype != "All": df = df[df["Subtype"]    == sel_subtype]
        if sel_status  != "All": df = df[df["Bot Status"] == sel_status]

    elif persona.startswith("💼"):
        st.markdown("**Marketing filters**")
        sel_am      = st.selectbox("Account Manager", ["All"] + AMs)
        sel_channel = st.selectbox("Channel", ["All"] + CHANNELS)
        if sel_am      != "All": df = df[df["AM"]      == sel_am]
        if sel_channel != "All": df = df[df["Channel"] == sel_channel]

    else:
        st.markdown("**Leadership filters**")
        sel_owner   = st.selectbox("Bot Owner", ["All"] + OWNERS)
        sel_am      = st.selectbox("Account Manager", ["All"] + AMs)
        if sel_owner != "All": df = df[df["Owner"] == sel_owner]
        if sel_am    != "All": df = df[df["AM"]    == sel_am]

    st.button("🔄 Refresh Data")


# ─── ANUNAY VIEW ──────────────────────────────────────────────────────────────

if persona.startswith("🤖"):
    st.markdown('<div class="persona-card">🤖 Anunay — Bot Team Head</div>', unsafe_allow_html=True)

    ud=int(df["Dialled"].sum()); uc=int(df["Connected"].sum()); ui=int(df["Interacted"].sum())
    ucp=int(df["Completed"].sum()); uq=int(df["Qualified"].sum())

    st.markdown('<p class="section-title">Volume</p>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Dialled", f"{ud:,}"); c2.metric("Connected", f"{uc:,}")
    c3.metric("Interacted", f"{ui:,}"); c4.metric("Completed", f"{ucp:,}"); c5.metric("Qualified", f"{uq:,}")

    st.markdown('<p class="section-title">Funnel Rates (lead-level)</p>', unsafe_allow_html=True)
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Connect %", f"{pct(uc,ud)}%"); r2.metric("Interact %", f"{pct(ui,uc)}%")
    r3.metric("Complete %", f"{pct(ucp,ui)}%"); r4.metric("Qualify %", f"{pct(uq,ucp)}%")

    funnel = pd.DataFrame({"Stage":["Dialled","Connected","Interacted","Completed","Qualified"],"Leads":[ud,uc,ui,ucp,uq]})
    st.altair_chart(alt.Chart(funnel).mark_bar().encode(
        y=alt.Y("Stage:N",sort=None,title=None), x="Leads:Q",
        color=alt.Color("Stage:N",legend=None,scale=alt.Scale(scheme="blues",reverse=True)),
        tooltip=["Stage","Leads"]).properties(height=220), use_container_width=True)

    st.markdown('<p class="section-title">Per-Bot Breakdown</p>', unsafe_allow_html=True)
    cols = ["Agent","Owner","Client","Stack","Channel","Subtype","Bot Status","Dialled","Connected","Interacted","Completed","Qualified","Connect %","Interact %","Complete %","Qualify %"]
    paged_table(df[cols], key="anunay_table")

    st.markdown('<p class="section-title">Drill-down</p>', unsafe_allow_html=True)
    sel_bot = st.selectbox("Pick a bot", ["—"] + df["Agent"].tolist())
    if sel_bot != "—":
        bot = df[df["Agent"]==sel_bot].iloc[0]
        h1,h2,h3,h4,h5 = st.columns(5)
        h1.markdown(f"**Bot:** `{sel_bot}`"); h2.markdown(f"**Stack:** {bot['Stack']}")
        h3.markdown(f"**Channel:** {bot['Channel']}"); h4.markdown(f"**Subtype:** {bot['Subtype']}"); h5.markdown(f"**Owner:** {bot['Owner']}")
        np.random.seed(hash(sel_bot)%1000)
        days = pd.date_range(end=date.today(), periods=14)
        trend = pd.DataFrame({"Date":days,
            "Connect %": np.clip(bot["Connect %"]+np.random.uniform(-8,8,14),0,100),
            "Interact %": np.clip(bot["Interact %"]+np.random.uniform(-8,8,14),0,100),
            "Complete %": np.clip(bot["Complete %"]+np.random.uniform(-8,8,14),0,100),
            "Qualify %": np.clip(bot["Qualify %"]+np.random.uniform(-3,3,14),0,100)})
        long = trend.melt("Date",var_name="Metric",value_name="Percentage")
        st.altair_chart(alt.Chart(long).mark_line(point=True,strokeWidth=2).encode(
            x="Date:T", y=alt.Y("Percentage:Q",scale=alt.Scale(domain=[0,100])),
            color="Metric:N", tooltip=["Date:T","Metric:N",alt.Tooltip("Percentage:Q",format=".1f")]
        ).properties(height=380), use_container_width=True)


# ─── JITESH VIEW ──────────────────────────────────────────────────────────────

elif persona.startswith("💼"):
    st.markdown('<div class="persona-card">💼 Jitesh — Marketing & Revenue</div>', unsafe_allow_html=True)

    ql=int(df["Qualified"].sum()); iql=int(df["IQL"].sum()); dql=int(df["DQL"].sum())
    fup=int(df["Followup"].sum()); cfup=int(df["Customer Followup"].sum()); sql=int(df["SQL"].sum())
    rev=int(df["Revenue (₹)"].sum()); cost=int(df["Cost (₹)"].sum())

    st.markdown('<p class="section-title">Lead Status</p>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Qualified", f"{ql:,}"); c2.metric("IQL", f"{iql:,}"); c3.metric("DQL", f"{dql:,}")
    c4.metric("Followup", f"{fup:,}"); c5.metric("Customer Followup", f"{cfup:,}")

    st.markdown('<p class="section-title">Revenue & SQL</p>', unsafe_allow_html=True)
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Total Revenue (₹)", f"₹{rev:,}")
    r2.metric("Total Cost (₹)", f"₹{cost:,}")
    r3.metric("Profit (₹)", f"₹{rev-cost:,}")
    r4.metric("SQL / QL %", f"{pct(sql,ql)}%")

    st.markdown('<p class="section-title">Avg Dials to Reach Stage — by Channel</p>', unsafe_allow_html=True)
    st.caption("Inbound bots reach qualified in few dials. Outbound bots cold-call so dial count to qualified is naturally higher (typical: 100+).")
    rows = []
    for ch in ["Inbound","Outbound"]:
        sub = df[df["Channel"]==ch]
        if sub.empty: continue
        d = sub["Dialled"].sum()
        for stage, num in [("First Connect","Connected"),("First Interact","Interacted"),("Completed","Completed"),("Qualified","Qualified")]:
            den = sub[num].sum()
            rows.append({"Stage": stage, "Channel": ch, "Avg Dials": round(d/max(den,1),2)})
    stages = pd.DataFrame(rows)
    st.altair_chart(alt.Chart(stages).mark_bar().encode(
        x=alt.X("Stage:N", sort=["First Connect","First Interact","Completed","Qualified"], title=None),
        y=alt.Y("Avg Dials:Q", title="Avg Dials Needed"),
        color=alt.Color("Channel:N", scale=alt.Scale(domain=["Inbound","Outbound"], range=["#4263eb","#f76707"])),
        column=alt.Column("Channel:N", title=None),
        tooltip=["Channel","Stage","Avg Dials"]).properties(height=240, width=300), use_container_width=False)

    st.markdown('<p class="section-title">Talk Time</p>', unsafe_allow_html=True)
    t1,t2 = st.columns(2)
    t1.metric("Avg Talk Time", f"{int(df['Avg Talk (s)'].mean())} s")
    t2.metric("Median Talk Time", f"{int(df['Median Talk (s)'].median())} s")
    total_calls = int(df["Dialled"].sum())
    buckets = pd.DataFrame({"Bucket":["0-10s","10-20s","20-30s","30-40s","40s+"],
        "Calls":[int(total_calls*p) for p in [0.18,0.14,0.12,0.10,0.46]]})
    st.altair_chart(alt.Chart(buckets).mark_bar().encode(
        x=alt.X("Bucket:N",sort=None), y="Calls:Q",
        color=alt.Color("Bucket:N",legend=None,scale=alt.Scale(scheme="purples")),
        tooltip=["Bucket","Calls"]).properties(height=220), use_container_width=True)

    st.markdown('<p class="section-title">Per-Bot Lead Status & Revenue</p>', unsafe_allow_html=True)
    cols = ["Agent","AM","Client","Channel","Qualified","IQL","DQL","Followup","Customer Followup","SQL","SQL/QL %","Revenue (₹)","Cost (₹)","Profit (₹)","Avg Talk (s)"]
    paged_table(df[cols].sort_values("Revenue (₹)",ascending=False), key="jitesh_table")


# ─── FOUNDERS VIEW ────────────────────────────────────────────────────────────

else:
    st.markdown('<div class="persona-card">👑 Harsha & Darshan — Founders / CEO</div>', unsafe_allow_html=True)

    rev=int(df["Revenue (₹)"].sum()); cost=int(df["Cost (₹)"].sum()); profit=rev-cost
    n_active = int((df["Bot Status"]=="Running").sum())
    st.markdown('<p class="section-title">Top KPIs</p>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Active Bots", n_active)
    c2.metric("Total Revenue (₹)", f"₹{rev:,}")
    c3.metric("Total Cost (₹)", f"₹{cost:,}")
    c4.metric("Profit (₹)", f"₹{profit:,}")

    st.markdown('<p class="section-title">Per Bot Owner</p>', unsafe_allow_html=True)
    summary = df.groupby("Owner").agg(**{
        "# Bots":("Agent","count"), "Active":("Bot Status",lambda s:(s=="Running").sum()),
        "Requests":("Requests","sum"), "Revisions":("Revisions","sum"),
        "Qualified":("Qualified","sum"), "Revenue (₹)":("Revenue (₹)","sum")
    }).reset_index().sort_values("Revenue (₹)",ascending=False)
    paged_table(summary, key="owner_summary")

    HEALTH_EMOJI = {"Bad":"🔴","Weak":"🟠","OK":"🟡","Good":"🟢","Very Good":"🟢","Excellent":"💚"}

    st.markdown('<p class="section-title">Bot Health — Inbound</p>', unsafe_allow_html=True)
    st.caption("Zone thresholds: 0–5 🔴 Bad · 5–10 🟠 Weak · 10–15 🟡 OK · 15–20 🟢 Good · 20+ 💚 Excellent")
    inb = df[df["Channel"]=="Inbound"][["Agent","Owner","Health Qualify %","Health"]].sort_values("Health Qualify %", ascending=False).rename(columns={"Health Qualify %": "Qualify %"})
    inb.insert(0, "", inb["Health"].map(HEALTH_EMOJI))
    paged_table(inb, key="health_inbound")

    st.markdown('<p class="section-title">Bot Health — Outbound</p>', unsafe_allow_html=True)
    st.caption("Zone thresholds: 0–0.2 🔴 Bad · 0.2–0.4 🟠 Weak · 0.4–0.6 🟡 OK · 0.6–0.8 🟢 Good · 0.8–1.0 🟢 Very Good · 1.0+ 💚 Excellent")
    out = df[df["Channel"]=="Outbound"][["Agent","Owner","Health Qualify %","Health"]].sort_values("Health Qualify %", ascending=False).rename(columns={"Health Qualify %": "Qualify %"})
    out.insert(0, "", out["Health"].map(HEALTH_EMOJI))
    paged_table(out, key="health_outbound")

    with st.expander("Health zone thresholds"):
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

    st.markdown('<p class="section-title">Top 5 / Bottom 5 — Today</p>', unsafe_allow_html=True)
    cA,cB = st.columns(2)
    cA.markdown("**🏆 Top 5**"); cA.dataframe(df.nlargest(5,"Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
    cB.markdown("**📉 Bottom 5**"); cB.dataframe(df.nsmallest(5,"Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)

    st.markdown('<p class="section-title">Top 5 / Bottom 5 — Per Owner</p>', unsafe_allow_html=True)
    sel_o = st.selectbox("Owner", OWNERS)
    sub = df[df["Owner"]==sel_o]
    if sub.empty:
        st.info("No bots for this owner under current filters.")
    else:
        cA,cB = st.columns(2)
        cA.markdown(f"**🏆 Top 5 — {sel_o}**"); cA.dataframe(sub.nlargest(5,"Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
        cB.markdown(f"**📉 Bottom 5 — {sel_o}**"); cB.dataframe(sub.nsmallest(5,"Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)


st.caption("Prototype • mock data • for stakeholder review")
