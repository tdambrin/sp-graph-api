"""
Task Manager to instantiate and handle tasks
"""
from typing import List
import uuid

import items
from api_clients.wrappers import SpotifyWrapper
from items.store import ItemStore
from viz import GraphVisualizer, GraphVisualizerSingleton
from config import OUTPUT_DIR
from tasks.task import Task


class TaskManager:
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
        self._init_query_graph(
            keywords=keywords,
        )

        graph_key = SpotifyWrapper().search(
            keywords=keywords,
            max_depth=2,
            restricted_types=self._selected_types,
            # read_cache=True,
            set_singleton=True,
            write_cache=True,
        )

        res = GraphVisualizer(
            ItemStore().get_graph(graph_key)
        ).set_singleton()

        if save:
            with open(OUTPUT_DIR / ("_".join(keywords + ["0", "4"]) + ".html"), "w") as f:
                f.write(res)

        return res

    @staticmethod
    def _init_query_graph(
        keywords: List[str],
    ) -> str:
        """
        Initialize query graph with a query node

        Args:
            keywords: list of search keywords

        Returns:
            graph key
        """
        task_id = "search_task"  # str(uuid.uuid4())
        graph_key = ItemStore().set_query_node(query_kw=keywords, task_id=task_id)
        return graph_key

    def start_expand_task(self, node_id: str, save: bool = False):
        """
        Start the task in a thread and return task id
        Args:
            node_id: node from which to expand
            save: whether to save the html graph as a result (default false)

        Returns:
            task id
        """
        task_id = "my_task_id"  # str(uuid.uuid4())
        task = Task(
            target=self.expand_from_node,
            task_uuid=task_id,
            use_threading=True,
            node_id=node_id,
            save=save,
        )
        task.run()
        return task_id

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
        current_graph_key = store.current_graph_key  # to make a query param
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
            with open(OUTPUT_DIR / ("_".join([current_graph_key, "0", "4"]) + ".html"), "w") as f:
                f.write(res)


if __name__ == "__main__":
    c = TaskManager(
        selected_types=[
            items.ValidItem.ALBUM.value,
            items.ValidItem.ARTIST.value,
            # items.ValidItem.TRACK.value,
        ]
    )
    c.set_graph_as_html(["charles", "aznavour"], cache=False, save=True)
    html_graph = GraphVisualizerSingleton().graph_as_html
