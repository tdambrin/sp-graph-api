import os
import sys
from enum import Enum
from pathlib import Path

from dotenv import dotenv_values

# --- Env vars ---

env_flag_idx = next((i for i, x in enumerate(sys.argv) if x in ["-e", "--env"]), None)
if (
    env_flag_idx is not None and len(sys.argv) > env_flag_idx + 1
):  # flag is there and env follows
    env_name = sys.argv[env_flag_idx + 1]  # env follows flag
    if env_name != "local":
        raise ValueError(f"[config] {env_name} is not a valid .env file extension")
    dotenv_path = Path(f".env.{env_name}")  # local
else:
    dotenv_path = Path(f".env")  # prod

if not dotenv_path.is_file():
    CONF = os.environ
else:
    print(f"Loading env from {str(dotenv_path)}")
    CONF = dotenv_values(dotenv_path)
SPOTIFY_CLIENT = CONF.get("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET = CONF.get("SPOTIFY_CLIENT_SECRET")

# --- API ---
API_HOST = CONF.get("SPG_API_HOST")
API_PORT = int(CONF.get("SPG_API_PORT", "0")) or None


# --- Utils and Config ---
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"


class NodeColor(Enum):
    PRIMARY = "#1ed760"
    SECONDARY = "#b1e6c4"
    TERTIARY = "#dddddd"
