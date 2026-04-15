import streamlit as st


def render():
    st.title("🔍 Task Drill-down")
    st.info("Select a run and task to view the full response + judge rationale.")
    # TODO: fetch run results from /results/{run_id} and display
