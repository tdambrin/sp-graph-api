from functools import reduce
from operator import add
from typing import Any, Callable, Dict, List, Optional, Set

import networkx as nx

import commons
from commons.metaclasses import ThreadSafeSingleton
from . import (
    Album,
    Artist,
    Playlist,
    Track,
    SpotifyItem,
    ValidItem,
)


class ItemStore(metaclass=ThreadSafeSingleton):
    def __init__(self):
        self._items: Dict[str, SpotifyItem] = {}
        self._graphs: Dict[str, nx.Graph] = dict()

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

    @property
    def graph_keys(self) -> Set[str]:
        return set(self._graphs.keys())

    def get(self, item_id: str):
        return self._items.get(item_id)

    def get_all_items(self):
        return self._items

    def get_graph(self, graph_key: str):
        return self._graphs.get(graph_key)

    def set_query_node(self, query_kw: List[str]) -> str:
        query_key = commons.values_to_str(query_kw, "+")
        if self._graphs.get(query_key):
            return query_key
        self._graphs[query_key] = nx.Graph()
        self._graphs[query_key].add_node(query_key)
        return query_key

    def __parse_item(self, item: Dict[str, Any], item_type: ValidItem):
        return self._items_parser[item_type](**item)

    def __parse_item_with_type(self, graph_key: str, item: Dict[str, Any], item_type: ValidItem) -> SpotifyItem:
        if not self._items.get(item["id"]):
            self._items[item["id"]] = self.__parse_item(item=item, item_type=item_type)
            self._graphs[graph_key].add_node(self._items[item["id"]].name)
        return self._items[item["id"]]

    def parse_items_from_list(self, dict_items: List[Dict[str, Any]], item_type: ValidItem) -> List[SpotifyItem]:
        return [self.__parse_item(item=item, item_type=item_type) for item in dict_items]

    def parse_items_from_api_result(
            self, graph_key: str, search_results: Dict[str, Any]
    ) -> List[SpotifyItem]:
        def _items_or_empty(entry: Optional[Dict[str, Any]], entry_type: ValidItem) -> List[Dict[str, Any]]:
            if (not entry) or (isinstance(entry, dict) and not entry.get("items")):
                return []
            return [{"item": item, "item_type": entry_type} for item in (entry if isinstance(entry, list) else entry["items"])]

        non_parsed_items = reduce(
            add,
            map(_items_or_empty,
                map(search_results.get, self._items_api_keys.values()),
                self._items_api_keys.keys()
                )
        )

        return [self.__parse_item_with_type(**{**item, "graph_key": graph_key}) for item in non_parsed_items]

    def relate(self, graph_key: str, parent_id: str, children_ids: Set[str]):
        for children_id in children_ids:
            self._graphs[graph_key].add_edge(parent_id, children_id)
