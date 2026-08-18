import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


st.set_page_config(page_title="Game Economy Ops", layout="wide")
st.title("Game Economy Ops")


def get_json(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


with st.sidebar:
    st.caption(API_BASE_URL)
    if st.button("Seed demo economy", use_container_width=True):
        response = requests.post(f"{API_BASE_URL}/seed", json={"players": 500, "days": 21, "reset": True}, timeout=30)
        response.raise_for_status()
        st.success("Demo economy seeded")

try:
    economy = get_json("/metrics/economy")
    resources = pd.DataFrame(get_json("/metrics/resources"))
    suspicious = pd.DataFrame(get_json("/players/suspicious?limit=30"))
    alerts = pd.DataFrame(get_json("/market/alerts"))
except Exception as exc:
    st.error(f"API unavailable: {exc}")
    st.stop()

metric_cols = st.columns(6)
metric_cols[0].metric("Net money supply", f"{economy['net_money_supply']:,.0f}")
metric_cols[1].metric("Generated", f"{economy['total_currency_generated']:,.0f}")
metric_cols[2].metric("Sunk", f"{economy['total_currency_sunk']:,.0f}")
metric_cols[3].metric("Velocity", f"{economy['marketplace_velocity']:.2f}")
metric_cols[4].metric("Wealth Gini", f"{economy['wealth_gini']:.2f}")
metric_cols[5].metric("7d inflation", f"{economy['inflation_7d']:.1%}")

alert_tab, bot_tab, resource_tab = st.tabs(["Market Alerts", "Bot Predictor", "Resource Balance"])

with alert_tab:
    if alerts.empty:
        st.info("No market alerts in the current analysis window.")
    else:
        st.dataframe(alerts, use_container_width=True, hide_index=True)

with bot_tab:
    if suspicious.empty:
        st.info("No player events available yet.")
    else:
        left, right = st.columns([0.62, 0.38])
        with left:
            fig = px.scatter(
                suspicious,
                x="gold_generated",
                y="trades",
                color="bot_risk_score",
                hover_data=["username", "segment", "flags"],
                color_continuous_scale="Reds",
                title="Risk by Gold Generation and Trade Activity",
            )
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.dataframe(
                suspicious[["player_id", "username", "segment", "bot_risk_score", "flags"]],
                use_container_width=True,
                hide_index=True,
            )

with resource_tab:
    if resources.empty:
        st.info("No resource data available yet.")
    else:
        melted = resources.melt(id_vars="resource", value_vars=["generated", "sunk", "net"], var_name="flow", value_name="amount")
        fig = px.bar(melted, x="resource", y="amount", color="flow", barmode="group", title="30-Day Resource Faucet/Sink Balance")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(resources, use_container_width=True, hide_index=True)
