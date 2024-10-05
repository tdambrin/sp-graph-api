from pathlib import Path

from commons.utils import load_from_yml

HERE = Path(__file__).parent

CONF = load_from_yml(HERE / "conf.yml")
SPOTIFY_CONF = CONF["SPOTIFY"]

OUTPUT_DIR = HERE / "outputs"
