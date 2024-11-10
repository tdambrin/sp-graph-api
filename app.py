"""
Streamlit app to interact with the graph
"""
import json
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from commons import values_to_str
from items import ValidItem
from viz import GraphVisualizer
from web_clients import sp_graph_client

# --- Functions and control vars---

TYPES = {
    ValidItem.ALBUM.value,
    ValidItem.ARTIST.value,
    ValidItem.TRACK.value,
}


@st.fragment
def launch_search():
    keywords_str = values_to_str(
        [kw.strip() for kw in keywords.split(" ") if kw],
        sep="+"
    )
    selected_str = values_to_str(
        [type_ for type_, is_selected in selected.items() if is_selected],
        sep="+"
    )
    sp_graph_client.request(method="GET", url=f"/api/search/{keywords_str}/{selected_str}")
    search_response = sp_graph_client.getresponse()
    body_ = json.loads(search_response.read())
    print(f"Got body {body_}")
    refresh_graph(nodes=body_.get("nodes"), edges=body_.get('edges'))


@st.fragment
def refresh_graph(nodes: List[Dict[str, Any]] = None, edges: List[Dict[str, Any]] = None):
    with placeholder.container():
        if not keywords or nodes is None:
            st.markdown('**Enter search keywords to compute the graph**')
        else:
            gv = GraphVisualizer(
                nodes=nodes,
                edges=edges,
            )
            components.html(gv.html_str(), height=1200,)


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
st.markdown("""
*Alt/Option click*: Open Spotify\\
*Double click*: Expand graph around node
""")

cols = st.columns(10)
selected = {}
for i, _type in enumerate(TYPES):
    with cols[i]:
        selected[_type] = st.checkbox(_type, value=True if _type != ValidItem.ALBUM.value else False)

placeholder = st.empty()

refresh_graph()

if keywords:
    launch_search()
