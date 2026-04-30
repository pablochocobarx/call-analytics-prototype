from pymongo import MongoClient
from datetime import datetime, date, timedelta
import streamlit as st
import pandas as pd


@st.cache_resource
def get_db():
    """Connect to MongoDB and return db object."""
    uri = "mongodb+srv://sourabh:ROnBLuF5pXxvyHTi@revvai-db-instance.w3amn8n.mongodb.net/"
    client = MongoClient(uri)
    return client["revv"]


@st.cache_data(ttl=300)
def load_agent_meta():
    """Fetch agent metadata from ai_agents collection.

    Returns:
        dict: {agent_identifier_str → {owner, template, status, project_name}}
    """
    db = get_db()
    agents = db["ai_agents"]

    result = {}
    for doc in agents.find(
        {},
        {"agent_identifier": 1, "owner": 1, "template": 1, "status": 1, "project_name": 1}
    ):
        agent_id = str(doc.get("agent_identifier", ""))
        if agent_id:
            result[agent_id] = {
                "owner": doc.get("owner"),
                "template": doc.get("template"),
                "status": "Running" if doc.get("status") == "Published" else "Paused",
                "project_name": doc.get("project_name")
            }

    return result


@st.cache_data(ttl=300)
def load_sequence_meta():
    """Fetch channel and status per agent_identifier from sequences (ai_call campaigns).

    A bot is Running if ANY of its sequences is running.
    A bot is Paused if ALL of its sequences are paused/completed.

    Returns:
        dict: {agent_identifier → {"channel": "Inbound"/"Outbound", "status": "Running"/"Paused"}}
    """
    db = get_db()

    # {agent_identifier → set of sequence statuses}
    ident_statuses: dict[str, set] = {}
    ident_channel: dict[str, str] = {}

    for doc in db["campaign"].find(
        {"channel": "ai_call"},
        {"channel_configuration.agent_identifier": 1, "type": 1, "status": 1}
    ):
        ident = (doc.get("channel_configuration") or {}).get("agent_identifier", "")
        ctype = doc.get("type", "")
        seq_status = doc.get("status", "")
        if not ident:
            continue

        # Channel — inbound wins if any sequence is inbound
        if ctype in ("inbound", "performance"):
            ident_channel[ident] = "Inbound"
        elif ctype == "outbound" and ident not in ident_channel:
            ident_channel[ident] = "Outbound"

        # Collect all sequence statuses for this bot
        ident_statuses.setdefault(ident, set()).add(seq_status)

    result = {}
    for ident, statuses in ident_statuses.items():
        # Running if any sequence is running
        bot_status = "Running" if "running" in statuses else "Paused"
        result[ident] = {
            "channel": ident_channel.get(ident, "—"),
            "status": bot_status
        }

    return result


def load_campaign_channel_map():
    """Compatibility wrapper — returns channel map only."""
    return {ident: meta["channel"] for ident, meta in load_sequence_meta().items()}


