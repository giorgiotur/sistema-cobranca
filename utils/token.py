import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
BASE_URL_API = os.getenv("BASE_URL_API")

def carregar_token():
    return st.session_state.get("token")
