"""
Graph search and viz controller for UI
"""
from typing import List

from api_clients.wrappers import SpotifyWrapper
from items.store import ItemStore
from viz import GraphVisualizer
from config import OUTPUT_DIR


class Controller:
    def __init__(self, keywords: List[str]):
        self._keywords = keywords

    def get_graph_as_html(self, cache: bool = False, save: bool = False):
        if not self._keywords:
            return '<p style="color:white;"> Enter search keywords to compute the graph </p>'

        if cache:
            graph_key = ItemStore().graph_key_from_keywords(keywords=self._keywords)
            if ItemStore().get_graph(graph_key):
                res = GraphVisualizer(
                    ItemStore().get_graph(graph_key)
                ).html_str()
                if save:
                    with open(OUTPUT_DIR / "_".join(self._keywords + ["0", "2"]), "w") as f:
                        f.write(res)
                return res

        graph_key = SpotifyWrapper().search(
            keywords=self._keywords,
            max_depth=2,
            # read_cache=True,
            # write_cache=True,
        )

        res = GraphVisualizer(
            ItemStore().get_graph(graph_key)
        ).html_str()

        if save:
            with open(OUTPUT_DIR / ("_".join(self._keywords + ["0", "2"]) + ".html"), "w") as f:
                f.write(res)

        return res


if __name__ == "__main__":
    query = ["lunatic"]
    c = Controller(query)
    c.get_graph_as_html(cache=False, save=True)
