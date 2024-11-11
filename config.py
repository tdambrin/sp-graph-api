from enum import Enum
from pathlib import Path

from commons.utils import load_from_yml

# --- Utils and Config ---
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

CONF = load_from_yml(PROJECT_ROOT / "conf.yml")
# SPOTIFY_CONF = CONF["SPOTIFY"]

dotenv_path = Path(".env")
if dotenv_path.is_file():
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=dotenv_path)


class NodeColor(Enum):
    PRIMARY = "#1ed760"
    SECONDARY = "#b1e6c4"
    TERTIARY = "#dddddd"


# --- API ---
API_HOST = "127.0.0.1"
API_PORT = 8502
