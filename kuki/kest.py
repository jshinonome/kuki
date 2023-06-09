import argparse
import json
import logging
from pathlib import Path

from .util import PROCESS_DEFAULT, generate_cmd

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

kest_path = Path("kest.json")

parser = argparse.ArgumentParser(description="K tEST CLI")

parser.add_argument(
    "-i",
    "--init",
    action="store_true",
    default=False,
    help="initialize kest.json",
)

parser.add_argument(
    "-c",
    "--consoleSize",
    dest="console_size",
    nargs=2,
    default=[50, 160],
    type=int,
    help="console maximum rows and columns",
)


parser.add_argument(
    "-e",
    "--errorTraps",
    dest="error_traps",
    type=str,
    default="none",
    choices=["none", "suspend", "dump"],
    help="error-trapping mode",
)

parser.add_argument(
    "--tls",
    type=str,
    default="plain",
    choices=["plain", "mixed", "tls"],
    help="TLS server mode",
)

parser.add_argument(
    "-g",
    "--gc",
    dest="garbage_collection",
    type=str,
    default="deferred",
    choices=["deferred", "immediate"],
    help="garbage collection mode",
)

parser.add_argument(
    "-o",
    "--offsetTime",
    dest="offset_time",
    type=int,
    default=0,
    help="offset from UTC",
)

parser.add_argument(
    "-p",
    "--port",
    type=int,
    default=31800,
    help="listening port",
)

parser.add_argument(
    "-P",
    "--precision",
    type=int,
    default=7,
    help="display precision",
)

parser.add_argument(
    "-q",
    "--quiet",
    action="store_true",
    default=False,
    help="quiet mode",
)

parser.add_argument(
    "-s",
    "--threads",
    type=int,
    default=0,
    help="number of threads or processes available for parallel processing",
)

parser.add_argument(
    "-t",
    "--timerPeriod",
    dest="timer_period",
    type=int,
    default=0,
    help="timer period in milliseconds",
)

parser.add_argument(
    "--timeout",
    type=int,
    default=0,
    help="timeout in seconds for client queries",
)

parser.add_argument(
    "-w",
    "--memoryLimit",
    dest="memory_limit",
    type=int,
    default=0,
    help="memory limit in MB",
)


KEST_DEFAULT = {
    "process": PROCESS_DEFAULT,
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
    if args.init:
        # generate kest.json
        with open(kest_path, "w") as file:
            json.dump(KEST_DEFAULT, file, indent=2)
    else:
        cmd = generate_cmd(args)

        logger.info(args)

        # generate run command
        logger.info(cmd)


def main():
    args = parser.parse_args()
    kest(args)
