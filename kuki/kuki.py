import argparse
import logging

from . import config_util, package_util, registry_util

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

parser = argparse.ArgumentParser(description="Kdb Ultimate pacKage Installer CLI")

group = parser.add_mutually_exclusive_group()

group.add_argument(
    "-a",
    "--adduser",
    action="store_true",
    default=False,
    help="add an user to the registry site",
)

group.add_argument(
    "-c",
    "--config",
    nargs="+",
    help="config kukirc, use format 'field=value'",
)

group.add_argument(
    "-d",
    "--download",
    type=str,
    help="download a kdb package of latest version, use '@' to specify a version",
)


group.add_argument(
    "-i",
    "--install",
    nargs="*",
    help="install a kdb package of latest version, use '@' to specify a version",
)

group.add_argument(
    "--init",
    action="store_true",
    default=False,
    help="init a kdb package",
)

group.add_argument(
    "--login",
    action="store_true",
    default=False,
    help="login to registry",
)

group.add_argument(
    "-p",
    "--publish",
    action="store_true",
    default=False,
    help="publish a kdb package using kuki.json",
)

group.add_argument(
    "-s",
    "--search",
    type=str,
    help="search a kdb package",
)


group.add_argument(
    "-u",
    "--uninstall",
    nargs="+",
    help="uninstall a kdb package, use '@' to specify a version",
)

group.add_argument(
    "-v",
    "--version",
    choices=["patch", "minor", "major"],
    help="roll up version(patch, minor, major)",
)


def kuki(args):
    if args.config:
        for arg in args.config:
            if "=" in arg:
                field, value = arg.split("=")
                allowed_config_fields = ["token", "registry"]
                if field in allowed_config_fields:
                    config_util.update_config(field, value)
                else:
                    logger.warning("unknown config field: " + field)
                    logger.info("allowed config fields " + ",".join(allowed_config_fields))
            else:
                logger.warning("requires to use '=' to separate field and value")
    elif args.init:
        package_util.init()
    elif args.adduser:
        user = input("Username: ")
        password = input("Password: ")
        email = input("Email: ")
        registry_util.add_user(user, password, email)
    elif args.login:
        user = input("Username: ")
        password = input("Password: ")
        registry_util.login(user, password)
    elif args.search:
        registry_util.search_package(args.search)
    elif args.download:
        registry_util.download_entry(args.download)
    else:
        if not package_util.exits():
            logger.error("kuki.json not found, use 'kuki --init' to init the package first")
            return
        elif args.version:
            package_util.roll_up_version(args.version)
        elif args.publish:
            registry_util.publish_entry()
        elif isinstance(args.install, list):
            registry_util.install_entry(args.install)
        elif args.uninstall:
            registry_util.uninstall_entry(args.uninstall)


def main():
    args = parser.parse_args()
    kuki(args)
