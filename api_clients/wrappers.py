import functools
import json
import operator
from typing import Any, Dict, List, Tuple

import items
from commons import utils
from items import ItemStore

from .clients import spotify_client


class SpotifyWrapper:
    REC_SIZE = 5  # Recommendation max size for one node

    def __init__(self):
        self.__client = spotify_client

    @property
    def all_types(self):
        return [
            items.ValidItem.ALBUM.value, items.ValidItem.ARTIST.value, items.ValidItem.TRACK.value,
            # items.ValidItem.PLAYLIST.value,
            # items.ValidItem.SHOW.value, items.ValidItem.EPISODE.value, items.ValidItem.AUDIOBOOK.value,
        ]

    @property
    def type_rec_weight(self):
        """ Recommendation weight for each type when several possible """
        return {
            items.ValidItem.ALBUM.value: 1, items.ValidItem.ARTIST.value: 1, items.ValidItem.TRACK.value: 3,
            # items.ValidItem.PLAYLIST.value: 0,
            # items.ValidItem.SHOW.value: 0, items.ValidItem.EPISODE.value: 0, items.ValidItem.AUDIOBOOK.value: 0,
        }

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
        graph_key: str,
        restricted_types: List[str] = None,
        max_depth: int = 2,
        **kwargs,
    ) -> str:
        """
        Search from keywords and recursive recommendation. Add results to items.ItemStore

        Args:
            keywords: search keywords
            graph_key: key of the graph it corresponds to in the store
            restricted_types: result items type restriction. All if None.
            max_depth: recommendations start at level 2, inclusive

        Returns:
            id of the graph
        """
        restricted_types = restricted_types or self.all_types
        if restricted_types and set(restricted_types) - set(self.all_types):
            raise ValueError(
                "[Error: SpotifyWrapper.search] "
                f"restricted_types={','.join(restricted_types)} contains illegal values."
                f"Accepted values are {','.join(self.all_types)}"
            )

        # Get spotify results
        query_params = self.__build_search_query(
            keywords=keywords,
            restricted_types=restricted_types,
        )

        if kwargs.get("read_cache"):
            search_results = SpotifyWrapper.read_cache(f"search_{graph_key.lower()}.json")
        else:
            search_results = self.__client.search(**query_params)

        if kwargs.get("write_cache"):
            SpotifyWrapper.cache(f"search_{graph_key.lower()}.json", search_results)

        # Parse and set results to store
        parsed_items = ItemStore().parse_items_from_api_result(
            graph_key=graph_key, search_results=search_results, depth=1, selected_types=restricted_types,
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
            self.find_related(
                graph_key=graph_key,
                item=item,
                depth=2,
                max_depth=max_depth,
                restricted_types=restricted_types,
                **kwargs
            )
        return graph_key

    def find_related(
        self,
        graph_key: str,
        item: items.SpotifyItem,
        depth: int,
        max_depth: int,
        restricted_types: List[str],
        **kwargs
    ):
        """
        Find nodes related to a starting node
        Args:
            graph_key: to get items from store
            item: starting item to find related for
            depth: current depth
            max_depth: maximum depth allowed, inclusive
            restricted_types: level result item type restriction. All if None.
            **kwargs:

        Returns:

        """
        if depth > max_depth:
            return

        relative_rec_weights = [self.type_rec_weight[_type] for _type in restricted_types]
        scaled_rec_weights = {
            _type: scaled_weight
            for _type, scaled_weight in zip(
                restricted_types,
                utils.scale_weights(relative_rec_weights, SpotifyWrapper.REC_SIZE)
            )
        }

        if kwargs.get("read_cache"):
            recommendation_results = SpotifyWrapper.read_cache(f"recommend_{item.id}.json")
        else:
            recommendation_results = self.recommend_from_item(item=item, limit_per_type=scaled_rec_weights)

        if kwargs.get("write_cache"):
            SpotifyWrapper.cache(f"recommend_{item.id}.json", recommendation_results)

        parsed_items = ItemStore().parse_items_from_api_result(
            graph_key=graph_key, search_results=recommendation_results, depth=depth, selected_types=restricted_types,
        )
        ItemStore().relate(
            graph_key=graph_key,
            parent_id=item.id,
            children_ids={parsed_item.id for parsed_item in parsed_items},
            depth=depth,
        )

        for item in parsed_items:
            self.find_related(
                graph_key=graph_key,
                item=item,
                depth=depth+1,
                max_depth=max_depth,
                restricted_types=restricted_types,
            )

    def recommend_from_item(
            self,
            item: items.SpotifyItem,
            limit_per_type: Dict[str, int],
            **kwargs,
    ):
        """
        Get recommendation results from item. Add items to items.ItemStore
        Args:
            item: parsed starting item
            limit_per_type: max results per items type
        """
        all_results = {}
        if limit := limit_per_type.get(items.ValidItem.TRACK.value):
            all_results = utils.dict_extend(all_results, self._recommend_track(
                **item.recommendation_query,
                limit=limit,
                **kwargs,
            ))
        if limit := limit_per_type.get(items.ValidItem.ALBUM.value):
            # get artists
            if item.type == items.ValidItem.ARTIST:
                artist_ids = [item.id]
            elif item.type in (items.ValidItem.ALBUM, items.ValidItem.TRACK):
                artist_ids = [a.id for a in item.artists]
            else:
                raise NotImplementedError(
                    "[Error: SpotifyWrapper.recommend_from_item] "
                    f"Don't know how to find related albums from item of type {item.type.value}"
                )
            # get artists albums
            all_results = utils.dict_extend(
                all_results,
                self._artists_albums(artists_ids=tuple(artist_ids), limit=limit, **kwargs)
            )
        if limit := limit_per_type.get(items.ValidItem.ARTIST.value):
            if item.type == items.ValidItem.ARTIST:
                artist_ids = [item.id]
            elif item.type in (items.ValidItem.ALBUM, items.ValidItem.TRACK):
                artist_ids = [a.id for a in item.artists]
            else:
                raise NotImplementedError(
                    "[Error: SpotifyWrapper.recommend_from_item] "
                    f"Don't know how to find related artists from item of type {item.type.value}"
                )
            all_results = utils.dict_extend(
                all_results,
                self._related_artists(artists_ids=tuple(artist_ids), limit=limit)
            )
        return all_results

    @functools.cache
    def _related_artists(self, artists_ids: Tuple[str], limit: int = 5, **kwargs) -> Dict[str, Any]:
        all_related = functools.reduce(operator.add, [
            self.__client.artist_related_artists(
                artist_id=artists_id,
                **kwargs
            )['artists'] for artists_id in artists_ids
        ])
        return {
            "artists": list({a['id']: a for a in all_related}.values())[:limit]  # removed duplicates
        }

    @functools.cache
    def _artists_albums(self, artists_ids: Tuple[str], limit: int = 5, **kwargs) -> Dict[str, Any]:
        limit_per_artist = utils.scale_weights([1]*min(len(artists_ids), limit), limit)
        limit_per_artist = {
            artist_id: limit_for_artist
            for artist_id, limit_for_artist in zip(
                artists_ids,
                limit_per_artist,
            )
        }
        all_albums = functools.reduce(operator.add, [
            self.__client.artist_albums(
                artist_id=artists_id,
                include_groups="album",
                limit=limit_for_artist,
                **kwargs
            )['items']
            for artists_id, limit_for_artist in limit_per_artist.items()
        ])
        return {
            "albums": list({a['id']: a for a in all_albums}.values())  # removed duplicates
        }

    @functools.cache
    def _recommend_track(
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
            **kwargs,
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
