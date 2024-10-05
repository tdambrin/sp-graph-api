import functools
from operator import add
from abc import abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

import spotipy
from pydantic import BaseModel

from api_clients import spotify_client
from commons import dict_extend
from config import SPOTIFY_CONF


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

    @abstractmethod
    def recommendation_query(self) -> Dict[str, Any]:
        raise NotImplementedError


class Artist(SpotifyItem):
    genres: Optional[List[str]] = None

    def model_post_init(self, __context__):
        if self.genres:
            return

        api_result = spotify_client.artist(self.id)
        if api_result:
            self.genres = api_result.get("genres")

    def recommendation_query(self) -> Dict[str, Any]:
        return {
            "seed_artists": [self],
            # "seed_genres": self.genres
        }


class Album(SpotifyItem):
    release_date: str
    artists: List[Artist]

    def recommendation_query(self) -> Dict[str, Any]:
        return {
            "seed_artists": self.artists,
            # "seed_genres": functools.reduce(add, [a.genres for a in self.artists], [])
        }


class Playlist(SpotifyItem):
    description: str
    preview_url: Optional[str] = None

    @property
    def genres(self):
        client = spotipy.Spotify(
            auth_manager=spotipy.SpotifyClientCredentials(
                client_id=SPOTIFY_CONF["client_id"],
                client_secret=SPOTIFY_CONF["client_secret"],
            )
        )
        api_result = client.playlist_items(self.id)["tracks"].get("items")
        if not api_result:
            return []
        artists = [Artist(**artist_info) for artist_info in api_result.get('track', {}).get("artists", [])]
        return functools.reduce(add, [a.genres for a in artists], [])

    def recommendation_query(self) -> Dict[str, Any]:
        return {
            "seed_genres": self.genres
        }


class Track(SpotifyItem):
    album: Optional[Album] = None
    artists: List[Artist]
    preview_url: Optional[str] = None

    def recommendation_query(self) -> Dict[str, Any]:
        # album_rec_query = self.album.recommendation_query() if self.album else {}
        # artist_rec_queries = dict_extend(*[a.recommendation_query() for a in self.artists])
        seed_tracks = {"seed_tracks": [self]}
        return seed_tracks  # dict_extend(album_rec_query, artist_rec_queries, seed_tracks)
