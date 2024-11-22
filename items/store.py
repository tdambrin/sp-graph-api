"""
Result items store - Singleton

Contains:
    - items cached to avoid parsing again
    - graphs for each query
"""

from functools import reduce
from operator import add
from typing import Any, Callable, Dict, List, Optional, Set

import commons
import config
import constants
import networkx as nx  # type: ignore
from commons.metaclasses import ThreadSafeSingleton
from items.item import Album, Artist, Playlist, SpotifyItem, Track, ValidItem
from status import StatusManager


class ItemStore(metaclass=ThreadSafeSingleton):
    def __init__(self):
        """
        _items: cache for SpotifyItem, key is spotify foreign item id
        _graphs: per session, per graph_key
        """
        self._items: Dict[str, SpotifyItem] = {}
        self._graphs: Dict[str, Dict[str, nx.DiGraph]] = dict()

    @property
    def _items_parser(self) -> Dict[ValidItem, Callable[..., SpotifyItem]]:
        return {
            ValidItem.ALBUM: Album,
            ValidItem.ARTIST: Artist,
            ValidItem.PLAYLIST: Playlist,
            ValidItem.TRACK: Track,
        }

    @property
    def _items_api_keys(self):
        return {
            ValidItem.ALBUM: "albums",
            ValidItem.ARTIST: "artists",
            ValidItem.PLAYLIST: "playlist",
            ValidItem.TRACK: "tracks",
        }

    @property
    def session_ids(self) -> Set[str]:
        return set(self._graphs.keys())

    @property
    def graph_keys(self) -> Set[str]:
        return set(
            sum(
                [
                    list(session_graphs.keys())
                    for session_graphs in self._graphs.values()
                ],
                [],
            )
        )

    @staticmethod
    def _depth_node_size(depth: int):
        if depth <= 1:
            return 50
        if depth == 2:
            return 30
        return 20

    @staticmethod
    def _popularity_node_size(popularity: int = None):
        if popularity is None or popularity <= 20:
            return 10
        return int(popularity / 2)

    @staticmethod
    def graph_key_from_keywords(keywords: List[str]):
        return commons.values_to_str(keywords, "+")

    def get(self, item_id: str) -> SpotifyItem | None:
        return self._items.get(item_id)

    def get_all_items(self):
        return self._items

    def get_graphs(self, session_id: str) -> Optional[Dict[str, nx.DiGraph]]:
        """
        Get active graphs from session
        Args:
            session_id (str): uuid4

        Returns:
            dict of graphs with id of their query node as key
        """
        return self._graphs.get(session_id)

    def get_graph(
        self, session_id: str, graph_key: str
    ) -> Optional[nx.DiGraph]:
        return self._graphs.get(session_id, {}).get(graph_key)

    def init_session(self, session_id: str):
        """
        Initialize graph for a session

        Args:
            session_id (str): uuid4
        """
        if self._graphs.get(session_id) is not None:
            return
        self._graphs[session_id] = {}

    def init_graph(self, session_id: str, graph_key: str):
        """
        Initialize graph for a session

        Args:
            session_id (str): uuid4
            graph_key (str): id of query node
        """
        self.init_session(session_id=session_id)
        if self._graphs[session_id].get(graph_key) is not None:
            return
        self._graphs[session_id][graph_key] = nx.DiGraph()

    def _add_node(
        self,
        session_id: str,
        graph_key: str,
        item: SpotifyItem,
        selected_types: List[str],
        depth: int = 3,
        color: str = None,
        **kwargs,
    ):
        """
        Add node to the graph

        Args:
            session_id (str): user session identifier
            graph_key (str): id of the graph to add item to
            item (items.SpotifyItem): parsed item
            selected_types (list): item types to add to node
            depth (int): for size styling
            color (str): node color, if None will be item.node_color
        """

        # Because Vis JS error if present
        optional_kwargs = {}
        if item.images:
            optional_kwargs["image"] = item.images[0]["url"]

        # Add node to graph
        self._graphs[session_id][graph_key].add_node(
            item.id,
            label=item.name,
            title=item.title,
            size=self._popularity_node_size(item.popularity),
            color=color or item.node_color,
            shape="dot" if not item.images else "circularImage",
            href=item.external_urls.get("spotify", "_blank"),
            preview_url=item.preview_url if isinstance(item, Track) else None,
            expand_enabled=item.expand_enabled,
            selected_types=commons.values_to_str(selected_types, sep="+"),
            graph_key=graph_key,
            node_type=item.type.value,
            depth=depth,
            **optional_kwargs,
            **kwargs,
            # font="10px arial white",
        )

    def set_query_node(
        self,
        session_id: str,
        query_kw: List[str],
        task_id: str,
        override: bool = False,
        **kwargs,
    ) -> str:
        """
        Set graph central query node
        Args:
            session_id (str): user session identifier
            query_kw: keywords used for the search
            task_id: task id corresponding to the search
            override (bool): whether to override if graph already exists

        Returns:
            Graph key
        """
        query_key = ItemStore.graph_key_from_keywords(query_kw)
        if self._graphs.get(session_id, {}).get(query_key):
            if not override:
                return query_key
            self._graphs[session_id][query_key] = nx.DiGraph()
        self.init_graph(session_id=session_id, graph_key=query_key)
        self._graphs[session_id][query_key].add_node(
            query_key,
            label=commons.values_to_str(query_kw, sep=" "),
            title="Query",
            size=50,
            color=config.NodeColor.PRIMARY.value,
            shape="circle",
            href=f"https://open.spotify.com/search/{'%20'.join(query_kw)}",
            task_id=task_id,
            graph_key=query_key,
            node_type="query",
            **kwargs,
        )
        return query_key

    def __parse_item(
        self, item: Dict[str, Any], item_type: ValidItem
    ) -> SpotifyItem:
        """
        Parse dict into subclass of items.SpotifyItem
        Args:
            item (dict): kwargs for item constructor
            item_type (one of ValidItem): to select constructor

        Returns:
            parsed items.SpotifyItem
        """
        return self._items_parser[item_type](**item)

    def __parse_item_with_type(
        self,
        session_id: str,
        graph_key: str,
        item: Dict[str, Any],
        item_type: ValidItem,
        depth: int,
        selected_types: List[str],
        task_id: Optional[str],
        **kwargs,
    ) -> SpotifyItem:
        """
        Parse item and add it to store

        Args:
            session_id (str): user session identifier
            graph_key (str): id of the graph to add item to
            item (dict): item to parse and add
            item_type (one of ValidItem):
            depth (int): depth of node (for styling)
            selected_types (list): item types to add to node
            task_id (str): if provided, set intermediate results to task

        Returns:
            parsed items.SpotifyItem
        """
        if not self._items.get(item["id"]):
            self._items[item["id"]] = self.__parse_item(
                item=item, item_type=item_type
            )

        if (
            not self._graphs.get(session_id, {})
            .get(graph_key)
            .nodes.get(item["id"])
        ):
            self._add_node(
                session_id=session_id,
                graph_key=graph_key,
                item=self._items[item["id"]],
                depth=depth,
                selected_types=selected_types,
                **kwargs,
            )
        if task_id is not None:
            self.__add_nodes_edges_to_task(
                session_id=session_id,
                graph_key=graph_key,
                task_id=task_id,
            )

        return self._items[item["id"]]

    def parse_items_from_list(
        self, dict_items: List[Dict[str, Any]], item_type: ValidItem
    ) -> List[SpotifyItem]:
        return [
            self.__parse_item(item=item, item_type=item_type)
            for item in dict_items
        ]

    def parse_items_from_api_result(
        self,
        session_id: str,
        graph_key: str,
        search_results: Dict[str, Any],
        depth: int,
        selected_types: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> List[SpotifyItem]:
        """
        Parse api result with json objects for potentially all items.SpotifyItem subclasses
        Args:
            session_id (str): user session identifier
            graph_key (str): id of the graph to add item to
            search_results (dict): api result with first level keys as spotify items names
            depth (int): for styling when adding to the graph
            selected_types: results obtained from filtering on these types
            task_id (str): if provided, set intermediate results to task

        Returns:
            list of parsed items.SpotifyItem
        """
        selected_types = selected_types or [
            ValidItem.ALBUM.value,
            ValidItem.ARTIST.value,
            ValidItem.TRACK.value,
        ]

        def _items_or_empty(
            entry: Optional[Dict[str, Any]], entry_type: ValidItem
        ) -> List[Dict[str, Any]]:
            if (
                (not entry)
                or (entry is None)
                or (isinstance(entry, dict) and not entry.get("items"))
            ):
                return []
            return [
                {"item": item, "item_type": entry_type}
                for item in (
                    entry["items"] if isinstance(entry, dict) else entry
                )
            ]

        non_parsed_items = reduce(
            add,
            map(
                _items_or_empty,
                map(search_results.get, self._items_api_keys.values()),
                self._items_api_keys.keys(),
            ),
        )
        self.init_graph(session_id=session_id, graph_key=graph_key)
        return [
            self.__parse_item_with_type(
                session_id=session_id,
                graph_key=graph_key,
                depth=depth,
                selected_types=selected_types,
                task_id=task_id,
                **item,
                **kwargs,
            )
            for item in non_parsed_items
        ]

    def relate(
        self,
        session_id: str,
        graph_key: str,
        parent_id: str,
        children_ids: Set[str],
        depth: int,
        task_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Add edges between result/query nodes

        Args:
            session_id (str): user session identifier
            graph_key (str): id of the graph to relate item in
            parent_id (str): node id of the parent node to relate item with
            children_ids (List[str]): list of node ids relate parent item with
            depth (int): for styling when adding to the graph
            task_id (str): if provided, set intermediate results to task
        """
        for child_id in children_ids:
            # children first for color
            self._graphs[session_id][graph_key].add_edge(
                child_id,
                parent_id,
                width=config.EDGE_WIDTH,
                id=f"{parent_id}_{child_id}",
                unordered_id=commons.commutative_hash(parent_id, child_id),
                **kwargs,
            )

        if task_id is not None:
            self.__add_nodes_edges_to_task(
                session_id=session_id, graph_key=graph_key, task_id=task_id
            )

    def get_successors(self, session_id: str, graph_key: str, node_id: str):
        """
        Get successors of a node in the directed graph

        Args:
            session_id (str): user session identifier
            graph_key (str): id of the graph to relate item in
            node_id (str): node identifier
        """
        if (
            node := self._graphs.get(session_id, {})
            .get(graph_key, {})
            .get(node_id)
        ) is None:
            return []
        return [
            n for n in self._graphs[session_id][graph_key].successors(node)
        ]

    def __add_nodes_edges_to_task(
        self, session_id: str, graph_key: str, task_id: str
    ):
        """
        Add nodes and edges to task result.
        Used to set intermediate (when task still running) results.

        Args:
            session_id (str): user session identifier
            graph_key (str): id of the graph to relate item in
            task_id (str): if provided, set intermediate results to task
        """
        current_graph = self.get_graph(
            session_id=session_id, graph_key=graph_key
        )
        nodes_and_edges = {
            "nodes": commons.nodes_edges_to_list_of_dict(
                current_graph, constants.NODES  # type: ignore
            ),
            "edges": commons.nodes_edges_to_list_of_dict(
                current_graph, constants.EDGES, system_=constants.VIS_JS_SYS  # type: ignore
            ),
        }
        StatusManager().set_intermediate_result(
            task_id=task_id,
            result=nodes_and_edges,
        )
