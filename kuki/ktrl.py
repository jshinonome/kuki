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

ktrl_path = Path("ktrl.json")

KTRL_DEFAULT = {
    "process": PROCESS_DEFAULT,
    "instance": {
        "module": "",
        "version": "",
        "file": "",
        "dbPath": "",
        "args": [],
    },
    "environment": {
        # source before running
        "envPath": "",
        "qBinary": "q",
        "qHome": "",
        "qLicenseDir": "",
    },
}


def ktrl(args):
    # use ktrl.json if available
    if "-init" in args:
        # generate ktrl.json
        if ktrl_path.exists():
            logger.warn("ktrl.json already exists, skip...")
            return
        with open(ktrl_path, "w") as file:
            json.dump(KTRL_DEFAULT, file, indent=2)
    else:
        ktrl_json = load_ktrl()
        options = generate_options(args, ktrl_json.get("process"))
        # generate run command
        options = ["-kScriptType", "ktrl"] + args + options

        cmd = generate_cmd(options, ktrl_json.get("environment"))
        logger.info(cmd)
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            exit(1)


def generate_cmd(options: List[str], env_cfg: dict[str, str]) -> str:
    q_path = Path.joinpath(Path(__file__).parent, "q", "kuki.q").resolve()
    cmd = []
    if env_cfg:
        if env_cfg.get("envPath"):
            cmd.append("source " + env_cfg.get("env_path"))
        if env_cfg.get("qHome"):
            cmd.append("export QHOME='{}'".format(env_cfg.get("qHome")))
        if env_cfg.get("qLicenseDir"):
            cmd.append("export QLIC='{}'".format(env_cfg.get("qLicenseDir")))
        if env_cfg.get("qBinary"):
            cmd.append(" ".join([env_cfg.get("qBinary"), str(q_path), *options]))
    return ";".join(cmd)


def load_ktrl():
    if ktrl_path.exists():
        return json.loads(ktrl_path.read_text())
    else:
        return KTRL_DEFAULT


def main():
    ktrl(sys.argv[1:])
