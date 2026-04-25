# Call Analytics Dashboard

## Files
- `prototype_mockup.py` — static prototype with sample data (for stakeholder review)
- `call_analytics_dashboard_v2.py` — live version (connects to MongoDB)
- `call_analytics_dashboard.py` — original v1

## Deploy prototype to Streamlit Cloud (free)

1. Push this folder to a **public** GitHub repo
2. Go to https://share.streamlit.io
3. Sign in with GitHub → **New app**
4. Repo: your repo • Branch: `main` • Main file: `prototype_mockup.py`
5. Click **Deploy** — get a public URL in ~2 min

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run prototype_mockup.py
```

## Live version (v2) — extra setup

Create `.env`:
```
MONGO_URI=mongodb+srv://...
```
Then `streamlit run call_analytics_dashboard_v2.py`.
For Streamlit Cloud, add `MONGO_URI` under app **Secrets** instead of `.env`.
