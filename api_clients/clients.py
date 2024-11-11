import os

import spotipy  # type: ignore

# from config import SPOTIFY_CONF

spotify_client = spotipy.Spotify(
    auth_manager=spotipy.SpotifyClientCredentials(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),  # SPOTIFY_CONF["client_id"],
        client_secret=os.environ.get(
            "SPOTIFY_CLIENT_SECRET"
        ),  # SPOTIFY_CONF["client_secret"],
    )
)