@st.cache_data(ttl=300)
def load_call_metrics(date_from_str: str, date_to_str: str):
    """Load aggregated call metrics per agent.

    Args:
        date_from_str: "YYYY-MM-DD" or "all"
        date_to_str: "YYYY-MM-DD"

    Returns:
        dict: {agent_identifier → metrics_dict}
    """
    db = get_db()
    call_log = db["call_log"]

    # Build date filter
    match_stage = {}
    if date_from_str != "all":
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
        # Extend to_date to end of day
        date_to = date_to.replace(hour=23, minute=59, second=59)
        match_stage["created_at"] = {
            "$gte": date_from,
            "$lte": date_to
        }

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "agent": "$agent_identifier",
                    "lead": "$lead_id"
                },
                "connected": {
                    "$max": {"$cond": [{"$eq": ["$status", "ended"]}, 1, 0]}
                },
                "interacted": {
                    "$max": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$status", "ended"]},
                                    {"$gte": ["$call_duration", 30]}
                                ]
                            },
                            1,
                            0
                        ]
                    }
                },
                "completed": {
                    "$max": {
                        "$cond": [
                            {"$eq": ["$report.call_status", "call_completed_normally"]},
                            1,
                            0
                        ]
                    }
                },
                "lead_status": {"$last": "$report_detailed.lead_status"},
                "total_cost": {"$sum": {"$ifNull": ["$call_cost", 0]}},
                "max_duration": {"$max": {"$ifNull": ["$call_duration", 0]}}
            }
        },
        {
            "$group": {
                "_id": "$_id.agent",
                "dialled": {"$sum": 1},
                "connected": {"$sum": "$connected"},
                "interacted": {"$sum": "$interacted"},
                "completed": {"$sum": "$completed"},
                "qualified": {
                    "$sum": {"$cond": [{"$eq": ["$lead_status", "Qualified"]}, 1, 0]}
                },
                "iql": {
                    "$sum": {"$cond": [{"$eq": ["$lead_status", "Intent Qualified"]}, 1, 0]}
                },
                "dql": {
                    "$sum": {"$cond": [{"$eq": ["$lead_status", "Disqualified"]}, 1, 0]}
                },
                "followup": {
                    "$sum": {"$cond": [{"$eq": ["$lead_status", "Follow up"]}, 1, 0]}
                },
                "cfu": {
                    "$sum": {"$cond": [{"$eq": ["$lead_status", "Customer Follow up"]}, 1, 0]}
                },
                "total_cost": {"$sum": "$total_cost"},
                "avg_duration": {"$avg": "$max_duration"},
                "durations": {"$push": "$max_duration"}
            }
        }
    ]

    def _median(durations: list) -> float:
        vals = sorted(d for d in durations if d is not None)
        n = len(vals)
        if n == 0:
            return 0.0
        mid = n // 2
        return vals[mid] if n % 2 == 1 else (vals[mid - 1] + vals[mid]) / 2

    result = {}
    for doc in call_log.aggregate(pipeline, allowDiskUse=True):
        agent_id = str(doc.get("_id", ""))
        if agent_id:
            result[agent_id] = {
                "dialled": doc.get("dialled", 0),
                "connected": doc.get("connected", 0),
                "interacted": doc.get("interacted", 0),
                "completed": doc.get("completed", 0),
                "qualified": doc.get("qualified", 0),
                "iql": doc.get("iql", 0),
                "dql": doc.get("dql", 0),
                "followup": doc.get("followup", 0),
                "cfu": doc.get("cfu", 0),
                "total_cost": doc.get("total_cost", 0),
                "avg_duration": doc.get("avg_duration", 0),
                "median_duration": _median(doc.get("durations", []))
            }

    return result


@st.cache_data(ttl=300)
def load_sql_counts(date_from_str: str, date_to_str: str):
    """Load SQL lead counts per agent.

    Join: campaign_lead.lead_id (sql=True) → call_log.lead_id → agent_identifier.
    campaign_lead.agent_identifier is NULL for 97% of SQL docs — can't use directly.

    Args:
        date_from_str: "YYYY-MM-DD" or "all"
        date_to_str: "YYYY-MM-DD"

    Returns:
        dict: {agent_identifier → sql_count}
    """
    db = get_db()

    # Step 1: get all SQL lead_ids (date filter on sql_marked_at)
    match_stage = {"sql": True, "lead_id": {"$ne": None}}
    if date_from_str != "all":
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
        date_to = date_to.replace(hour=23, minute=59, second=59)
        match_stage["sql_marked_at"] = {"$gte": date_from, "$lte": date_to}

    sql_lead_ids = [
        doc["lead_id"]
        for doc in db["campaign_lead"].find(match_stage, {"lead_id": 1})
    ]

    if not sql_lead_ids:
        return {}

    # Step 2: look up agent_identifier for those lead_ids in call_log
    pipeline = [
        {"$match": {"lead_id": {"$in": sql_lead_ids}}},
        {"$group": {
            "_id": {"agent": "$agent_identifier", "lead": "$lead_id"}
        }},
        {"$group": {
            "_id": "$_id.agent",
            "sql_count": {"$sum": 1}
        }}
    ]

    result = {}
    for doc in db["call_log"].aggregate(pipeline, allowDiskUse=True):
        agent_id = str(doc.get("_id", ""))
        if agent_id:
            result[agent_id] = doc.get("sql_count", 0)

    return result


