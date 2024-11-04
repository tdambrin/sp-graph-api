import http.client
import threading
from typing import List

from tornado.web import RequestHandler

from commons import StreamlitApplication, str_to_values, with_streamlit_context
from controller import Controller

st_app = StreamlitApplication()


spg_api_client = http.client.HTTPConnection("localhost", 8501)


@st_app.api_route("/api/search/{keywords}/{selected_types}")
class SearchHandler(RequestHandler):
    def get(self, keywords: str, selected_types: str) -> None:
        """
        Start a search
        Args:
            keywords: search keywords, + separated
            selected_types: search allowed item types, + separated
        """
        threading.Thread(
            target=self.__search,
            kwargs={
                "keywords": str_to_values(keywords, sep="+"),
                "selected_types": str_to_values(selected_types, sep="+"),
            },
        ).start()

    @with_streamlit_context
    def __search(self, keywords: List[str], selected_types: List[str]):
        ctrl = Controller(selected_types=selected_types)
        ctrl.set_graph_as_html(keywords=keywords, cache=False, save=True)


@st_app.api_route("/api/expand/{node_id}/{selected_types}")
class ExpandHandler(RequestHandler):
    def get(self, node_id: str, selected_types: str) -> None:
        """
        Expand graph from a node
        Args:
            node_id: id of the node in the store
            selected_types: expand allowed item types, + separated
        """
        threading.Thread(
            target=self.__expand,
            kwargs={
                "node_id": node_id,
                "selected_types": str_to_values(selected_types, sep="+"),
            },
        ).start()

    @with_streamlit_context
    def __expand(self, node_id: str, selected_types: List[str]):
        ctrl = Controller(selected_types=selected_types)
        ctrl.expand_from_node(node_id=node_id)
