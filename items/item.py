"""
Deezer Items classes for parsing, control and styling

Contains:
    - ValiItem: all possible deezer item types
    - DeezerItem (parent class)
    - one class for each deezer item type
"""

from enum import Enum
from typing import Annotated, Any, Dict, List

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


# -- Utils --


class ValidItem(Enum):  # should match deezer types
    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    TRACK = "track"
    SHOW = "show"
    EPISODE = "episode"
    AUDIOBOOK = "audiobook"


POPULARITY_THRESHOLDS: Dict[str, int] = {
    ValidItem.ARTIST.value: int(2e4),
    ValidItem.ALBUM.value: int(2e3),
    ValidItem.TRACK.value: int(1e4),
}

POPULARITY_UPPERS: Dict[str, int] = {
    ValidItem.ARTIST.value: int(12e6),  # Taylor Swift (2023)
    ValidItem.ALBUM.value: int(2e5),  # Bad Bunny - Un Verano Sin Ti (2023)
    ValidItem.TRACK.value: int(1e6),  # Known upper limit
}

# -- Classes --


class ResourceFactory(BaseModel):
    resource: DeezerResource

    def get_target_label(self, target_type: ValidItem) -> str:
        """
        Get label of target_type from another type.
        E.g. get artist name from self.resource being a track
        Args:
            target_type (ValidItem): label should be one of this type

        Returns:
            label as string
        """
        if self.resource.type == target_type.value:
            return self.label

        if target_type == ValidItem.ALBUM:
            if isinstance(self.resource, deezer.Artist):
                # first album name
                return ResourceFactory(
                    resource=self.resource.get_albums(limit=1)[0]
                ).label
            if isinstance(self.resource, deezer.Track):
                return ResourceFactory(resource=self.resource.album).label

        if target_type == ValidItem.ARTIST:
            if isinstance(self.resource, deezer.Album):
                return ResourceFactory(resource=self.resource.artist).label
            if isinstance(self.resource, deezer.Track):
                return ResourceFactory(resource=self.resource.artist).label

        if target_type == ValidItem.TRACK:
            if isinstance(self.resource, deezer.Album):
                return ResourceFactory(resource=self.resource.tracks[0]).label
            if isinstance(self.resource, deezer.Artist):
                return ResourceFactory(
                    resource=self.resource.get_top(limit=1)[0]
                ).label

        raise NotImplementedError(
            "[ResourceFactory.get_target_label]"
            f" Target type {target_type.value} not supported"
            f" for resource of type {self.resource.type}"
        )

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
    def full_name(self):
        name = self.label
        if isinstance(self.resource, deezer.Album):
            artist_names = [c.name for c in self.resource.contributors]
            return f"{name} {' '.join(artist_names)}"
        if isinstance(self.resource, deezer.Track):
            artist_names = [c.name for c in self.resource.contributors]
            album_name = self.resource.album.label
            return f"{name} {' '.join(artist_names)} {album_name}"
        return name  # Artist

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
            return self.resource.picture_medium
        if isinstance(self.resource, deezer.Album):
            return self.resource.cover_medium
        if isinstance(self.resource, deezer.Track):
            return None  # no image for tracks
        raise NotImplementedError(
            "[ResourceFactory.image]"
            f" {self.resource.__class__} not supported for image property"
        )

    @property
    def popularity_indicator(self) -> int:
        if isinstance(self.resource, deezer.Track):
            return self.resource.rank
        if isinstance(self.resource, deezer.Artist):
            return self.resource.nb_fan
        if isinstance(self.resource, deezer.Album):
            return self.resource.fans

        raise NotImplementedError(
            "[ResourceFactory.popularity_indicator]"
            f" {self.resource.__class__} not supported for popularity property"
        )

    @property
    def popularity_upper(self):
        return POPULARITY_UPPERS[self.resource.type]

    @property
    def popularity_distance(self) -> int:
        return self.popularity_indicator - self.popularity_threshold

    @property
    def popularity(self) -> int:  # fixMe - not very contrasted
        """is a percent"""
        return int(self.popularity_indicator / self.popularity_upper * 100)

    @property
    def popularity_threshold(self) -> int:
        return POPULARITY_THRESHOLDS[self.resource.type]

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
