import functools
import json
import operator
from typing import Any, Dict, List, Optional, Tuple, Union

import commons
import config
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
            items.ValidItem.ALBUM.value,
            items.ValidItem.ARTIST.value,
            items.ValidItem.TRACK.value,
            # items.ValidItem.PLAYLIST.value,
            # items.ValidItem.SHOW.value, items.ValidItem.EPISODE.value, items.ValidItem.AUDIOBOOK.value,
        ]

    @property
    def backbone_priorities(self) -> Dict[str, int]:
        return {
            items.ValidItem.ARTIST.value: 1,
            items.ValidItem.ALBUM.value: 2,
            items.ValidItem.TRACK.value: 3,
        }

    @property
    def type_rec_weight(self) -> Dict[str, int]:
        """Recommendation weight for each type when several possible"""
        return {
            items.ValidItem.ALBUM.value: 1,
            items.ValidItem.ARTIST.value: 1,
            items.ValidItem.TRACK.value: 3,
            # items.ValidItem.PLAYLIST.value: 0,
            # items.ValidItem.SHOW.value: 0, items.ValidItem.EPISODE.value: 0, items.ValidItem.AUDIOBOOK.value: 0,
        }

    @staticmethod
    def cache(name, obj):
        from config import PROJECT_ROOT

        response_dir = PROJECT_ROOT / "responses"
        response_dir.mkdir(parents=True, exist_ok=True)
        with open(response_dir / name, "w") as f:
            json.dump(obj, f)

    @staticmethod
    def read_cache(name):
        from config import PROJECT_ROOT

        return json.load(open(PROJECT_ROOT / "responses" / name, "r"))

    # -- Helpers --

    def get_backbone_type(self, restricted_types: List[str]) -> str:
        """
        Get backbone type out of list of restricted types
        Args:
            restricted_types (List[str]): values from self.all_types

        Returns:
            selected backbone type, one of restricted_types
        """
        candidates = sorted(
            restricted_types, key=lambda type_: self.backbone_priorities[type_]
        )
        return next(iter(candidates))

    # -- Spotify methods --

    def find(
        self,
        item_id: str,
        item_type: Union[items.ValidItem, str],
    ) -> items.SpotifyItem:
        """
        Find an item from Spotify

        Args:
            item_id: id of the item looked for
            item_type: type of the item e.g. album, artist, track

        Returns:
            instance of items.SpotifyItem subclass
        """
        if isinstance(item_type, str):
            item_type = items.ValidItem(item_type)

        valid_types = [
            items.ValidItem.ALBUM.value,
            items.ValidItem.ARTIST.value,
            items.ValidItem.TRACK.value,
        ]
        if item_type.value not in valid_types:
            raise ValueError(
                "[Error: SpotifyWrapper.find] Item type not provided or not in "
                f"{','.join(valid_types)}"
            )

        if item_type == items.ValidItem.ALBUM:
            json_item = self.__client.album(album_id=item_id)
        elif item_type == items.ValidItem.ARTIST:
            json_item = self.__client.artist(artist_id=item_id)
        else:  # item_type == items.ValidItem.TRACK:
            json_item = self.__client.track(track_id=item_id)

        parsed = ItemStore().parse_items_from_list(
            dict_items=[json_item],
            item_type=item_type,
        )
        return parsed[0]

    def search(
        self,
        keywords: List[str],
        session_id: str,
        graph_key: str,
        restricted_types: Optional[List[str]] = None,
        max_depth: int = 2,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Search from keywords and recursive recommendation. Add results to items.ItemStore
        Adding to the store will form a graph whose structure is a backbone of a single type
        and stars of the other types.
        Backbone types priorities are the order of self.all_types

        Args:
            keywords: search keywords
            session_id (str): user session identifier
            graph_key: key of the graph it corresponds to in the store
            restricted_types: result items type restriction. All if None.
            max_depth: recommendations start at level 2, inclusive
            task_id (str): if provided, set intermediate results to task

        Returns:
            id of the graph
        """
        restricted_types = restricted_types or self.all_types

        assert len(set(restricted_types) - set(self.all_types)) == 0, (
            "[Error: SpotifyWrapper.search] "
            f"restricted_types={','.join(restricted_types)} contains illegal values."
            f"Accepted values are {','.join(self.all_types)}"
        )

        backbone_type = self.get_backbone_type(
            restricted_types=restricted_types
        )

        # Get spotify results
        query_params = self.__build_search_query(
            keywords=keywords,
            restricted_types=[backbone_type],
        )

        if kwargs.get("read_cache"):
            search_results = SpotifyWrapper.read_cache(
                f"search_{graph_key.lower()}.json"
            )
        else:
            search_results = self.__client.search(**query_params)

        if kwargs.get("write_cache"):
            SpotifyWrapper.cache(
                f"search_{graph_key.lower()}.json", search_results
            )

        # Parse and set results to store
        parsed_items = ItemStore().parse_items_from_api_result(
            session_id=session_id,
            graph_key=graph_key,
            search_results=search_results,
            depth=1,
            selected_types=restricted_types,
            task_id=task_id,
            is_backbone=True,
        )

        ItemStore().relate(
            session_id=session_id,
            graph_key=graph_key,
            parent_id=graph_key,
            children_ids={parsed_item.id for parsed_item in parsed_items},
            depth=1,
            task_id=task_id,
            is_backbone=True,
            color=config.NodeColor.BACKBONE,
        )

        # Expand search
        if max_depth >= 1:
            for item in parsed_items:
                self.find_related(
                    session_id=session_id,
                    graph_key=graph_key,
                    item=item,
                    depth=2,
                    max_depth=max_depth,
                    backbone_type=backbone_type,
                    star_types=restricted_types,
                    task_id=task_id,
                    **kwargs,
                )

        return graph_key

    def find_related(
        self,
        session_id: str,
        graph_key: str,
        item: items.SpotifyItem,
        depth: int,
        max_depth: int,
        backbone_type: str,
        star_types: List[str],
        task_id: Optional[str] = None,
        exploration_mode: bool = False,
        **kwargs,
    ):
        """
        Find nodes related to a starting node
        Args:
            session_id (str): user session identifier
            graph_key: to get items from store
            item: starting item to find related for
            depth: current depth
            max_depth: maximum depth allowed, inclusive
            backbone_type (str): item type of the backbone
            star_types (List[str)]: types of the star nodes
            task_id (str): if provided, set intermediate results to task
            exploration_mode (str): to avoid getting tracks from the same artists
            **kwargs:

        Returns:

        """
        if depth > max_depth:
            return

        assert backbone_type in self.all_types, (
            "[Error: SpotifyWrapper.find_related] "
            f"Illegal value for backbone type : {backbone_type}. "
            f"Accepted values are {','.join(self.all_types)}"
        )

        # Get backbone extension first
        backbone_extension_result = self.recommend_from_item(
            item=item,
            limit_per_type={backbone_type: 1},
            explorator_mode=exploration_mode,
        )
        backbone_extensions = ItemStore().parse_items_from_api_result(
            session_id=session_id,
            graph_key=graph_key,
            search_results=backbone_extension_result,
            depth=depth,
            selected_types=[backbone_type],
            task_id=task_id,
            is_backbone=True,
        )
        assert len(backbone_extensions) <= 1, (
            "[Error: SpotifyWrapper.find_related] "
            f"Backbone extensions larger than 1: {backbone_extensions}"
            f"From item {item}, limit per type = {backbone_type}: 1"
        )

        ItemStore().relate(
            session_id=session_id,
            graph_key=graph_key,
            parent_id=item.id,
            children_ids={
                parsed_item.id for parsed_item in backbone_extensions
            },
            depth=depth,
            task_id=task_id,
            is_backbone=False,
            color=config.NodeColor.BACKBONE,
        )

        if backbone_extensions:  # bfs
            self.find_related(
                session_id=session_id,
                graph_key=graph_key,
                item=backbone_extensions[0],
                depth=depth + 1,
                max_depth=max_depth,
                backbone_type=backbone_type,
                star_types=star_types,
                task_id=task_id,
                color=config.NodeColor.BACKBONE,
                exploration_mode=exploration_mode,
            )

        # Then get star
        # make sure backbone type not in star types
        star_types = [type_ for type_ in star_types if type_ != backbone_type]

        if star_types:  # If no start type, no star
            relative_rec_weights = [
                self.type_rec_weight[_type] for _type in star_types
            ]
            scaled_rec_weights = {
                _type: scaled_weight
                for _type, scaled_weight in zip(
                    star_types,
                    utils.scale_weights(
                        relative_rec_weights, SpotifyWrapper.REC_SIZE
                    ),
                )
            }

            if kwargs.get("read_cache"):
                recommendation_results = SpotifyWrapper.read_cache(
                    f"recommend_{item.id}.json"
                )
            else:
                recommendation_results = self.recommend_from_item(
                    item=item,
                    limit_per_type=scaled_rec_weights,
                    explorator_mode=exploration_mode,
                )

            if kwargs.get("write_cache"):
                SpotifyWrapper.cache(
                    f"recommend_{item.id}.json", recommendation_results
                )

            # For styling - new group
            random_color = commons.random_color_generator()

            # Parse and add to store
            star_items = ItemStore().parse_items_from_api_result(
                session_id=session_id,
                graph_key=graph_key,
                search_results=recommendation_results,
                depth=depth + 2,
                selected_types=star_types,
                task_id=task_id,
                is_backbone=False,
                color=random_color,
            )

            ItemStore().relate(
                session_id=session_id,
                graph_key=graph_key,
                parent_id=item.id,
                children_ids={parsed_item.id for parsed_item in star_items},
                depth=depth,
                task_id=task_id,
                color=config.NodeColor.BACKBONE,
                hidden=True,
                is_backbone=False,
            )

    def recommend_from_item(
        self,
        item: items.SpotifyItem,
        limit_per_type: Dict[str, int],
        explorator_mode: bool = False,
        **kwargs,
    ):
        """
        Get recommendation results from item. Add items to items.ItemStore
        Args:
            item: parsed starting item
            limit_per_type: max results per items type
            explorator_mode (bool): to avoid getting tracks with same artists
        """
        all_results: Dict[str, Any] = {}
        if limit := limit_per_type.get(items.ValidItem.TRACK.value):
            item_artists_ids = item.get_artists_ids()
            # n_same_artist = ceil(limit / 2) if item_artists_ids else 0
            n_same_artist = limit if not explorator_mode else 0
            if n_same_artist > 0:
                all_results = utils.dict_extend(
                    all_results,
                    self._tracks_from_artists(
                        artists_ids=tuple(item_artists_ids),
                        limit=n_same_artist,
                    ),
                )
            n_other_artists = limit - n_same_artist
            all_results = utils.dict_extend(
                all_results,
                self._recommend_track(
                    **item.recommendation_query,
                    limit=n_other_artists,
                    **kwargs,
                ),
            )
        if limit := limit_per_type.get(items.ValidItem.ALBUM.value):
            # get artists
            if item.type == items.ValidItem.ARTIST:
                artist_ids = [item.id]
            elif item.type in (items.ValidItem.ALBUM, items.ValidItem.TRACK):
                artist_ids = [a.id for a in item.artists]  # type: ignore
            else:
                raise NotImplementedError(
                    "[Error: SpotifyWrapper.recommend_from_item] "
                    f"Don't know how to find related albums from item of type {item.type.value}"
                )
            # get artists albums
            all_results = utils.dict_extend(
                all_results,
                self._artists_albums(
                    artists_ids=tuple(artist_ids), limit=limit, **kwargs
                ),
            )
        if limit := limit_per_type.get(items.ValidItem.ARTIST.value):
            if item.type == items.ValidItem.ARTIST:
                artist_ids = [item.id]
            elif item.type in (items.ValidItem.ALBUM, items.ValidItem.TRACK):
                artist_ids = [a.id for a in item.artists]  # type: ignore
            else:
                raise NotImplementedError(
                    "[Error: SpotifyWrapper.recommend_from_item] "
                    f"Don't know how to find related artists from item of type {item.type.value}"
                )
            all_results = utils.dict_extend(
                all_results,
                self._related_artists(
                    artists_ids=tuple(artist_ids), limit=limit
                ),
            )
        return all_results

    @functools.cache
    def _related_artists(
        self, artists_ids: Tuple[str], limit: int = 5, **kwargs
    ) -> Dict[str, Any]:
        if limit <= 0:
            return {}

        all_related = functools.reduce(
            operator.add,
            [
                self.__client.artist_related_artists(
                    artist_id=artists_id, **kwargs
                )["artists"]
                for artists_id in artists_ids
            ],
        )
        return {
            "artists": list({a["id"]: a for a in all_related}.values())[
                :limit
            ]  # removed duplicates
        }

    @functools.cache
    def _artists_albums(
        self, artists_ids: Tuple[str], limit: int = 5, **kwargs
    ) -> Dict[str, Any]:
        if limit <= 0:
            return {}

        limit_per_artist = utils.scale_weights(
            [1] * min(len(artists_ids), limit), limit
        )
        limit_per_artist = {
            artist_id: limit_for_artist
            for artist_id, limit_for_artist in zip(
                artists_ids,
                limit_per_artist,
            )
        }
        all_albums = functools.reduce(
            operator.add,
            [
                self.__client.artist_albums(
                    artist_id=artists_id,
                    include_groups="album",
                    limit=limit_for_artist,
                    **kwargs,
                )["items"]
                for artists_id, limit_for_artist in limit_per_artist.items()
            ],
        )
        return {
            "albums": list(
                {a["id"]: a for a in all_albums}.values()
            )  # removed duplicates
        }

    @functools.cache
    def _tracks_from_artists(
        self, artists_ids: Tuple[str], limit: int = 5, **kwargs
    ) -> Dict[str, Any]:
        if limit <= 0:
            return {}

        limit_per_artist = utils.scale_weights(
            [1] * min(len(artists_ids), limit), limit
        )
        limit_per_artist = {
            artist_id: limit_for_artist
            for artist_id, limit_for_artist in zip(
                artists_ids,
                limit_per_artist,
            )
        }
        all_tracks = functools.reduce(
            operator.add,
            [
                self.__client.artist_top_tracks(
                    artist_id=artists_id,
                    **kwargs,
                )["tracks"][:limit_for_artist]
                for artists_id, limit_for_artist in limit_per_artist.items()
            ],
        )
        return {
            "tracks": list(
                {t["id"]: t for t in all_tracks}.values()
            )  # removed duplicates
        }

    @functools.cache
    def _recommend_track(
        self,
        seed_artists: Optional[Tuple[items.Artist]] = None,
        seed_genres: Optional[Tuple[str]] = None,
        seed_tracks: Optional[Tuple[items.Track]] = None,
        limit: int = 5,
        **kwargs,
    ) -> Dict[str, Any]:
        if limit <= 0:
            return {}

        return self.__client.recommendations(
            seed_artists=(
                [a.id for a in seed_artists][:5] if seed_artists else None
            ),
            seed_genres=seed_genres[:5] if seed_genres else None,
            seed_tracks=(
                [t.id for t in seed_tracks][:5] if seed_tracks else None
            ),
            limit=limit,
            **kwargs,
        )

    @staticmethod
    def __build_search_query(
        keywords: List[str],
        restricted_types: Optional[List[str]] = None,
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
        return self.__client.search(q="khruangbin", limit=20)
