import getpass
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, TypedDict

DEFAULT_REGISTRY = "https://www.kuki.ninja/"

DEFAULT_SCOPE = "@default/"

logger = logging.getLogger()

global_kuki_root = (
    Path(os.getenv("KUKIPATH")) if os.getenv("KUKIPATH") else Path.joinpath(Path.home(), "kuki")
)

global_config_dir = Path.joinpath(global_kuki_root, "_config")

global_config_dir.mkdir(parents=True, exist_ok=True)

config_file = "kukirc.json"

global_config_path = Path.joinpath(global_config_dir, config_file)


class RegistryCfg(TypedDict):
    registry: str
    token: str
    user: str


# registry, token, user
def get_reg_cfg(scope=DEFAULT_SCOPE) -> (str, str, str):
    kukirc: Dict[str, RegistryCfg] = load_config()
    if scope in kukirc:
        reg_cfg = kukirc.get(scope, {})
    else:
        reg_cfg = kukirc.get(DEFAULT_SCOPE, {})
    reg: str = reg_cfg.get("registry", DEFAULT_REGISTRY)
    reg.endswith("/")
    return (
        reg if reg.endswith("/") else reg + "/",
        reg_cfg.get("token", ""),
        reg_cfg.get("user", getpass.getuser()),
    )


def load_config() -> Dict[str, RegistryCfg]:
    if not Path.exists(global_config_path):
        with open(global_config_path, "w") as file:
            file.write(json.dumps({}))
        return {}
    else:
        with open(global_config_path, "r") as file:
            return json.load(file)


def validate_scope(scope: str) -> bool:
    pattern = r"(@[a-z-]+/)"
    if re.fullmatch(pattern, scope):
        return True
    else:
        logger.error("only allows lower cases(a-z) and hyphen(-) as the scope name")
        exit(1)


def update_config(field: str, value: str, scope: str):
    validate_scope(scope)
    kukirc: Dict[str, RegistryCfg] = load_config()
    if scope in kukirc:
        kukirc.setdefault(scope, ())
        reg_cfg = kukirc.get(scope)
    else:
        kukirc.setdefault(scope, {})
        reg_cfg = kukirc.get(scope)
    if not value:
        logger.info("Empty value for {}, removing existing value".format(field))
        if field in reg_cfg:
            reg_cfg.pop(field)
    else:
        logger.info("update '{}' of {}".format(field, config_file))
        reg_cfg[field] = value
    dump_config(kukirc)


def dump_config(config):
    logger.info("persist update to {}".format(config_file))
    with open(global_config_path, "w") as file:
        file.write(json.dumps(config, indent=2))
