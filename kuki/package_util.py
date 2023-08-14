import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, TypedDict

logger = logging.getLogger()
config_file = "kuki.json"
index_file = "kuki_index.json"
readme_file = "README.md"

package_path = Path.cwd()
readme_path = Path(readme_file)
src_path = Path("src")
package_config_path = Path(config_file)
package_include_path = Path(".kukiinclude")
package_index_path = Path(index_file)


class Repository(TypedDict):
    type: str
    url: str


class Kuki(TypedDict):
    name: str
    version: str
    description: str
    author: str
    repository: Repository
    type: str
    dependencies: Dict[str, str]


def generate_json(name: str, description="", author="", repository="", package_type="q"):
    if package_config_path.exists():
        overwrite = input("kuki.json already exists, overwrite: (yes/No) ").strip()
        if not overwrite or not overwrite.lower() in ["yes"]:
            return
    kuki: Kuki = {
        "name": name,
        "version": "0.0.1",
        "description": description,
        "author": author,
        "repository": {
            "type": "git",
            "url": repository,
        },
        "type": package_type,
        "dependencies": {},
    }
    kuki_json = json.dumps(kuki, indent=2)
    logger.info("About to write to {}".format(package_config_path))
    logger.info("\n" + kuki_json)
    proceed = input("Is this OK? (YES/no) ").strip()
    if not proceed or proceed.lower() == "yes":
        dump_kuki(kuki)
        readme_path.touch()
        readme_path.write_text("# {}\n\n- author: {}\n".format(name, author))
        package_index_path.write_text("{}")
        src_path.mkdir(parents=True, exist_ok=True)


def init():
    dir = os.path.basename(os.getcwd())
    package = input("package name: ({}) ".format(dir.lower())).strip()
    if not package:
        package = dir.lower()

    is_valid_name(package)

    description = input("description: ").strip()
    author = input("author: ").strip()
    repository = input("git repository: ").strip()
    package_type = input("package type: (q)").strip()
    if not package_type:
        package_type = "q"
    if package_type not in ["q", "k", "k9"]:
        logger.error("only support q, k, or k9 package type")
        return

    generate_json(package, description, author, repository, package_type)


def dump_kuki(kuki: Kuki):
    with open(package_config_path, "w") as file:
        file.write(json.dumps(kuki, indent=2))
        file.write("\n")


def exits():
    return package_config_path.exists()


def roll_up_version(type: str):
    kuki: Kuki = json.loads(package_config_path.read_text())
    logger.info("roll up version")
    logger.info("from - " + kuki["version"])
    [major, minor, patch] = list(map(int, kuki["version"].split(".")))
    if type == "patch":
        patch += 1
    elif type == "minor":
        minor += 1
        patch = 0
    elif type == "major":
        major += 1
        minor = 0
        patch = 0
    version = "{}.{}.{}".format(major, minor, patch)
    kuki["version"] = version
    logger.info("to   - " + version)
    dump_kuki(kuki)


def load_kuki() -> Kuki:
    if package_config_path.exists():
        return json.loads(package_config_path.read_text())
    else:
        return {}


def load_include() -> List[str]:
    includes = set(["src/*", "cfg/*", config_file, index_file, readme_file])
    if package_include_path.exists():
        with open(package_include_path, "r") as file:
            while line := file.readline():
                if line.strip() != "":
                    includes.add(line.strip())
    return includes


def load_readme() -> str:
    with open(readme_path, "r") as file:
        return file.read()


def load_pkg_index() -> Dict[str, Kuki]:
    if package_index_path.exists():
        with open(package_index_path, "r") as file:
            return json.load(file)
    else:
        return {}


def dump_pkg_index(kuki_index: Dict[str, Kuki]):
    with open(package_index_path, "w") as file:
        json.dump(kuki_index, file, indent=2)


def is_valid_name(name: str) -> bool:
    if re.fullmatch(r"(@[a-z-]+/)?[a-z-]+", name) is None:
        logger.error("only allows lower cases(a-z) and hyphen(-) as the package name")
        exit(1)
