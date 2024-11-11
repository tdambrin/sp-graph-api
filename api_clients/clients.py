import config
import spotipy  # type: ignore

spotify_client = spotipy.Spotify(
    auth_manager=spotipy.SpotifyClientCredentials(
        client_id=config.SPOTIFY_CLIENT,
        client_secret=config.SPOTIFY_SECRET,
    )
)
