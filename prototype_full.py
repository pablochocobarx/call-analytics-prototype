"""
Call Analytics Dashboard — V_FULL with Persona Switcher
3 personas, each sees only their own filters + metrics.
"""
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import date, timedelta

st.set_page_config(page_title="Call Analytics", page_icon="📞", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }
    h1, h2, h3 { letter-spacing: -0.01em; }
    .stRadio > label { font-weight: 600; }
    /* tighten metric card spacing in dark theme too */
    [data-testid="stMetric"] { padding: 4px 0; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; opacity: 0.7; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; }
    .proto-banner {
        background: rgba(255,193,7,0.12); border-left: 3px solid #ffc107;
        padding: 8px 14px; border-radius: 4px; font-size: 0.82rem;
        margin: 6px 0 14px;
    }
    .small-caption { font-size: 0.78rem; opacity: 0.65; margin-top: -8px; }
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

def fmt_inr(n: int) -> str:
    """Indian number format: 12.5L, 1.2Cr."""
    n = int(n)
    if abs(n) >= 1_00_00_000: return f"₹{n/1_00_00_000:.2f} Cr"
    if abs(n) >= 1_00_000:    return f"₹{n/1_00_000:.2f} L"
    if abs(n) >= 1_000:       return f"₹{n/1_000:.1f}K"
    return f"₹{n}"

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
HEALTH_EMOJI = {"Bad":"🔴","Weak":"🟠","OK":"🟡","Good":"🟢","Very Good":"🟢","Excellent":"💚"}


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
    st.dataframe(df_in.iloc[(page-1)*page_size : page*page_size], use_container_width=True, hide_index=True)


# ─── HEADER + PERSONA SWITCHER ────────────────────────────────────────────────

st.markdown("# 📞 Call Analytics")
st.markdown('<div class="proto-banner">⚠ Prototype • mock data • for stakeholder review</div>', unsafe_allow_html=True)

persona = st.radio(
    "View as",
    ["🤖 Anunay — Bot Team", "💼 Jitesh — Marketing", "👑 Harsha & Darshan — Founders"],
    horizontal=True, label_visibility="collapsed",
)
st.divider()


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Filters")
    preset = st.selectbox("Date range", ["Last 1 day","Last 3 days","Last 7 days","Last 15 days","Last 30 days","All time","Custom"], index=2)
    if preset == "Custom":
        st.date_input("Range", value=(date.today()-timedelta(days=7), date.today()), label_visibility="collapsed")

    sel_client = st.selectbox("Client", ["All"] + CLIENTS)

    df = agents_df.copy()
    if sel_client != "All": df = df[df["Client"] == sel_client]

    if persona.startswith("🤖"):
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
        sel_am      = st.selectbox("Account Manager", ["All"] + AMs)
        sel_channel = st.selectbox("Channel", ["All"] + CHANNELS)
        if sel_am      != "All": df = df[df["AM"]      == sel_am]
        if sel_channel != "All": df = df[df["Channel"] == sel_channel]

    else:
        sel_owner   = st.selectbox("Bot Owner", ["All"] + OWNERS)
        sel_am      = st.selectbox("Account Manager", ["All"] + AMs)
        if sel_owner != "All": df = df[df["Owner"] == sel_owner]
        if sel_am    != "All": df = df[df["AM"]    == sel_am]



# ─── ANUNAY ───────────────────────────────────────────────────────────────────

