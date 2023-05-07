import json
import logging
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger()

config_file = ".kukirc.json"

config_path = Path.joinpath(Path.home(), config_file)


class Kukirc(TypedDict):
    registry: str
    token: str


def load_config() -> Kukirc:
    if not Path.exists(config_path):
        with open(config_path, "w") as file:
            file.write(json.dumps({}))
        return {}
    else:
        with open(config_path, "r") as file:
            return json.load(file)


def update_config(field: str, value: str):
    logger.info("update '{}' of .kukirc".format(field))
    kukirc = load_config()
    kukirc[field] = value
    dump_config(kukirc)


def dump_config(config: Kukirc):
    logger.info("persist update to .kukirc")
    with open(config_path, "w") as file:
        file.write(json.dumps(config, indent=2))
