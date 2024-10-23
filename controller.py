"""
Graph search and viz controller for UI
"""
from typing import Dict, List

import items
from api_clients.wrappers import SpotifyWrapper
from items.store import ItemStore
from viz import GraphVisualizer
from config import OUTPUT_DIR


class Controller:
    def __init__(self, keywords: List[str], selected_types: Dict[str, bool]):
        self._keywords = keywords
        self._selected_types = selected_types

    def get_graph_as_html(self, cache: bool = False, save: bool = False):
        if not self._keywords:
            return '<strong>Enter search keywords to compute the graph </strong>'

        if cache:
            graph_key = ItemStore().graph_key_from_keywords(keywords=self._keywords)
            if ItemStore().get_graph(graph_key):
                res = GraphVisualizer(
                    ItemStore().get_graph(graph_key)
                ).html_str()
                if save:
                    with open(OUTPUT_DIR / "_".join(self._keywords + ["0", "3"]), "w") as f:
                        f.write(res)
                return res

        graph_key = SpotifyWrapper().search(
            keywords=self._keywords,
            max_depth=2,
            initial_types=[_type for _type in self._selected_types if self._selected_types[_type]],
            restricted_types=[_type for _type in self._selected_types if self._selected_types[_type]],
            # read_cache=True,
            write_cache=True,
        )

        res = GraphVisualizer(
            ItemStore().get_graph(graph_key)
        ).html_str()

        if save:
            with open(OUTPUT_DIR / ("_".join(self._keywords + ["0", "3"]) + ".html"), "w") as f:
                f.write(res)

        return res


if __name__ == "__main__":
    c = Controller(
        keywords=["charles", "aznavour"],
        selected_types={
            items.ValidItem.ALBUM.value: True,
            items.ValidItem.ARTIST.value: True,
            items.ValidItem.TRACK.value: False,
        }
    )
    c.get_graph_as_html(cache=False, save=True)
