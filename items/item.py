"""
Spotify Items classes for parsing, control and styling

Contains:
    - ValiItem: all possible spotify item types
    - SpotifyItems (parent class)
    - one class for each spotify item type
"""


import functools
from operator import add
from abc import abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from functools import cached_property

from pydantic import BaseModel

from api_clients import spotify_client
from config import NodeColor


class ValidItem(Enum):
    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    TRACK = "track"
    SHOW = "show"
    EPISODE = "episode"
    AUDIOBOOK = "audiobook"


class SpotifyItem(BaseModel):
    type: ValidItem
    name: str
    id: str
    href: str
    external_urls: Dict[str, str]
    images: Optional[List[Dict[str, Any]]] = None

    def __hash__(self):
        return self.id.__hash__()

    @abstractmethod
    def recommendation_query(self) -> Dict[str, Any]:
        """
        Args for wrappers.SpotifyWrapper._recommend(..)
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def node_color(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError


class Artist(SpotifyItem):
    genres: Optional[List[str]] = None

    def model_post_init(self, __context__):
        if self.genres:
            return

        # from config import PROJECT_ROOT
        # import json
        # with open(PROJECT_ROOT / "responses" / f"artist_{self.id}", 'r') as f:
        #     api_result = json.load(f)
        # with open(PROJECT_ROOT / "responses" / f"artist_{self.id}", "w") as f:
        #     json.dump(api_result, f)

        api_result = spotify_client.artist(self.id)
        if api_result:
            self.genres = api_result.get("genres")

    def recommendation_query(self) -> Dict[str, Any]:
        return {
            "seed_artists": tuple([self]),
            # "seed_genres": self.genres
        }

    @property
    def node_color(self) -> str:
        return NodeColor.PRIMARY.value

    @property
    def title(self) -> str:
        return f"Artist - {self.name}"


class Album(SpotifyItem):
    release_date: str
    artists: List[Artist]

    def recommendation_query(self) -> Dict[str, Any]:
        return {
            "seed_artists": tuple(self.artists),
            # "seed_genres": functools.reduce(add, [a.genres for a in self.artists], [])
        }

    @property
    def node_color(self) -> str:
        return NodeColor.TERTIARY.value

    @property
    def title(self) -> str:
        return (
            f"Album - {self.name}\n"
            f"released on {self.release_date}"
        )


class Playlist(SpotifyItem):
    description: str
    preview_url: Optional[str] = None

    @cached_property
    @property
    def genres(self):
        api_result = spotify_client.playlist_items(self.id)["tracks"].get("items")
        # from config import PROJECT_ROOT
        # import json
        # with open(PROJECT_ROOT / "responses" / f"playlist_items_{self.id}", "w") as f:
        #     json.dump(api_result, f)
        if not api_result:
            return []
        artists = [Artist(**artist_info) for artist_info in api_result.get('track', {}).get("artists", [])]
        return functools.reduce(add, [a.genres for a in artists], [])

    def recommendation_query(self) -> Dict[str, Any]:
        return {
            "seed_genres": tuple(self.genres),
        }

    @property
    def node_color(self) -> str:
        return NodeColor.TERTIARY.value

    @property
    def title(self) -> str:
        return f"Playlist - {self.name}\n"


class Track(SpotifyItem):
    album: Optional[Album] = None
    artists: List[Artist]
    preview_url: Optional[str] = None

    def recommendation_query(self) -> Dict[str, Any]:
        # album_rec_query = self.album.recommendation_query() if self.album else {}
        # artist_rec_queries = dict_extend(*[a.recommendation_query() for a in self.artists])
        seed_tracks = {"seed_tracks": tuple([self])}
        return seed_tracks  # dict_extend(album_rec_query, artist_rec_queries, seed_tracks)

    @property
    def node_color(self) -> str:
        return NodeColor.SECONDARY.value

    @property
    def title(self) -> str:
        return (
            f"Track - {self.name}\n"
            f"by {','.join([a.name for a in self.artists])}"
        )
