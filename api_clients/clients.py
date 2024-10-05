import spotipy

from config import SPOTIFY_CONF


spotify_client = spotipy.Spotify(
            auth_manager=spotipy.SpotifyClientCredentials(
                client_id=SPOTIFY_CONF["client_id"],
                client_secret=SPOTIFY_CONF["client_secret"],
            )
        )