if persona.startswith("🤖"):
    st.markdown("### Bot Team Performance")

    ud=int(df["Dialled"].sum()); uc=int(df["Connected"].sum()); ui=int(df["Interacted"].sum())
    ucp=int(df["Completed"].sum()); uq=int(df["Qualified"].sum())

    # KPIs — 4 funnel rates (volume in table below, not duplicated here)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Connect %",  f"{pct(uc,ud)}%")
    c2.metric("Interact %", f"{pct(ui,uc)}%")
    c3.metric("Complete %", f"{pct(ucp,ui)}%")
    c4.metric("Qualify %",  f"{pct(uq,ucp)}%")

    # Funnel chart
    funnel = pd.DataFrame({"Stage":["Dialled","Connected","Interacted","Completed","Qualified"],"Leads":[ud,uc,ui,ucp,uq]})
    st.altair_chart(alt.Chart(funnel).mark_bar(cornerRadius=3).encode(
        y=alt.Y("Stage:N", sort=None, title=None),
        x=alt.X("Leads:Q", title=None),
        color=alt.Color("Stage:N", legend=None, scale=alt.Scale(scheme="blues", reverse=True)),
        tooltip=["Stage","Leads"]).properties(height=180), use_container_width=True)

    st.divider()

    # Per-bot table
    st.markdown("#### Per-bot breakdown")
    cols = ["Agent","Owner","Client","Stack","Channel","Subtype","Bot Status","Connect %","Interact %","Complete %","Qualify %","Dialled","Qualified"]
    paged_table(df[cols].sort_values("Qualify %", ascending=False), key="anunay_table")

    st.divider()

    # Drill-down
    st.markdown("#### Drill-down")
    sel_bot = st.selectbox("Pick a bot", ["—"] + df["Agent"].tolist(), label_visibility="collapsed")
    if sel_bot != "—":
        bot = df[df["Agent"]==sel_bot].iloc[0]
        st.caption(f"Stack: **{bot['Stack']}**  •  Channel: **{bot['Channel']}**  •  Subtype: **{bot['Subtype']}**  •  Owner: **{bot['Owner']}**  •  Status: **{bot['Bot Status']}**")

        np.random.seed(hash(sel_bot)%1000)
        days = pd.date_range(end=date.today(), periods=14)
        trend = pd.DataFrame({"Date":days,
            "Connect %": np.clip(bot["Connect %"]+np.random.uniform(-8,8,14),0,100),
            "Interact %": np.clip(bot["Interact %"]+np.random.uniform(-8,8,14),0,100),
            "Complete %": np.clip(bot["Complete %"]+np.random.uniform(-8,8,14),0,100),
            "Qualify %": np.clip(bot["Qualify %"]+np.random.uniform(-3,3,14),0,100)})
        long = trend.melt("Date",var_name="Metric",value_name="Percentage")
        st.altair_chart(alt.Chart(long).mark_line(point=True,strokeWidth=2.5).encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Percentage:Q", scale=alt.Scale(domain=[0,100]), title="%"),
            color=alt.Color("Metric:N", legend=alt.Legend(orient="top", title=None)),
            tooltip=["Date:T","Metric:N",alt.Tooltip("Percentage:Q",format=".1f")]
        ).properties(height=340), use_container_width=True)


# ─── JITESH ───────────────────────────────────────────────────────────────────

