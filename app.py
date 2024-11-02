import streamlit as st
import streamlit.components.v1 as components

from controller import Controller
from items import ValidItem
from viz import GraphVisualizerSingleton
from commons import with_streamlit_context
from threading import Thread

# --- Functions and control vars---

TYPES = {
    ValidItem.ALBUM.value,
    ValidItem.ARTIST.value,
    ValidItem.TRACK.value,
}


@with_streamlit_context
def launch_search():
    ctrl = Controller(
        keywords=[kw.strip() for kw in keywords.split(" ") if kw],
        selected_types=selected
    )
    Thread(target=ctrl.set_graph_as_html, kwargs={"cache": False, "save": True}).start()


@st.fragment(run_every=1)
def periodic_refresh():
    with placeholder.container():
        gvs = GraphVisualizerSingleton()
        components.html(gvs.graph_as_html, height=1200,)


# --- Streamlit components ---

st.set_page_config(
    layout="wide",
    page_title="Spotify Graph",
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
        selected[_type] = st.checkbox(_type, value=True if _type != ValidItem.ALBUM.value else False)

placeholder = st.empty()

periodic_refresh()

if keywords:
    launch_search()
