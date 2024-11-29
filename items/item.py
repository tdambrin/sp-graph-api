"""
Deezer Items classes for parsing, control and styling

Contains:
    - ValiItem: all possible deezer item types
    - DeezerItem (parent class)
    - one class for each deezer item type
"""

from enum import Enum
from typing import Annotated, Any, List

import deezer
from config import NodeColor
from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

# -- Validators --


def is_deezer_resource(v: Any):
    if not isinstance(v, deezer.Resource):
        raise ValueError("not a deezer resource")
    return v


DeezerResource = Annotated[Any, BeforeValidator(is_deezer_resource)]

# -- Classes --


class ValidItem(Enum):
    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    TRACK = "track"
    SHOW = "show"
    EPISODE = "episode"
    AUDIOBOOK = "audiobook"


class ResourceFactory(BaseModel):
    resource: DeezerResource

    @property
    def label(self) -> str:
        if isinstance(self.resource, deezer.Artist):
            return self.resource.name
        if isinstance(self.resource, deezer.Album | deezer.Track):
            return self.resource.title
        if isinstance(self.resource, deezer.Track):
            return self._track_title
        raise NotImplementedError(
            "[ResourceFactory.label]"
            f" {self.resource.__class__} not supported for label property"
        )

    @property
    def title(self) -> str:
        if isinstance(self.resource, deezer.Artist):
            return self._artist_title
        if isinstance(self.resource, deezer.Album):
            return self._album_title
        if isinstance(self.resource, deezer.Track):
            return self._track_title
        raise NotImplementedError(
            "[ResourceFactory.title]"
            f" {self.resource.__class__} not supported for title property"
        )

    @property
    def artist_ids(self) -> List[int]:
        if isinstance(self.resource, deezer.Artist):
            return [self.resource.id]
        if isinstance(self.resource, deezer.Album | deezer.Track):
            return [a.id for a in self.resource.contributors]
        raise NotImplementedError(
            "[ResourceFactory.artist_ids]"
            f" {self.resource.__class__} not supported for artist_ids property"
        )

    @property
    def preview_url(self) -> str | None:
        if isinstance(self.resource, deezer.Track):
            return self.resource.preview
        return None

    @property
    def image(self) -> str | None:
        if isinstance(self.resource, deezer.Artist):
            return self.resource.picture
        if isinstance(self.resource, deezer.Album):
            return self.resource.cover
        if isinstance(self.resource, deezer.Track):
            return None  # no image for tracks
        raise NotImplementedError(
            "[ResourceFactory.image]"
            f" {self.resource.__class__} not supported for image property"
        )

    @property
    def popularity(self) -> int:
        if isinstance(self.resource, deezer.Track):
            return int(self.resource.rank / 1e4)
        if isinstance(self.resource, deezer.Artist):
            return min(
                int(self.resource.nb_fan / 1e3),
                70,
            )
        if isinstance(self.resource, deezer.Album):
            return min(
                int(self.resource.fans / 1e2),
                70,
            )
        raise NotImplementedError(
            "[ResourceFactory.popularity]"
            f" {self.resource.__class__} not supported for popularity property"
        )

    @property
    def node_color(self) -> str:
        return NodeColor.PRIMARY.value  # default

    @property
    def _artist_title(self) -> str:
        return f"Artist - {self.resource.name}"

    @property
    def _album_title(self) -> str:
        return f"Album - {self.resource.title}\n released on {self.resource.release_date}"

    @property
    def _track_title(self) -> str:
        return (
            f"Track - {self.resource.title}\n"
            f"by {','.join([a.name for a in self.resource.contributors])}"
        )
