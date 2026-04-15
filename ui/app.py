"""
EvalForge Streamlit app — main entry point.
Run with: streamlit run ui/app.py
"""
import streamlit as st

st.set_page_config(page_title="EvalForge", layout="wide")

st.sidebar.title("EvalForge")
page = st.sidebar.radio("Navigate", ["Leaderboard", "Capability Radar", "Task Drill-down"])

if page == "Leaderboard":
    from ui.pages.leaderboard import render
elif page == "Capability Radar":
    from ui.pages.radar import render
else:
    from ui.pages.drilldown import render

render()
