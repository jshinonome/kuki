import json
import logging
import os
from pathlib import Path
from typing import Dict, List, TypedDict

logger = logging.getLogger()
config_file = "kuki.json"
index_file = "kuki_index.json"
readme_file = "README.md"

package_path = Path.cwd()
readme_path = Path(readme_file)
kuki_config_path = Path(config_file)
kuki_include_path = Path(".kukiinclude")
kuki_index_path = Path(index_file)


class Kuki(TypedDict):
    name: str
    version: str
    description: str
    author: str
    git: str
    dependencies: Dict[str, str]


def generate_json(name: str, description="", author="", git=""):
    if kuki_config_path.exists():
        overwrite = input("kuki.json already exists, overwrite: (yes/No) ").strip()
        if not overwrite or not overwrite.lower() in ["yes"]:
            return
    kuki: Kuki = {
        "name": name,
        "version": "0.0.1",
        "description": description,
        "author": author,
        "git": git,
        "dependencies": {},
    }
    kuki_json = json.dumps(kuki, indent=2)
    logger.info("About to write to {}".format(kuki_config_path))
    logger.info("\n" + kuki_json)
    proceed = input("Is this OK? (YES/no) ").strip()
    if not proceed or proceed.lower() == "yes":
        dump_kuki(kuki)
        readme_path.touch()


def init():
    dir = os.path.basename(os.getcwd())
    package = input("package name: ({}) ".format(dir)).strip()
    if not package:
        package = dir
    description = input("description: ").strip()
    author = input("author: ").strip()
    git = input("git repository: ").strip()

    generate_json(package, description, author, git)


def dump_kuki(kuki: Kuki):
    with open(kuki_config_path, "w") as file:
        file.write(json.dumps(kuki, indent=2))


def exits():
    return kuki_config_path.exists()


def roll_up_version(type: str):
    kuki: Kuki = json.loads(kuki_config_path.read_text())
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
    if kuki_config_path.exists():
        return json.loads(kuki_config_path.read_text())
    else:
        return {}


def load_include() -> List[str]:
    includes = set(["src/*", "lib/*", config_file, readme_file])
    if kuki_include_path.exists():
        with open(kuki_include_path, "r") as file:
            while line := file.readline():
                if line.strip() != "":
                    includes.add(line.strip())
    return includes


def load_readme() -> str:
    with open(readme_path, "r") as file:
        return file.read()


def load_pkg_index() -> Dict[str, Kuki]:
    if kuki_index_path.exists():
        with open(kuki_index_path, "r") as file:
            return json.load(file)
    else:
        return {}


def dump_pkg_index(kuki_index: Dict[str, Kuki]):
    with open(kuki_index_path, "w") as file:
        json.dump(kuki_index, file, indent=2)
