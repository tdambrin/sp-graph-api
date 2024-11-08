import streamlit as st
import streamlit.components.v1 as components

from items import ValidItem
from viz import GraphVisualizerSingleton
from commons import values_to_str

from api import spg_api_client
# --- Functions and control vars---

# Fast API
import uvicorn
import threading
from api_v2 import api_v2
threading.Thread(
    target=uvicorn.run,
    kwargs={
        "app": api_v2,
        "host": "127.0.0.1",
        "port": 8502,
        "log_level": "info",

    },
).start()
# End Fast API

TYPES = {
    ValidItem.ALBUM.value,
    ValidItem.ARTIST.value,
    ValidItem.TRACK.value,
}


def launch_search():
    keywords_str = values_to_str(
        [kw.strip() for kw in keywords.split(" ") if kw],
        sep="+"
    )
    selected_str = values_to_str(
        [type_ for type_, is_selected in selected.items() if is_selected],
        sep="+"
    )
    spg_api_client.request(method="GET", url=f"/api/search/{keywords_str}/{selected_str}")


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
