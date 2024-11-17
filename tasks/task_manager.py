"""
Task Manager to instantiate and handle tasks
"""

import uuid
from typing import Any, Dict, List, Optional

import commons
import constants
import networkx as nx
from api_clients.wrappers import SpotifyWrapper
from config import OUTPUT_DIR
from items.item import ValidItem
from items.store import ItemStore
from tasks.task import Task


class TaskManager:
    ALL_TYPES = [
        ValidItem.ALBUM.value,
        ValidItem.ARTIST.value,
        ValidItem.TRACK.value,
    ]

    def __init__(self, selected_types: Optional[List[str]] = None):
        self._selected_types: List[str] = selected_types or TaskManager.ALL_TYPES

    def search_task(self, keywords: List[str], save: bool = False):
        task_id = str(uuid.uuid4())
        graph_key = self._init_query_graph(keywords=keywords, task_id=task_id)
        task = Task(
            target=self.expand_from_query_node,
            task_uuid=task_id,
            use_threading=True,
            keywords=keywords,
            graph_key=graph_key,
            save=save,
            task_id=task_id,
        )
        task.run()
        graph_ = ItemStore().get_graph(graph_key)
        return {
            "task_id": task_id,
            "nodes": commons.nodes_edges_to_list_of_dict(graph_, which=constants.NODES),
            "edges": commons.nodes_edges_to_list_of_dict(
                graph_, which=constants.EDGES, system_=constants.VIS_JS_SYS
            ),
        }

    def expand_from_query_node(
        self,
        keywords: List[str],
        graph_key: str,
        save: bool = False,
        task_id: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Expand with search from query node

        Args:
            keywords: list of keywords to search
            graph_key: to add to the graph
            save: whether to save the graph's output as html
            task_id (str): if provided, set intermediate results to task
        """
        SpotifyWrapper().search(
            keywords=keywords,
            graph_key=graph_key,
            max_depth=2,
            restricted_types=self._selected_types,
            set_singleton=True,
            write_cache=True,
            task_id=task_id,
        )
        current_graph = ItemStore().get_graph(graph_key=graph_key)

        if save:
            if save:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                filename = OUTPUT_DIR / ("_".join([graph_key, "0", "4"]) + ".gml")
                nx.write_gml(current_graph, filename)

        res = {
            "nodes": commons.nodes_edges_to_list_of_dict(
                current_graph, constants.NODES
            ),
            "edges": commons.nodes_edges_to_list_of_dict(
                current_graph, constants.EDGES, system_=constants.VIS_JS_SYS
            ),
        }
        return res

    @staticmethod
    def _init_query_graph(keywords: List[str], task_id: str) -> str:
        """
        Initialize query graph with a query node

        Args:
            keywords: list of search keywords
            task_id: search task id

        Returns:
            graph key
        """
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
        task_id = str(uuid.uuid4())
        task = Task(
            target=self.expand_from_node,
            task_uuid=task_id,
            use_threading=True,
            node_id=node_id,
            save=save,
        )
        task.run()
        return task_id

    def expand_from_node(
        self, node_id: str, save: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Expand the graph from one node
        Args:
            node_id: node from which to expand
            save: whether to save the html graph as a result (default false)

        Returns:
            nodes and edges as dict
        """

        store = ItemStore()
        current_graph_key = store.current_graph_key  # to make a query param
        item = store.get(item_id=node_id)

        if not item.expand_enabled:  # nothing to add
            return {
                "nodes": [],
                "edges": [],
            }

        SpotifyWrapper().find_related(
            graph_key=current_graph_key,
            item=item,
            depth=1,
            max_depth=1,
            restricted_types=self._selected_types,
            set_singleton=True,
        )
        current_graph = ItemStore().get_graph(graph_key=current_graph_key)

        if save:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            filename = OUTPUT_DIR / ("_".join([current_graph_key, "0", "4"]) + ".gml")
            nx.write_gml(current_graph, filename)

        return {
            "nodes": commons.nodes_edges_to_list_of_dict(
                current_graph, constants.NODES
            ),
            "edges": commons.nodes_edges_to_list_of_dict(
                current_graph, constants.EDGES
            ),
        }
