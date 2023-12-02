import argparse
import getpass
import logging
import sys
import webbrowser
from pathlib import Path

from . import config_util, package_util, registry_util
from . import version as kuki_version

FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger()

parser = argparse.ArgumentParser(
    description="K Ultimate pacKage Installer CLI ({})".format(kuki_version.__version__)
)

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

group.add_argument(
    "-q",
    action="store_true",
    default=False,
    help="print q framework source folder",
)

parser.add_argument(
    "-g",
    "--global",
    action="store_true",
    default=False,
    dest="globalMode",
    help="enable global mode",
)

parser.add_argument(
    "--scope",
    type=str,
    default="@default/",
    help="configure for @scope/, scoped packages",
)

parser.add_argument(
    "--registry",
    type=str,
    default=config_util.DEFAULT_REGISTRY,
    help="the kuki package registry",
)

parser.add_argument(
    "--force",
    action="store_true",
    default=False,
    help="force reinstall",
)


def kuki(args: argparse.Namespace):
    scope: str = args.scope
    if not scope.startswith("@"):
        scope = "@" + scope
    if not scope.endswith("/"):
        scope += "/"
    registry: str = args.registry
    if not registry.endswith("/"):
        registry += "/"

    if args.config:
        for arg in args.config:
            if "=" in arg:
                field, value = arg.split("=")
                allowed_config_fields = ["token", "registry"]
                if field in allowed_config_fields:
                    config_util.update_config(field, value, scope)
                else:
                    logger.warning("unknown config field: " + field)
                    logger.info("allowed config fields " + ",".join(allowed_config_fields))
            else:
                logger.warning("requires to use '=' to separate field and value")
    elif args.init:
        package_util.init()
    elif args.adduser:
        logger.info("Create your account at:")
        logger.info(
            "https://kuki.auth.ap-southeast-2.amazoncognito.com/signup?client_id=6r51ebpp6o14ecqsv8mvn2o160&response_type=code&scope=aws.cognito.signin.user.admin&redirect_uri=https%3A%2F%2Fkuki.ninja"  # noqa: E501
        )
        input("Press ENTER to open in the browser")
        webbrowser.open(
            "https://kuki.auth.ap-southeast-2.amazoncognito.com/signup?client_id=6r51ebpp6o14ecqsv8mvn2o160&response_type=code&scope=aws.cognito.signin.user.admin&redirect_uri=https%3A%2F%2Fkuki.ninja",  # noqa: E501
            new=2,
        )
    elif args.login:
        user = input("Username: ")
        password = getpass.getpass("Password: ")
        registry_util.login(user, password, scope, registry)
    elif args.search:
        registry_util.search_package(args.search, scope)
    elif args.download:
        registry_util.download_entry(args.download)
    elif args.unpublish:
        registry_util.unpublish_package(args.unpublish)
    elif args.q:
        print(Path.joinpath(Path(__file__).parent, "q"))
    else:
        if args.globalMode:
            if isinstance(args.install, list):
                registry_util.install_global_entry(args.install, args.force)
        elif not package_util.exits():
            logger.error("kuki.json not found, use 'kuki --init' to init the package first")
            return
        elif args.version:
            package_util.roll_up_version(args.version)
        elif args.publish:
            registry_util.publish_entry()
        elif args.pack:
            registry_util.pack_entry()
        elif args.install is not None:
            registry_util.install_entry(args.install, args.force)
        elif args.uninstall:
            registry_util.uninstall_entry(args.uninstall)


def main():
    args = parser.parse_args()
    try:
        kuki(args)
    except KeyboardInterrupt:
        sys.exit(0)
