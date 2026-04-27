"""
Call Analytics Dashboard — V_NOW
Only metrics derivable from CURRENT DB schema (mock data shaped accordingly).
Excludes: Bot Stack, Bot Subtype, Bot Revisions, Bot Requests, Bot Owner (mostly).
SQL% included — sourced from campaign_lead.sql (boolean).
"""
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import date, timedelta

st.set_page_config(page_title="Call Analytics — Now", page_icon="📞", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background-color: #f7f9fc; border: 1px solid #e0e4ea;
        border-radius: 10px; padding: 14px 18px;
    }
    .section-title { font-size: 1.05rem; font-weight: 600; color: #333; margin-bottom: 0.5rem; }
    .scope-banner {
        background: #d1ecf1; border: 1px solid #17a2b8; padding: 8px 14px;
        border-radius: 6px; font-size: 0.85rem; color: #0c5460; margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ─── MOCK DATA — only fields derivable from current DB ────────────────────────
# Real DB sources noted in comments

OWNERS  = ["shriya@revspot.ai","rahul.soren@revspot.ai","vaibhav@revspot.ai"]  # ai_agents.owner (sparse, 13/214)
CLIENTS = ["godrej-blr","godrej-pune","sobha","assetz","bhavisha_homes","sumadhura","tvs"]  # campaign.client / call_log.client
CHANNELS = ["Inbound","Outbound"]  # campaign.type
AMs     = ["Vikram","Abhay","Pooja","Sakshi","Bhoomika","Rohit","Naina"]  # projects.json.account_manager_name

np.random.seed(42)

# (agent_id, owner, client, project, channel, am, status, dialled, connected, interacted, completed, qualified)
AGENTS_RAW = [
    ("godrej_aveline_sv",        "shriya@revspot.ai","godrej-blr",      "Aveline",         "Inbound", "Vikram",   "Running", 209, 140, 138,  92,   14),
    ("godrej_bannerghatta_bully", "",                "godrej-blr",      "Godrej Bannerghatta","Outbound","Vikram",  "Running", 286, 167, 150, 110,   28),
    ("godrej_ivara_outbound",    "rahul.soren@revspot.ai","godrej-pune","Ivara",           "Outbound","Vikram",   "Running",4867,1881,1721,1140,   14),
    ("godrej_reserve_sv",        "rahul.soren@revspot.ai","godrej-mmr","Reserve",         "Inbound", "Vikram",   "Running",1113, 376, 243, 168,    3),
    ("sobha_aranya_outbound",    "",                "sobha",           "Aranya",          "Outbound","Abhay",    "Running",2657,1174,1103, 870,   47),
    ("sobha_inizio_inbound",     "",                "sobha",           "Inizio",          "Inbound", "Abhay",    "Running", 207, 134, 130, 105,   13),
    ("sobha_elysia_outbound",    "",                "sobha",           "Elysia",          "Outbound","Abhay",    "Running",1895, 900, 888, 580,    4),
    ("sobha_altus_outbound",     "",                "sobha",           "Altus",           "Outbound","Abhay",    "Running",1596, 690, 690, 410,   24),
    ("assetz_inbound_2_props",   "vaibhav@revspot.ai","assetz",        "Assetz Meru & Meadow","Inbound","Pooja", "Running", 121,  56,  36,  28,    0),
    ("assetz_zen_sato_outbound", "",                "assetz",          "Assetz Zen & Sato","Outbound","Pooja",   "Paused",  363, 258, 233, 210,   33),
    ("bhavisha_zurich_outbound", "",                "bhavisha_homes",  "Zurich II",       "Outbound","Abhay",    "Running",2996,1289,1146, 880,   16),
    ("bhavisha_bilva_inbound",   "",                "bhavisha_homes",  "Bilva II",        "Inbound", "Abhay",    "Running", 115,  90,  88,  70,    7),
    ("sumadhura_panorama",       "",                "sumadhura",       "Sumadhura Panorama","Outbound","Pooja",  "Running", 944, 331, 190, 122,    5),
    ("tvs_cascadia",             "",                "tvs",             "Cascadia",        "Outbound","Sakshi",   "Running",6892,5191,4368,3850,   24),
]
cols = ["Agent","Owner","Client","Project","Channel","AM","Bot Status","Dialled","Connected","Interacted","Completed","Qualified"]
agents_df = pd.DataFrame(AGENTS_RAW, columns=cols)

# Lead status breakdown — DERIVABLE from report_detailed.lead_status enum
def derive_status(row):
    interacted = row["Interacted"]; qualified = row["Qualified"]
    iql = int(qualified * np.random.uniform(0.4,0.8))
    dql = int(interacted * np.random.uniform(0.10,0.20))
    fup = int(interacted * np.random.uniform(0.15,0.30))
    cfup = int(interacted * np.random.uniform(0.04,0.10))
    sql = int(qualified * np.random.uniform(0.35,0.65))  # campaign_lead.sql=true joined by lead_id
    return pd.Series([iql,dql,fup,cfup,sql])
agents_df[["IQL","DQL","Followup","Customer Followup","SQL"]] = agents_df.apply(derive_status, axis=1)
agents_df["SQL/QL %"] = (agents_df["SQL"] / agents_df["Qualified"].replace(0,np.nan) * 100).round(1).fillna(0)

# Revenue — DERIVABLE from projects.json (3 pricing models)
PRICING = {
    "Aveline":(45000,"site_visit"),"Godrej Bannerghatta":(25000,"site_visit"),
    "Ivara":(7500,"ql"),"Reserve":(12494,"ql"),
    "Aranya":(3600,"ql"),"Inizio":(3500,"ql"),"Elysia":(3500,"ql"),"Altus":(3800,"ql"),
    "Assetz Meru & Meadow":(8750,"budget"),"Assetz Zen & Sato":(8750,"ql"),
    "Bilva II":(1120,"budget"),"Zurich II":(1120,"budget"),
    "Sumadhura Panorama":(27500,"site_visit"),"Cascadia":(18000,"ql"),
}
agents_df["Rate (₹)"] = agents_df["Project"].map(lambda p: PRICING.get(p,(1000,"ql"))[0])
agents_df["Pricing Model"] = agents_df["Project"].map(lambda p: PRICING.get(p,(1000,"ql"))[1])
agents_df["Revenue (₹)"] = agents_df["Qualified"] * agents_df["Rate (₹)"]

# Talk time — DERIVABLE from call_log.call_duration
agents_df["Avg Talk (s)"]    = np.random.randint(35,110,len(agents_df))
agents_df["Median Talk (s)"] = (agents_df["Avg Talk (s)"] * np.random.uniform(0.7,1.0,len(agents_df))).astype(int)

# Funnel rates
def pct(n,d): return round(n/d*100,1) if d else 0.0
agents_df["Connect %"]  = (agents_df["Connected"]  / agents_df["Dialled"]    * 100).round(1)
agents_df["Interact %"] = (agents_df["Interacted"] / agents_df["Connected"]  * 100).round(1)
agents_df["Complete %"] = (agents_df["Completed"]  / agents_df["Interacted"] * 100).round(1)
agents_df["Qualify %"]  = (agents_df["Qualified"]  / agents_df["Completed"]  * 100).round(1)

# Health zone (qualify% of dialled)
agents_df["Health Qualify %"] = (agents_df["Qualified"] / agents_df["Dialled"] * 100).round(2)
def health(qp, ch):
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
agents_df["Health"] = agents_df.apply(lambda r: health(r["Health Qualify %"], r["Channel"]), axis=1)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📅 Date Range")
    preset = st.selectbox("Preset", ["Last 1 day","Last 3 days","Last 7 days","Last 15 days","Last 30 days","All time","Custom"], index=2)
    if preset == "Custom":
        st.date_input("Range", value=(date.today()-timedelta(days=7), date.today()))
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    sel_client = st.selectbox("Client", ["All"] + CLIENTS)
    sel_proj   = st.selectbox("Project", ["All"] + sorted(agents_df["Project"].unique().tolist()))
    sel_owner  = st.selectbox("Bot Owner ⚠ sparse", ["All"] + OWNERS)
    sel_am     = st.selectbox("Account Manager", ["All"] + AMs)
    sel_chan   = st.selectbox("Channel", ["All"] + CHANNELS)
    sel_status = st.selectbox("Bot Status", ["All","Running","Paused"])

    df = agents_df.copy()
    if sel_client != "All": df = df[df["Client"]    == sel_client]
    if sel_proj   != "All": df = df[df["Project"]   == sel_proj]
    if sel_owner  != "All": df = df[df["Owner"]     == sel_owner]
    if sel_am     != "All": df = df[df["AM"]        == sel_am]
    if sel_chan   != "All": df = df[df["Channel"]   == sel_chan]
    if sel_status != "All": df = df[df["Bot Status"]== sel_status]

    st.button("🔄 Refresh Data")


# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("## 📞 Call Analytics — V_NOW")
st.markdown('<div class="scope-banner">ℹ️ <b>V_NOW scope</b> — only metrics derivable from current DB schema. Excludes: Bot Stack (LGS/LQS), Bot Subtype (BPCL/Bully/Proto), Bot Revisions, Bot Requests, dense Bot Owner data.</div>', unsafe_allow_html=True)


# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab_o, tab_b, tab_m, tab_l = st.tabs(["📊 Overview","🤖 Bot Performance","💼 Marketing & Revenue","👑 Leadership"])


# OVERVIEW
with tab_o:
    ud = int(df["Dialled"].sum()); uc=int(df["Connected"].sum())
    ui = int(df["Interacted"].sum()); ucp=int(df["Completed"].sum()); uq=int(df["Qualified"].sum())
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Unique Dialled", f"{ud:,}"); c2.metric("Connected", f"{uc:,}")
    c3.metric("Interacted", f"{ui:,}"); c4.metric("Completed", f"{ucp:,}"); c5.metric("Qualified", f"{uq:,}")
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Connect %", f"{pct(uc,ud)}%"); r2.metric("Interact %", f"{pct(ui,uc)}%")
    r3.metric("Complete %", f"{pct(ucp,ui)}%"); r4.metric("Qualify %", f"{pct(uq,ucp)}%")
    funnel = pd.DataFrame({"Stage":["Dialled","Connected","Interacted","Completed","Qualified"],"Leads":[ud,uc,ui,ucp,uq]})
    st.altair_chart(alt.Chart(funnel).mark_bar().encode(
        y=alt.Y("Stage:N",sort=None,title=None), x="Leads:Q",
        color=alt.Color("Stage:N",legend=None,scale=alt.Scale(scheme="blues",reverse=True)),
        tooltip=["Stage","Leads"]).properties(height=220), use_container_width=True)


# BOT PERF — Anunay (no Stack/Subtype filters here)
with tab_b:
    st.markdown("### 🤖 Bot Performance")
    st.caption("⚠ Stack (LGS/LQS) & Subtype (BPCL/Bully/Proto) filters NOT available — DB fields missing.")
    cols_show = ["Agent","Owner","Client","Project","Channel","AM","Bot Status","Dialled","Connected","Interacted","Completed","Qualified","Connect %","Interact %","Complete %","Qualify %"]
    st.dataframe(df[cols_show], use_container_width=True, hide_index=True)

    st.markdown("---")
    sel_bot = st.selectbox("Drill-down", ["—"] + df["Agent"].tolist())
    if sel_bot != "—":
        bot = df[df["Agent"]==sel_bot].iloc[0]
        h1,h2,h3,h4 = st.columns(4)
        h1.markdown(f"**Bot:** `{sel_bot}`"); h2.markdown(f"**Project:** {bot['Project']}")
        h3.markdown(f"**Channel:** {bot['Channel']}"); h4.markdown(f"**Owner:** {bot['Owner'] or '—'}")
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


# MARKETING — Jitesh (no SQL%)
with tab_m:
    st.markdown("### 💼 Marketing & Revenue")
    ql=int(df["Qualified"].sum()); iql=int(df["IQL"].sum()); dql=int(df["DQL"].sum())
    fup=int(df["Followup"].sum()); cfup=int(df["Customer Followup"].sum())
    sql=int(df["SQL"].sum()); rev=int(df["Revenue (₹)"].sum())

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Qualified", f"{ql:,}"); c2.metric("IQL", f"{iql:,}"); c3.metric("DQL", f"{dql:,}")
    c4.metric("Followup", f"{fup:,}"); c5.metric("Customer Followup", f"{cfup:,}")

    r1,r2,r3 = st.columns(3)
    r1.metric("Total Revenue (₹)", f"₹{rev:,}", help="From projects.json — handles ql/site_visit/budget pricing models")
    r2.metric("SQL / QL %", f"{pct(sql,ql)}%", help="From campaign_lead.sql — joined by lead_id")
    r3.metric("Avg Revenue / Bot", f"₹{int(rev/max(len(df),1)):,}")

    st.markdown('<p class="section-title">Avg Dials to Reach Stage</p>', unsafe_allow_html=True)
    stages = pd.DataFrame({"Stage":["First Connect","First Interact","Completed","Qualified"],
        "Avg Dials":[
            round(df["Dialled"].sum()/max(df["Connected"].sum(),1),2),
            round(df["Dialled"].sum()/max(df["Interacted"].sum(),1),2),
            round(df["Dialled"].sum()/max(df["Completed"].sum(),1),2),
            round(df["Dialled"].sum()/max(df["Qualified"].sum(),1),2)]})
    st.altair_chart(alt.Chart(stages).mark_bar().encode(
        x=alt.X("Stage:N",sort=None), y="Avg Dials:Q",
        color=alt.Color("Stage:N",legend=None,scale=alt.Scale(scheme="oranges")),
        tooltip=["Stage","Avg Dials"]).properties(height=240), use_container_width=True)

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
    cols_show = ["Agent","AM","Project","Pricing Model","Qualified","IQL","DQL","Followup","Customer Followup","SQL","SQL/QL %","Rate (₹)","Revenue (₹)","Avg Talk (s)"]
    st.dataframe(df[cols_show].sort_values("Revenue (₹)",ascending=False), use_container_width=True, hide_index=True)


# LEADERSHIP — Founders (no Requests/Revisions)
with tab_l:
    st.markdown("### 👑 Leadership")
    st.caption("⚠ Bot Requests & Revisions NOT available — versioning collection (`agent_versions`) empty; bot-request workflow doesn't exist yet.")

    st.markdown('<p class="section-title">Per Owner — Activity (sparse, only 13/214 agents have owner set)</p>', unsafe_allow_html=True)
    summary = df[df["Owner"]!=""].groupby("Owner").agg(**{
        "# Bots":("Agent","count"), "Active":("Bot Status",lambda s:(s=="Running").sum()),
        "Qualified":("Qualified","sum"), "Revenue (₹)":("Revenue (₹)","sum")
    }).reset_index().sort_values("Revenue (₹)",ascending=False)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown('<p class="section-title">Per AM — Activity (clean from projects.json)</p>', unsafe_allow_html=True)
    am_summary = df.groupby("AM").agg(**{
        "# Bots":("Agent","count"), "Active":("Bot Status",lambda s:(s=="Running").sum()),
        "Qualified":("Qualified","sum"), "Revenue (₹)":("Revenue (₹)","sum")
    }).reset_index().sort_values("Revenue (₹)",ascending=False)
    st.dataframe(am_summary, use_container_width=True, hide_index=True)

    st.markdown('<p class="section-title">Bot Health Zones</p>', unsafe_allow_html=True)
    chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("Agent:N",sort="-x",title=None), x=alt.X("Health Qualify %:Q", title="Qualified % of Dialled"),
        color=alt.Color("Health:N", scale=alt.Scale(domain=["Bad","Weak","OK","Good","Very Good","Excellent"],
            range=["#d9534f","#f0ad4e","#ffc107","#5cb85c","#28a745","#1e7e34"])),
        tooltip=["Agent","Channel","Health Qualify %","Health"]).properties(height=max(300,24*len(df)))
    st.altair_chart(chart, use_container_width=True)

    st.markdown('<p class="section-title">Top 5 / Bottom 5 Today</p>', unsafe_allow_html=True)
    cA,cB = st.columns(2)
    cA.markdown("**🏆 Top 5**"); cA.dataframe(df.nlargest(5,"Qualify %")[["Agent","AM","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)
    cB.markdown("**📉 Bottom 5**"); cB.dataframe(df.nsmallest(5,"Qualify %")[["Agent","AM","Channel","Qualified","Qualify %"]], use_container_width=True, hide_index=True)


st.caption("V_NOW • mock data shaped to current DB schema only • prototype for stakeholder review")
