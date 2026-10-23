"""Path shim: /vet serves the same page as /?page=vet."""
import runpy
import streamlit as st

st.query_params["page"] = "vet"
runpy.run_path(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__file__)), "app.py"), run_name="__main__")
