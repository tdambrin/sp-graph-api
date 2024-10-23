import streamlit as st
import streamlit.components.v1 as components

from controller import Controller
from items import ValidItem

TYPES = {
    ValidItem.ALBUM.value,
    ValidItem.ARTIST.value,
    ValidItem.TRACK.value,
}

st.set_page_config(
    layout="wide",
)

# --- Title ---
st.title("Explore through graphs")
st.markdown("_Powered by Spotify Web API_")

# --- Search params ---
keywords = st.text_input(label="Search spotify: ")

cols = st.columns(10)
selected = {}
for i, _type in enumerate(TYPES):
    with cols[i]:
        selected[_type] = st.checkbox(_type, value=True if _type != ValidItem.TRACK.value else False)

st.write(f"Selected: {', '.join([_type for _type in selected if selected[_type]])}")

# --- Graph ---
controller = Controller(
    keywords=[kw.strip() for kw in keywords.split(" ") if kw],
    selected_types=selected
)
components.html(controller.get_graph_as_html(cache=True, save=True), height=1200, scrolling=True)
