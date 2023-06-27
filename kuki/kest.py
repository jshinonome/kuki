import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import List

from .util import PROCESS_DEFAULT, generate_options

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

kest_path = Path("kest.json")

kest_process_default = PROCESS_DEFAULT.copy()

kest_process_default.pop("blocked")
kest_process_default.pop("replicate")
kest_process_default.pop("disable_system_cmd")

KEST_DEFAULT = {
    "process": kest_process_default,
    "environment": {
        # source before running
        "env_path": "",
        "q_binary": "q",
        "q_home": "",
        "q_license_dir": "",
    },
}


def kest(args):
    # use kest.json if available
    if "-init" in args:
        # generate kest.json
        if kest_path.exists():
            logger.warn("kest.json already exists, skip...")
            return
        with open(kest_path, "w") as file:
            json.dump(KEST_DEFAULT, file, indent=2)
    else:
        kest_json = load_kest()
        options = generate_options(args, kest_json.get("process"))
        # generate run command
        options = ["-kScriptType", "kest"] + args + options

        cmd = generate_cmd(options, kest_json.get("environment"))
        logger.info(cmd)
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            exit(1)


def generate_cmd(options: List[str], env_cfg: dict[str, str]) -> str:
    q_path = Path.joinpath(Path(__file__).parent, "q", "kuki.q").resolve()
    cmd = []
    if env_cfg:
        if env_cfg.get("env_path"):
            cmd.append("source " + env_cfg.get("env_path"))
        if env_cfg.get("q_home"):
            cmd.append("export QHOME='{}'".format(env_cfg.get("q_home")))
        if env_cfg.get("q_license_dir"):
            cmd.append("export QLIC='{}'".format(env_cfg.get("q_license_dir")))
        if env_cfg.get("q_binary"):
            cmd.append(" ".join([env_cfg.get("q_binary"), str(q_path), *options]))
    return ";".join(cmd)


def load_kest():
    if kest_path.exists():
        return json.loads(kest_path.read_text())
    else:
        return KEST_DEFAULT


def main():
    kest(sys.argv[1:])
