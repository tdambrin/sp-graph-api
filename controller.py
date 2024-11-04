"""
Graph search and viz controller for UI
"""
from typing import List

import items
from api_clients.wrappers import SpotifyWrapper
from items.store import ItemStore
from viz import GraphVisualizer, GraphVisualizerSingleton
from config import OUTPUT_DIR


class Controller:
    def __init__(self, selected_types: List[str] = None):
        self._selected_types = selected_types

    def set_graph_as_html(self, keywords: List[str], cache: bool = False, save: bool = False) -> str:
        """
        Launch search and set current viz graph to result
        Args:
            keywords: list of keywords to search
            cache: whether to read the result from cache initially (default false)
            save: whether to save the html graph as a result (default false)

        Returns:
            graph as html
        """
        if not keywords:
            return '<strong>Enter search keywords to compute the graph </strong>'
        GraphVisualizerSingleton().set_loading()

        if cache:
            graph_key = ItemStore().graph_key_from_keywords(keywords=keywords)
            if ItemStore().get_graph(graph_key):
                res = GraphVisualizer(
                    ItemStore().get_graph(graph_key)
                ).set_singleton()
                if save:
                    with open(OUTPUT_DIR / "_".join(keywords + ["0", "3"]), "w") as f:
                        f.write(res)
                return res

        graph_key = SpotifyWrapper().search(
            keywords=keywords,
            max_depth=2,
            initial_types=self._selected_types,
            restricted_types=self._selected_types,
            # read_cache=True,
            set_singleton=True,
            write_cache=True,
        )

        res = GraphVisualizer(
            ItemStore().get_graph(graph_key)
        ).set_singleton()

        if save:
            with open(OUTPUT_DIR / ("_".join(keywords + ["0", "3"]) + ".html"), "w") as f:
                f.write(res)

        return res

    def expand_from_node(self, node_id: str, save: bool = False) -> str:
        """
        Expand the graph from one node
        Args:
            node_id: node from which to expand
            save: whether to save the html graph as a result (default false)

        Returns:
            graph as html
        """

        store = ItemStore()
        current_graph_key = store.current_graph_key
        item = store.get(item_id=node_id)
        if not item.expand_enabled:
            return GraphVisualizerSingleton().graph_as_html

        SpotifyWrapper().find_related(
            graph_key=current_graph_key,
            item=item,
            depth=1,
            max_depth=1,
            restricted_types=self._selected_types,
            set_singleton=True,
        )
        res = GraphVisualizer(
            ItemStore().get_graph(current_graph_key)
        ).set_singleton()

        if save:
            with open(OUTPUT_DIR / ("_".join([current_graph_key, "0", "3"]) + ".html"), "w") as f:
                f.write(res)


if __name__ == "__main__":
    c = Controller(
        selected_types=[
            items.ValidItem.ALBUM.value,
            items.ValidItem.ARTIST.value,
            # items.ValidItem.TRACK.value,
        ]
    )
    c.set_graph_as_html(["charles", "aznavour"], cache=False, save=True)
    html_graph = GraphVisualizerSingleton().graph_as_html