elif persona.startswith("💼"):
    st.markdown("### Marketing & Revenue")

    ql=int(df["Qualified"].sum()); iql=int(df["IQL"].sum()); dql=int(df["DQL"].sum())
    fup=int(df["Followup"].sum()); cfup=int(df["Customer Followup"].sum()); sql=int(df["SQL"].sum())
    rev=int(df["Revenue (₹)"].sum()); cost=int(df["Cost (₹)"].sum())

    # Hero — revenue
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Revenue", fmt_inr(rev))
    c2.metric("Cost",    fmt_inr(cost))
    c3.metric("Profit",  fmt_inr(rev-cost))
    c4.metric("SQL / QL %", f"{pct(sql,ql)}%")

    # Secondary — leads
    st.markdown("<div class='small-caption'>Lead status</div>", unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Qualified", f"{ql:,}")
    c2.metric("IQL", f"{iql:,}")
    c3.metric("DQL", f"{dql:,}")
    c4.metric("Followup", f"{fup:,}")
    c5.metric("Customer FU", f"{cfup:,}")

    st.divider()

    # Avg dials by channel
    st.markdown("#### Avg dials to reach stage")
    st.markdown('<div class="small-caption">Inbound qualifies in few dials. Outbound cold-calls so qualifies need 100+ dials.</div>', unsafe_allow_html=True)
    rows = []
    for ch in ["Inbound","Outbound"]:
        sub = df[df["Channel"]==ch]
        if sub.empty: continue
        d = sub["Dialled"].sum()
        for stage, num in [("Connect","Connected"),("Interact","Interacted"),("Complete","Completed"),("Qualify","Qualified")]:
            den = sub[num].sum()
            rows.append({"Stage": stage, "Channel": ch, "Avg Dials": round(d/max(den,1),2)})
    stages = pd.DataFrame(rows)
    st.altair_chart(alt.Chart(stages).mark_bar(cornerRadius=3).encode(
        x=alt.X("Stage:N", sort=["Connect","Interact","Complete","Qualify"], title=None),
        y=alt.Y("Avg Dials:Q", title="Avg dials"),
        color=alt.Color("Channel:N", scale=alt.Scale(domain=["Inbound","Outbound"], range=["#4263eb","#f76707"])),
        column=alt.Column("Channel:N", title=None, header=alt.Header(labelFontSize=13, labelFontWeight="bold")),
        tooltip=["Channel","Stage","Avg Dials"]).properties(height=220, width=280), use_container_width=False)

    st.divider()

    # Talk time
    st.markdown("#### Talk time")
    c1,c2 = st.columns(2)
    c1.metric("Avg",    f"{int(df['Avg Talk (s)'].mean())} s")
    c2.metric("Median", f"{int(df['Median Talk (s)'].median())} s")
    total_calls = int(df["Dialled"].sum())
    buckets = pd.DataFrame({"Bucket":["0-10s","10-20s","20-30s","30-40s","40s+"],
        "Calls":[int(total_calls*p) for p in [0.18,0.14,0.12,0.10,0.46]]})
    st.altair_chart(alt.Chart(buckets).mark_bar(cornerRadius=3).encode(
        x=alt.X("Bucket:N", sort=None, title=None),
        y=alt.Y("Calls:Q", title=None),
        color=alt.Color("Bucket:N", legend=None, scale=alt.Scale(scheme="purples")),
        tooltip=["Bucket","Calls"]).properties(height=220), use_container_width=True)

    st.divider()

    # Per-bot table
    st.markdown("#### Per-bot lead status & revenue")
    df_disp = df.copy()
    df_disp["Revenue"] = df_disp["Revenue (₹)"].map(fmt_inr)
    df_disp["Cost"]    = df_disp["Cost (₹)"].map(fmt_inr)
    df_disp["Profit"]  = df_disp["Profit (₹)"].map(fmt_inr)
    cols = ["Agent","AM","Client","Channel","Qualified","IQL","DQL","SQL","SQL/QL %","Revenue","Cost","Profit","Avg Talk (s)"]
    paged_table(df_disp[cols].sort_values("Qualified",ascending=False), key="jitesh_table")


# ─── FOUNDERS ─────────────────────────────────────────────────────────────────

else:
    st.markdown("### Leadership")

    rev=int(df["Revenue (₹)"].sum()); cost=int(df["Cost (₹)"].sum()); profit=rev-cost
    n_active = int((df["Bot Status"]=="Running").sum()); n_total = len(df)
    total_qual = int(df["Qualified"].sum())

    # Hero
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Active bots", f"{n_active} / {n_total}")
    c2.metric("Revenue", fmt_inr(rev))
    c3.metric("Profit",  fmt_inr(profit))
    c4.metric("Total qualified", f"{total_qual:,}")

    st.divider()

    # Owner roll-up
    st.markdown("#### Per bot owner")
    summary = df.groupby("Owner").agg(**{
        "# Bots":("Agent","count"), "Active":("Bot Status",lambda s:(s=="Running").sum()),
        "Requests":("Requests","sum"), "Revisions":("Revisions","sum"),
        "Qualified":("Qualified","sum"), "Revenue":("Revenue (₹)","sum")
    }).reset_index().sort_values("Revenue", ascending=False)
    summary["Revenue"] = summary["Revenue"].map(fmt_inr)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.divider()

    # Top / Bottom
    st.markdown("#### Top & bottom performers (today)")
    cA,cB = st.columns(2)
    with cA:
        st.markdown("**🏆 Top 5**")
        st.dataframe(df.nlargest(5,"Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
    with cB:
        st.markdown("**📉 Bottom 5**")
        st.dataframe(df.nsmallest(5,"Qualify %")[["Agent","Owner","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)

    st.markdown("**Per owner**")
    sel_o = st.selectbox("Owner", OWNERS, label_visibility="collapsed")
    sub = df[df["Owner"]==sel_o]
    if sub.empty:
        st.info("No bots for this owner under current filters.")
    else:
        cA,cB = st.columns(2)
        with cA:
            st.markdown("**🏆 Top 5**")
            st.dataframe(sub.nlargest(5,"Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
        with cB:
            st.markdown("**📉 Bottom 5**")
            st.dataframe(sub.nsmallest(5,"Qualify %")[["Agent","Client","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)

    st.divider()

    # Health
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

    st.markdown("**Inbound**")
    inb = df[df["Channel"]=="Inbound"][["Agent","Owner","Health Qualify %","Health"]].sort_values("Health Qualify %", ascending=False).rename(columns={"Health Qualify %": "Qualify %"})
    inb["Health"] = inb["Health"].map(lambda h: f"{HEALTH_EMOJI.get(h,'')} {h}")
    paged_table(inb, key="health_inbound")

    st.markdown("**Outbound**")
    out = df[df["Channel"]=="Outbound"][["Agent","Owner","Health Qualify %","Health"]].sort_values("Health Qualify %", ascending=False).rename(columns={"Health Qualify %": "Qualify %"})
    out["Health"] = out["Health"].map(lambda h: f"{HEALTH_EMOJI.get(h,'')} {h}")
    paged_table(out, key="health_outbound")
