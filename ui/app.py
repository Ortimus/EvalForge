"""
EvalForge Streamlit app — main entry point.
Run with: python3 -m streamlit run ui/app.py
"""
import streamlit as st

st.set_page_config(page_title="EvalForge", layout="wide")

st.sidebar.title("EvalForge")
page = st.sidebar.radio("Navigate", ["Leaderboard", "Capability Radar", "Task Drill-down"])

if page == "Leaderboard":
    from pages.leaderboard import render        # ← relative, no 'ui.' prefix
elif page == "Capability Radar":
    from pages.radar import render
else:
    from pages.drilldown import render

render()