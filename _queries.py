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
def load_campaign_channel_map():
    """Fetch campaign to channel mapping.

    Returns:
        dict: {agent_id_as_str → "inbound"/"outbound"}
    """
    db = get_db()
    campaigns = db["campaign"]

    result = {}
    for doc in campaigns.find({}, {"ai_agent": 1, "type": 1}):
        ai_agent = doc.get("ai_agent")
        if ai_agent:
            agent_id = str(ai_agent)
            channel = doc.get("type", "unknown")
            result[agent_id] = channel

    return result


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
                "avg_duration": {"$avg": "$max_duration"}
            }
        }
    ]

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
                "avg_duration": doc.get("avg_duration", 0)
            }

    return result


@st.cache_data(ttl=300)
def load_sql_counts(date_from_str: str, date_to_str: str):
    """Load SQL lead counts per agent.

    Args:
        date_from_str: "YYYY-MM-DD" or "all"
        date_to_str: "YYYY-MM-DD"

    Returns:
        dict: {agent_identifier → sql_count}
    """
    db = get_db()
    campaign_lead = db["campaign_lead"]
    call_log = db["call_log"]

    # Fetch all SQL lead IDs in batches
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

    # Build date filter for call_log
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
