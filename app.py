import streamlit as st
import streamlit.components.v1 as components

from controller import Controller

st.set_page_config(
    layout="wide",
)

st.title("Explore through graphs")
st.markdown("_Powered by Spotify Web API_")

keywords = st.text_input(label="Search spotify: ", value="the weekend")

controller = Controller(keywords=[kw.strip() for kw in keywords.split(" ") if kw])

components.html(controller.get_graph_as_html(cache=True, save=True), height=1200, scrolling=True)
