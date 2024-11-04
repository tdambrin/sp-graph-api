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
        threading.Thread(
            target=self.__search,
            kwargs={
                "keywords": str_to_values(keywords, sep="+"),
                "selected_types": str_to_values(selected_types, sep="+"),
            },
        ).start()

    @with_streamlit_context
    def __search(self, keywords: List[str], selected_types: List[str]):
        ctrl = Controller(
            keywords=keywords,
            selected_types={
                selected_type: True for selected_type in selected_types
            },
        )
        ctrl.set_graph_as_html(cache=False, save=True)
