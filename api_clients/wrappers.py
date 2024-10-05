from typing import Any, Dict, List

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

    def search(
        self,
        keywords: List[str],
        initial_types: List[str] = None,
        restricted_types: List[str] = None,
        max_depth: int = 2,
        **kwargs,
    ) -> str:
        """
        Returns id of the graph
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
        search_results = self.__client.search(**query_params)

        # Parse and set results to store
        parsed_items = ItemStore().parse_items_from_api_result(graph_key=graph_key, search_results=search_results)
        ItemStore().relate(
            graph_key=graph_key,
            parent_id=graph_key,
            children_ids={parsed_item.name for parsed_item in parsed_items}
        )

        # Expand search
        if max_depth <= 1:
            return graph_key

        for item in parsed_items:
            self.recommend_from_item(
                graph_key=graph_key,
                item=item,
                depth=2,
                max_depth=max_depth
            )
        return graph_key

    def recommend_from_item(
            self,
            graph_key: str,
            item: items.SpotifyItem,
            depth: int,
            max_depth: int
    ):
        if depth > max_depth:
            return
        recommendation_results = self._recommend(
            **item.recommendation_query()
        )
        parsed_items = ItemStore().parse_items_from_api_result(graph_key=graph_key,search_results=recommendation_results)
        ItemStore().relate(
            graph_key=graph_key,
            parent_id=item.name,
            children_ids={parsed_item.name for parsed_item in parsed_items}
        )
        for item in parsed_items:
            self.recommend_from_item(
                graph_key=graph_key,
                item=item,
                depth=depth+1,
                max_depth=max_depth,
            )

    def _recommend(
            self,
            seed_artists: List[items.Artist] = None,
            seed_genres: List[str] = None,
            seed_tracks: List[items.Track] = None,
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
