from pathlib import Path
from enum import Enum

from commons.utils import load_from_yml

PROJECT_ROOT = Path(__file__).parent

CONF = load_from_yml(PROJECT_ROOT / "conf.yml")
SPOTIFY_CONF = CONF["SPOTIFY"]

OUTPUT_DIR = PROJECT_ROOT / "outputs"


class NodeColor(Enum):
    PRIMARY = "#1ed760"
    SECONDARY = "#b1e6c4"
    TERTIARY = "#dddddd"
