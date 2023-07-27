import argparse
import getpass
import logging

from . import config_util, package_util, registry_util

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

parser = argparse.ArgumentParser(description="K Ultimate pacKage Installer CLI")

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
    help="download a q/k package of latest version, use '@' to specify a version",
)


group.add_argument(
    "-i",
    "--install",
    nargs="*",
    help="install a q/k package of latest version, use '@' to specify a version",
)

group.add_argument(
    "--init",
    action="store_true",
    default=False,
    help="init a q/k package",
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
    help="publish a q/k package using kuki.json",
)

group.add_argument(
    "--unpublish",
    type=str,
    help="unpublish a q/k package",
)


group.add_argument(
    "--pack",
    action="store_true",
    default=False,
    help="pack a q/k package using kuki.json",
)

group.add_argument(
    "-s",
    "--search",
    type=str,
    help="search a q/k package",
)


group.add_argument(
    "-u",
    "--uninstall",
    nargs="+",
    help="uninstall a q/k package, use '@' to specify a version",
)

group.add_argument(
    "-v",
    "--version",
    choices=["patch", "minor", "major"],
    help="roll up version(patch, minor, major)",
)


parser.add_argument(
    "-g",
    "--global",
    action="store_true",
    default=False,
    dest="globalMode",
    help="enable global mode",
)


def kuki(args: argparse.Namespace):
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
        password = getpass.getpass("Password: ")
        confirmed_pass = getpass.getpass("Confirm password: ")
        if confirmed_pass != password:
            logger.info("Password doesn't match, Try again")
            return
        email = input("Email: ")
        logger.info("About to register '{}' with '{}'".format(user, password))
        proceed = input("Is this OK? (yes/no) ").strip()
        if proceed.lower() == "yes":
            registry_util.add_user(user, password, email)
        else:
            logger.info("Abort registering '{}'".format(user))
    elif args.login:
        user = input("Username: ")
        password = getpass.getpass("Password: ")
        registry_util.login(user, password)
    elif args.search:
        registry_util.search_package(args.search)
    elif args.download:
        registry_util.download_entry(args.download)
    elif args.unpublish:
        registry_util.unpublish_package(args.unpublish)
    else:
        if args.globalMode:
            if isinstance(args.install, list):
                for pkg in args.install:
                    if pkg.startswith("."):
                        registry_util.install_local_package(pkg, False, True)
                    else:
                        registry_util.install_package(pkg, False, True)
                    registry_util.dump_global_index()
        elif not package_util.exits():
            logger.error("kuki.json not found, use 'kuki --init' to init the package first")
            return
        elif args.version:
            package_util.roll_up_version(args.version)
        elif args.publish:
            registry_util.publish_entry()
        elif args.pack:
            registry_util.pack_entry()
        elif isinstance(args.install, list):
            registry_util.install_entry(args.install)
        elif args.uninstall:
            registry_util.uninstall_entry(args.uninstall)


def main():
    args = parser.parse_args()
    kuki(args)
