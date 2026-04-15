import streamlit as st
import pandas as pd


def render():
    st.title("🏆 Model Leaderboard")
    st.info("No evaluation runs yet. Submit one via POST /evaluate.")
    # TODO: fetch from /leaderboard API and render sortable table
