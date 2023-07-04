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
    "environment": ENV_DEFAULT,
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
        logger.info("starting " + cmd)
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            exit(1)


def load_ktrl():
    if ktrl_path.exists():
        return json.loads(ktrl_path.read_text())
    else:
        return KTRL_DEFAULT


def main():
    ktrl(sys.argv[1:])
