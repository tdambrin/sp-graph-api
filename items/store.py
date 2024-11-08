"""
Result items store - Singleton

Contains:
    - items cached to avoid parsing again
    - graphs for each query
"""

from functools import reduce
from operator import add
from typing import Any, Callable, Dict, List, Optional, Set

import networkx as nx

import commons
import config
from commons.metaclasses import ThreadSafeSingleton
from items.item import (
    Album,
    Artist,
    Playlist,
    Track,
    SpotifyItem,
    ValidItem,
)
from viz import GraphVisualizer


class ItemStore(metaclass=ThreadSafeSingleton):
    def __init__(self):
        self._items: Dict[str, SpotifyItem] = {}
        self._graphs: Dict[str, nx.DiGraph] = dict()
        self._current_graph_key = None

    @property
    def _items_parser(self) -> Dict[ValidItem, Callable[..., SpotifyItem]]:
        return {
            ValidItem.ALBUM: Album,
            ValidItem.ARTIST: Artist,
            ValidItem.PLAYLIST: Playlist,
            ValidItem.TRACK: Track
        }

    @property
    def _items_api_keys(self):
        return {
            ValidItem.ALBUM: "albums",
            ValidItem.ARTIST: "artists",
            ValidItem.PLAYLIST: "playlist",
            ValidItem.TRACK: "tracks",
        }

    @staticmethod
    def _depth_node_size(depth: int):
        if depth <= 1:
            return 30
        if depth == 2:
            return 20
        return 10

    @staticmethod
    def _depth_edge_weight(depth: int):
        if depth <= 1:
            return 12
        if depth == 2:
            return 6
        return 1

    @property
    def graph_keys(self) -> Set[str]:
        return set(self._graphs.keys())

    @property
    def current_graph_key(self):
        return self._current_graph_key

    def get(self, item_id: str):
        return self._items.get(item_id)

    def get_all_items(self):
        return self._items

    def get_graph(self, graph_key: str):
        return self._graphs.get(graph_key)

    def get_current_graph(self):
        return self._graphs.get(self._current_graph_key)

    def _set_current_graph_key(self, key: str):
        self._current_graph_key = key

    def _add_node(self, graph_key: str, item: SpotifyItem, selected_types: List[str], depth: int = 3):
        """
        Add node to the graph

        Args:
            graph_key (str): id of the graph to add item to
            item (items.SpotifyItem): parsed item
            selected_types (list): item types to add to node
            depth (int): for size styling
        """
        optional_kwargs = {}
        if item.images:
            optional_kwargs["image"] = item.images[0]["url"]
        self._graphs[graph_key].add_node(
            item.id,
            label=item.name,
            title=item.title,
            size=self._depth_node_size(depth),
            color=item.node_color,
            shape="dot" if not item.images else "circularImage",
            href=item.external_urls.get("spotify", "_blank"),
            preview_url=item.preview_url if isinstance(item, Track) else None,
            expand_enabled=item.expand_enabled,
            selected_types=commons.values_to_str(selected_types, sep="+"),
            **optional_kwargs,
            # font="10px arial white",
        )

    @staticmethod
    def graph_key_from_keywords(keywords: List[str]):
        return commons.values_to_str(keywords, "+")

    def set_query_node(self, query_kw: List[str]) -> str:
        query_key = ItemStore.graph_key_from_keywords(query_kw)
        self._set_current_graph_key(query_key)
        if self._graphs.get(query_key):
            return query_key
        self._graphs[query_key] = nx.DiGraph()
        self._graphs[query_key].add_node(
            query_key,
            label=" ".join(query_kw),
            title="Query node",
            size=30,
            color=config.NodeColor.PRIMARY.value,
            shape="circle",
            href=f"https://open.spotify.com/search/{'%20'.join(query_kw)}",
            # font="10px arial white",
        )
        return query_key

    def set_singleton_viz(self, graph_key: str):
        """
        Refreshed the visualization singleton with graph from store
        Args:
            graph_key: identifies the graph to select
        """
        GraphVisualizer(
            self.get_graph(graph_key)
        ).set_singleton()

    def __parse_item(self, item: Dict[str, Any], item_type: ValidItem) -> SpotifyItem:
        """
        Parse dict into subclass of items.SpotifyItem
        Args:
            item (dict): kwargs for item constructor
            item_type (one of ValidItem): to select constructure

        Returns:
            parsed items.SpotifyItem
        """
        return self._items_parser[item_type](**item)

    def __parse_item_with_type(
            self, graph_key: str, item: Dict[str, Any], item_type: ValidItem, depth: int, selected_types: List[str],
    ) -> SpotifyItem:
        """
        Parse item and add it to store

        Args:
            graph_key (str): id of the graph to add item to
            item (dict): item to parse and add
            item_type (one of ValidItem):
            depth (int): depth of node (for styling)
            selected_types (list): item types to add to node

        Returns:
            parsed items.SpotifyItem
        """
        if not self._items.get(item["id"]):
            self._items[item["id"]] = self.__parse_item(item=item, item_type=item_type)
        if not self._graphs[graph_key].nodes.get(item["id"]):
            self._add_node(
                graph_key=graph_key, item=self._items[item["id"]], depth=depth, selected_types=selected_types
            )
        return self._items[item["id"]]

    def parse_items_from_list(self, dict_items: List[Dict[str, Any]], item_type: ValidItem) -> List[SpotifyItem]:
        return [self.__parse_item(item=item, item_type=item_type) for item in dict_items]

    def parse_items_from_api_result(
            self, graph_key: str, search_results: Dict[str, Any], depth: int,
            selected_types: List[str] = None,
    ) -> List[SpotifyItem]:
        """
        Parse api result with json objects for potentially all items.SpotifyItem subclasses
        Args:
            graph_key (str): id of the graph to add item to
            search_results (dict): api result with first level keys as spotify items names
            depth (int): for styling when adding to the graph
            selected_types: results obtained from filtering on these types

        Returns:
            list of parsed items.SpotifyItem
        """
        selected_types = selected_types or [ValidItem.ALBUM.value, ValidItem.ARTIST.value, ValidItem.TRACK.value]

        def _items_or_empty(entry: Optional[Dict[str, Any]], entry_type: ValidItem) -> List[Dict[str, Any]]:
            if (not entry) or (isinstance(entry, dict) and not entry.get("items")):
                return []
            return [{"item": item, "item_type": entry_type}
                    for item in (entry if isinstance(entry, list) else entry["items"])]

        non_parsed_items = reduce(
            add,
            map(_items_or_empty,
                map(search_results.get, self._items_api_keys.values()),
                self._items_api_keys.keys()
                )
        )

        return [
            self.__parse_item_with_type(**{
                **item, "graph_key": graph_key, "depth": depth, "selected_types": selected_types
            })
            for item in non_parsed_items
        ]

    def relate(self, graph_key: str, parent_id: str, children_ids: Set[str], depth: int):
        """
        Add edges between result/query nodes

        Args:
            graph_key (str): id of the graph to relate item in
            parent_id (str): node id of the parent node to relate item with
            children_ids (List[str]): list of node ids relate parent item with
            depth (int): for styling when adding to the graph
        """
        for children_id in children_ids:
            # children first for color
            self._graphs[graph_key].add_edge(children_id, parent_id, weight=self._depth_edge_weight(depth))
