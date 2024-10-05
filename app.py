import streamlit as st
import streamlit.components.v1 as components

from config import OUTPUT_DIR

st.title("Explore Spotify")

HtmlFile = open(OUTPUT_DIR / "hruangbin_v_0_1.html", 'r', encoding='utf-8')
source_code = HtmlFile.read()
components.html(source_code, height=1200, width=1000)

