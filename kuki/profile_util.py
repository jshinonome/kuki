import logging
from pathlib import Path

from . import config_util

logger = logging.getLogger()

global_profile_dir = Path.joinpath(config_util.global_kuki_root, "_profile")


def config(profile_name: str):
    pass


def start(profile_name: str):
    logger.info(profile_name)
