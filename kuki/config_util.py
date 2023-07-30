import json
import logging
import os
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger()

global_kuki_root = (
    Path(os.getenv("KUKIPATH")) if os.getenv("KUKIPATH") else Path.joinpath(Path.home(), "kuki")
)

global_config_dir = Path.joinpath(global_kuki_root, "_config")

global_config_dir.mkdir(parents=True, exist_ok=True)

config_file = "kukirc.json"

global_config_path = Path.joinpath(global_config_dir, config_file)


class Kukirc(TypedDict):
    registry: str
    token: str


def load_config() -> Kukirc:
    if not Path.exists(global_config_path):
        with open(global_config_path, "w") as file:
            file.write(json.dumps({}))
        return {}
    else:
        with open(global_config_path, "r") as file:
            return json.load(file)


def update_config(field: str, value: str):
    if not value:
        kukirc = load_config()
        delattr(kukirc, field)
        logger.info("Empty value for {}, removing existing value".format(field))
    else:
        logger.info("update '{}' of {}".format(field, config_file))
        kukirc = load_config()
        kukirc[field] = value
    dump_config(kukirc)


def dump_config(config: Kukirc):
    logger.info("persist update to {}".format(config_file))
    with open(global_config_path, "w") as file:
        file.write(json.dumps(config, indent=2))
