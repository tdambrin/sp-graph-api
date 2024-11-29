from enum import Enum
from pathlib import Path

from commons.utils import load_from_yml

# --- Utils and Config ---
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# -- conf.yml ---

CONF = load_from_yml(PROJECT_ROOT / "conf.yml")

# --- API ---
API_HOST = CONF.get("DZG_API_HOST", "localhost")
API_PORT = int(CONF.get("DZG_API_PORT", 8502)) or None


# --- Styling ---

EDGE_WIDTH = 10


class NodeColor(Enum):
    PRIMARY = "#ff673d"
    SECONDARY = "#b1e6c4"
    TERTIARY = "#dddddd"
    BACKBONE = "#dddddd"
