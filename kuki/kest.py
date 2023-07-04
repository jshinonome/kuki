import json
import logging
import subprocess
import sys
from pathlib import Path

from .util import ENV_DEFAULT, PROCESS_DEFAULT, generate_cmd, generate_options

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
    "environment": ENV_DEFAULT,
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
        logger.info("starting " + cmd)
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            exit(1)


def load_kest():
    if kest_path.exists():
        return json.loads(kest_path.read_text())
    else:
        return KEST_DEFAULT


def main():
    kest(sys.argv[1:])
