import argparse
import json
import logging
import subprocess
from pathlib import Path
from typing import List

from .util import PROCESS_DEFAULT, generate_options

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

kest_path = Path("kest.json")

parser = argparse.ArgumentParser(description="K tEST CLI")

parser.add_argument(
    "--debug",
    action="store_true",
    default=False,
    help="test in debug mode",
)

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
    help="offset from UTC in hours",
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
    "--testRoot",
    type=str,
    default="test",
    help="directory that kest use to search for test files in",
)

parser.add_argument(
    "--testOutputFile",
    type=str,
    default="",
    help="write test results to a file",
)

parser.add_argument(
    "--testPattern",
    type=str,
    default="*",
    help="run only tests with a name that matches the pattern",
)

parser.add_argument(
    "--testFile",
    type=str,
    default="",
    help="run specific test file",
)

parser.add_argument(
    "-w",
    "--memoryLimit",
    dest="memory_limit",
    type=int,
    default=0,
    help="memory limit in MB",
)

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
    if args.init:
        # generate kest.json
        if kest_path.exists():
            logger.warn("kest.json already exists, skip...")
            return
        with open(kest_path, "w") as file:
            json.dump(KEST_DEFAULT, file, indent=2)
    else:
        options = generate_options(args)
        # generate run command
        options = ["-kScriptType", "kest"] + options

        cmd = generate_cmd(options)
        logger.info(cmd)
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            exit(1)


def generate_cmd(options: List[str]) -> str:
    q_path = Path.joinpath(Path(__file__).parent, "q", "kuki.q").resolve()
    kest_json = load_kest()
    env_conf = kest_json.get("environment")
    cmd = []
    if env_conf:
        if env_conf.get("env_path"):
            cmd.append("source " + env_conf.get("env_path"))
        if env_conf.get("q_home"):
            cmd.append("export QHOME='{}'".format(env_conf.get("q_home")))
        if env_conf.get("q_license_dir"):
            cmd.append("export QLIC='{}'".format(env_conf.get("q_license_dir")))
        if env_conf.get("q_binary"):
            cmd.append(" ".join([env_conf.get("q_binary"), str(q_path), *options]))
    return ";".join(cmd)


def load_kest():
    if kest_path.exists():
        return json.loads(kest_path.read_text())
    else:
        return KEST_DEFAULT


def main():
    args = parser.parse_args()
    kest(args)
