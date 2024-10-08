import json
from typing import Any, Dict, List, Tuple
import functools

import items
from commons import utils
from items import ItemStore

from .clients import spotify_client


class SpotifyWrapper:
    def __init__(self):
        self.__client = spotify_client

    @property
    def all_types(self):
        return ["album", "artist", "playlist", "track", "show", "episode", "audiobook"]

    @staticmethod
    def cache(name, obj):
        from config import PROJECT_ROOT
        with open(PROJECT_ROOT / "responses" / name, "w") as f:
            json.dump(obj, f)

    @staticmethod
    def read_cache(name):
        from config import PROJECT_ROOT
        return json.load(open(PROJECT_ROOT / "responses" / name, "r"))

    def search(
        self,
        keywords: List[str],
        initial_types: List[str] = None,
        restricted_types: List[str] = None,
        max_depth: int = 2,
        **kwargs,
    ) -> str:
        """
        Search from keywords and recursive recommendation. Add results to items.ItemStore

        Args:
            keywords: search keywords
            initial_types: first level result item type restriction. All if None. NOT_IMPLEMENTED
            restricted_types: first level result item type restriction. All if None. NOT_IMPLEMENTED
            max_depth: recommendations start at level 2

        Returns:
            id of the graph
        """

        if initial_types is None:
            initial_types = self.all_types
        if set(initial_types) - set(self.all_types):
            raise ValueError(
                "[Error: SpotifyWrapper.search] "
                f"initial_types={','.join(initial_types)} contains illegal values."
                f"Accepted values are {','.join(self.all_types)}"
            )

        graph_key = ItemStore().set_query_node(keywords)

        # Get spotify results
        query_params = self.__build_search_query(
            keywords=keywords,
            restricted_types=restricted_types or self.all_types,
        )

        if kwargs.get("read_cache"):
            search_results = SpotifyWrapper.read_cache(f"search_{graph_key.lower()}.json")
        else:
            search_results = self.__client.search(**query_params)

        if kwargs.get("write_cache"):
            SpotifyWrapper.cache(f"search_{graph_key.lower()}.json", search_results)

        # Parse and set results to store
        parsed_items = ItemStore().parse_items_from_api_result(
            graph_key=graph_key, search_results=search_results, depth=1
        )
        ItemStore().relate(
            graph_key=graph_key,
            parent_id=graph_key,
            children_ids={parsed_item.id for parsed_item in parsed_items},
            depth=1,
        )

        # Expand search
        if max_depth <= 1:
            return graph_key

        for item in parsed_items:
            self.recommend_from_item(
                graph_key=graph_key,
                item=item,
                depth=2,
                max_depth=max_depth,
                **kwargs
            )
        return graph_key

    def recommend_from_item(
            self,
            graph_key: str,
            item: items.SpotifyItem,
            depth: int,
            max_depth: int,
            **kwargs,
    ):
        """
        Get recommendation results from item. Add items to items.ItemStore
        Args:
            graph_key (str): id of the graph to add items to
            item: parsed starting item
            depth: to recursively recommend from result nodes
            max_depth: inclusive
        """
        if depth > max_depth:
            return

        if kwargs.get("read_cache"):
            recommendation_results = SpotifyWrapper.read_cache(f"recommend_{item.id}.json")
        else:
            recommendation_results = self._recommend(
                **item.recommendation_query()
            )
        if kwargs.get("write_cache"):
            SpotifyWrapper.cache(f"recommend_{item.id}.json", recommendation_results)

        parsed_items = ItemStore().parse_items_from_api_result(
            graph_key=graph_key,search_results=recommendation_results, depth=depth,
        )
        ItemStore().relate(
            graph_key=graph_key,
            parent_id=item.id,
            children_ids={parsed_item.id for parsed_item in parsed_items},
            depth=depth,
        )
        for item in parsed_items:
            self.recommend_from_item(
                graph_key=graph_key,
                item=item,
                depth=depth+1,
                max_depth=max_depth,
            )

    @functools.cache
    def _recommend(
            self,
            seed_artists: Tuple[items.Artist] = None,
            seed_genres: Tuple[str] = None,
            seed_tracks: Tuple[items.Track] = None,
            limit: int = 5,
            **kwargs,
    ) -> Dict[str, Any]:
        return self.__client.recommendations(
            seed_artists=[a.id for a in seed_artists][:5] if seed_artists else None,
            seed_genres=seed_genres[:5] if seed_genres else None,
            seed_tracks=[t.id for t in seed_tracks][:5] if seed_tracks else None,
            limit=limit,
        )

    @staticmethod
    def __build_search_query(
        keywords: List[str],
        restricted_types: List[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        params = {
            "q": utils.values_to_str(keywords, " "),
            "limit": limit,
        }
        if restricted_types:
            params["type"] = utils.values_to_str(restricted_types, ",")
        return params

    def search_exemple(self):
        return self.__client.search(q='khruangbin', limit=20)