def _load_sql_counts_old(date_from_str: str, date_to_str: str):
    """OLD broken implementation kept for reference.
    Bug: joined campaign_lead._id (ObjectId) against call_log.lead_id (UUID string) → always 0.
    """
    db = get_db()
    campaign_lead = db["campaign_lead"]
    call_log = db["call_log"]

    sql_lead_ids = []
    batch_size = 10000
    skip = 0

    while True:
        batch = list(campaign_lead.find(
            {"sql": True},
            {"_id": 1}
        ).skip(skip).limit(batch_size))

        if not batch:
            break

        sql_lead_ids.extend([doc["_id"] for doc in batch])
        skip += batch_size

    if not sql_lead_ids:
        return {}

    match_stage = {"lead_id": {"$in": sql_lead_ids}}
    if date_from_str != "all":
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
        date_to = date_to.replace(hour=23, minute=59, second=59)
        match_stage["created_at"] = {
            "$gte": date_from,
            "$lte": date_to
        }

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "agent": "$agent_identifier",
                    "lead": "$lead_id"
                }
            }
        },
        {
            "$group": {
                "_id": "$_id.agent",
                "sql_count": {"$sum": 1}
            }
        }
    ]

    result = {}
    for doc in call_log.aggregate(pipeline, allowDiskUse=True):
        agent_id = str(doc.get("_id", ""))
        if agent_id:
            result[agent_id] = doc.get("sql_count", 0)

    return result


@st.cache_data(ttl=300)
def load_daily_trend(agent_identifier: str, date_from_str: str, date_to_str: str):
    """Load daily trend metrics for a single agent.

    Args:
        agent_identifier: Agent identifier string
        date_from_str: "YYYY-MM-DD" or "all"
        date_to_str: "YYYY-MM-DD"

    Returns:
        list: Sorted list of daily metrics dicts
    """
    db = get_db()
    call_log = db["call_log"]

    # Build date filter
    match_stage = {"agent_identifier": agent_identifier}
    if date_from_str != "all":
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
        date_to = date_to.replace(hour=23, minute=59, second=59)
        match_stage["created_at"] = {
            "$gte": date_from,
            "$lte": date_to
        }

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "lead": "$lead_id"
                },
                "connected": {
                    "$max": {"$cond": [{"$eq": ["$status", "ended"]}, 1, 0]}
                },
                "interacted": {
                    "$max": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$status", "ended"]},
                                    {"$gte": ["$call_duration", 30]}
                                ]
                            },
                            1,
                            0
                        ]
                    }
                },
                "completed": {
                    "$max": {
                        "$cond": [
                            {"$eq": ["$report.call_status", "call_completed_normally"]},
                            1,
                            0
                        ]
                    }
                },
                "lead_status": {"$last": "$report_detailed.lead_status"}
            }
        },
        {
            "$group": {
                "_id": "$_id.date",
                "dialled": {"$sum": 1},
                "connected": {"$sum": "$connected"},
                "interacted": {"$sum": "$interacted"},
                "completed": {"$sum": "$completed"},
                "qualified": {
                    "$sum": {"$cond": [{"$eq": ["$lead_status", "Qualified"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"_id": 1}}
    ]

    result = []
    for doc in call_log.aggregate(pipeline, allowDiskUse=True):
        result.append({
            "date": doc.get("_id"),
            "dialled": doc.get("dialled", 0),
            "connected": doc.get("connected", 0),
            "interacted": doc.get("interacted", 0),
            "completed": doc.get("completed", 0),
            "qualified": doc.get("qualified", 0)
        })

    return result
