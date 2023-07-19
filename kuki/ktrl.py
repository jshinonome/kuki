import argparse
import logging

from . import ktrl_util
from .package_util import package_config_path

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

parser = argparse.ArgumentParser(description="K conTRoL CLI")

parser.add_argument(
    "-g",
    "--global",
    action="store_true",
    default=False,
    dest="globalMode",
    help="enable global mode",
)

parser.add_argument(
    "--profile",
    type=str,
    help="profile name",
)

parser.add_argument(
    "--process",
    type=str,
    help="process name",
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    "-l",
    "--list",
    choices=["profile", "process"],
    help="list all profiles or all processes",
)

group.add_argument(
    "-c",
    "--config",
    action="store_true",
    default=False,
    help="config profile or process",
)

group.add_argument(
    "-s",
    "--start",
    action="store_true",
    default=False,
    help="start a specified process with a specified profile",
)


def ktrl(args: argparse.Namespace):
    if not args.globalMode and not package_config_path.exists():
        logger.error("'ktrl' in local mode must be executed from the project root")
        return
    if args.config:
        if args.profile:
            ktrl_util.config_file(args.profile, "profile", args.globalMode)
        elif args.process:
            ktrl_util.config_file(args.process, "process", args.globalMode)
        else:
            logger.error("requires --profile or --process name")

    elif args.list:
        ktrl_util.list_config(args.list, args.globalMode)

    elif args.start:
        if args.profile and args.process:
            ktrl_util.start(args.profile, args.process, args.globalMode)
        else:
            logger.error("requires --profile name and --process name")


def main():
    args = parser.parse_args()
    ktrl(args)
