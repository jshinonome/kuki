import base64
import glob
import hashlib
import json
import logging
import os
import shutil
import tarfile
from pathlib import Path
from typing import Dict, List, TypedDict

import requests
from requests.auth import HTTPBasicAuth

from . import config_util, package_util

logger = logging.getLogger()
config = config_util.load_config()
registry = config.get("registry", "http://0.0.0.0:4873/")
token = config.get("token", "")

global_repo_path = (
    Path(os.getenv("KUKIPATH")) if os.getenv("KUKIPATH") else Path.joinpath(Path.home(), "kuki")
)

global_cache_path = Path.joinpath(global_repo_path, ".cache")
global_index_path = Path.joinpath(global_repo_path, ".index")

kuki_json = package_util.load_kuki()

if global_cache_path.exists() and not global_cache_path.is_dir():
    os.remove(str(global_cache_path))

global_cache_path.mkdir(parents=True, exist_ok=True)

user_url = registry + "-/user/org.couchdb.user:"
search_url = registry + "-/v1/search?text={}"

package_index = package_util.load_pkg_index()


class Metadata(TypedDict):
    name: str
    version: str
    dist: any
    dependencies: any


def load_global_index() -> Dict[str, package_util.Kuki]:
    if global_index_path.exists():
        with open(global_index_path, "r") as file:
            return json.load(file)
    else:
        return {}


global_index = load_global_index()


def add_user(user: str, password: str, email: str):
    payload = {"name": user, "password": password, "email": email}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    res = requests.put(user_url + user, json.dumps(payload), headers=headers)

    if res.status_code == 201:
        logger.info("the user '{}' has been added".format(user))
        token = res.json()["token"]
        config_util.update_config("token", token)
    else:
        logger.error("failed to add user: " + user)
        logger.error("status code: {}, error: {}".format(res.status_code, res.json()["error"]))


def login(user: str, password: str):
    basic_auth = HTTPBasicAuth(user, password)
    payload = {"name": user, "password": password}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    res = requests.put(user_url + user, json.dumps(payload), headers=headers, auth=basic_auth)
    if res.status_code == 201:
        logger.info("you are authenticated as '{}'".format(user))
        token = res.json()["token"]
        config_util.update_config("token", token)
    else:
        logger.error("failed to authenticated as '{}'".format(user))
        logger.error("status code: {}, error: {}".format(res.status_code, res.json()["error"]))


def search_package(package: str):
    res = requests.get(search_url.format(package))
    logger.info(
        "{:20.20} | {:20.20} | {:20.20} | {:10.10} | {:10.10} | {:10.10}".format(
            "NAME", "DESCRIPTION", "AUTHOR", "DATE", "VERSION", "KEYWORDS"
        )
    )
    for obj in res.json()["objects"]:
        pkg = obj["package"]
        logger.info(
            "{:20.20} | {:20.20} | {:20.20} | {:10.10} | {:10.10} | {:10.10}".format(
                pkg["name"],
                pkg["description"],
                pkg["author"]["name"],
                pkg["time"]["modified"],
                pkg["dist-tags"]["latest"],
                " ".join(pkg.get("keywords", "")),
            )
        )


def publish_entry():
    try:
        publish_package()
    except Exception as e:
        logger.error("failed to publish")
        logger.error(e)


def publish_package():
    kuki = package_util.load_kuki()
    pkg_name = kuki.get("name")
    version = kuki.get("version")
    logger.info("📦  {}@{}".format(pkg_name, version))

    includes = package_util.load_include()
    tar_name = get_tar_name(pkg_name, version)
    tar = tarfile.open(tar_name, "w:gz")

    files = set([])
    for pattern in includes:
        for file in glob.glob(pattern):
            files.add(file)

    logger.info("=== Tarball Contents === ")

    tar_unpacked_size = 0
    for file in files:
        size = os.path.getsize(file)
        logger.info("{:10d} | {:30.30}".format(size, os.path.basename(file)))
        tar_unpacked_size += size
        tar.add(file)

    tar.close()

    tar_packed_size = os.path.getsize(tar_name)
    logger.info("=== Tarball Details === ")
    logger.info("filename:      " + tar_name)
    logger.info("package size:  {}".format(tar_packed_size))
    logger.info("unpacked size: {}".format(tar_unpacked_size))
    logger.info("total files:   {}".format(len(files)))
    logger.info("publishing to {} with tag latest and default access".format(registry))

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token),
    }

    shasum = hashlib.sha1()

    with open(tar_name, "rb") as file:
        while chunk := file.read(2**20):
            shasum.update(chunk)

    with open(tar_name, "rb") as file:
        tar_base64 = base64.b64encode(file.read())

    data = {
        "_id": pkg_name,
        "name": pkg_name,
        "description": kuki.get("package", ""),
        "dist-tags": {
            "latest": version,
        },
        "readme": package_util.load_readme(),
        "versions": {
            version: {
                "_id": "{}@{}".format(pkg_name, version),
                "name": pkg_name,
                "description": kuki.get("package", ""),
                "author": {"name": kuki.get("author", "unknown")},
                "version": version,
                "readme": package_util.load_readme(),
                "dependencies": kuki.get("dependencies", {}),
                "dist": {
                    "shasum": shasum.hexdigest(),
                    "tarball": "{}{}/-/{}".format(registry, pkg_name, tar_name),
                },
            }
        },
        "_attachments": {
            tar_name: {
                "content_type": "application/octet-stream",
                "data": tar_base64.decode("ascii"),
                "length": tar_packed_size,
            },
        },
    }
    res = requests.put(registry + pkg_name, data=json.dumps(data), headers=headers)
    if res.status_code != 201:
        raise Exception(
            "failed to publish package '{}' with error: {}".format(pkg_name, res.json()["error"])
        )


def get_tar_name(name: str, version: str):
    return "{}-v{}.tgz".format(name, version)


def get_pkg_path(name: str, version: str):
    return Path.joinpath(global_repo_path, name, version)


def get_pkg_id(metadata: Metadata):
    return "{}@{}".format(metadata["name"], metadata["version"])


def get_metadata(name: str) -> Metadata:
    pkg_name, version = (name if "@" in name else name + "@").split("@")
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    if not version:
        res = requests.get(registry + name, headers=headers)
        res_json = res.json()
        if res.status_code != 200:
            raise Exception(res_json.get("error"))
        version: str = res_json["dist-tags"]["latest"]
        metadata = res_json["versions"][version]
    else:
        res = requests.get("{}{}/{}".format(registry, pkg_name, version), headers=headers)
        metadata = res.json()
        if res.status_code != 200:
            raise Exception(metadata.get("error"))
    return metadata


def is_cached(tar_name: str) -> bool:
    filepath = get_cached_filepath(tar_name)
    if os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
        return True
    else:
        return False


def get_cached_filepath(tar_name) -> str:
    return str(Path.joinpath(global_cache_path, tar_name))


def download_entry(name: str):
    try:
        metadata = get_metadata(name)
        pkg_filepath = download_package(metadata)
        shutil.copy(pkg_filepath, os.path.basename(pkg_filepath))
    except Exception as e:
        logger.error("failed to download package '{}' with error: {}".format(name, e))


def download_package(metadata: Metadata) -> str:
    tar_url = metadata["dist"]["tarball"]
    tar_name = os.path.basename(tar_url)
    cached_filepath = get_cached_filepath(tar_name)
    logger.info("download package '{}'".format(tar_name))
    if not is_cached(tar_name):
        headers = {
            "Authorization": "Bearer {}".format(token),
        }
        res = requests.get(tar_url, headers=headers)
        if len(res.content) > 0:
            with open(cached_filepath, "wb") as file:
                file.write(res.content)
        else:
            raise Exception("empty tar file - " + tar_name)
    return cached_filepath


def install_entry(pkgs: List[str]):
    try:
        install_packages(pkgs, False)
        install_dependencies()
        package_util.dump_kuki(kuki_json)
        package_util.dump_pkg_index(package_index)
        dump_global_index()
    except Exception as e:
        logger.error("failed to install packages with error: {}".format(e))


def install_packages(pkgs: List[str], skip_updating_pkg_index=True):
    for pkg in pkgs:
        if skip_updating_pkg_index:
            logger.info("install dependency package '{}'".format(pkg))
        else:
            logger.info("install package '{}'".format(pkg))
        metadata = get_metadata(pkg)
        name = metadata["name"]
        if name == kuki_json["name"]:
            logger.warning("shouldn't install itself, skip...")
            return
        version = metadata["version"]
        pkg_id = get_pkg_id(metadata)

        if not skip_updating_pkg_index:
            kuki_json["dependencies"][name] = version

        if name in package_index and version != package_index[name]["version"]:
            logger.info("current '{}@{}' exists".format(name, package_index[name]["version"]))
            if name in kuki_json["dependencies"]:
                version = kuki_json["dependencies"][name]
                logger.warning(
                    "{} is a dependency package, force to use version {}".format(name, version)
                )
            elif newer_than(version, package_index[name]["version"]):
                logger.warning("use newer '{}@{}'".format(name, version))
            else:
                logger.warning("skip outdated '{}@{}'".format(name, version))
                continue

        package_index[name] = metadata

        if pkg_id in global_index and name in package_index:
            logger.warning("{} is already installed, skip...".format(pkg_id))
            continue
        if pkg_id not in global_index:
            install_package(metadata)
            # global index uses package id as keys, package index uses package name as keys
            global_index[pkg_id] = metadata
            install_packages([k + "@" + v for k, v in metadata["dependencies"].items()])


def install_package(metadata: Metadata):
    pkg_filepath = download_package(metadata)
    pkg_path = get_pkg_path(metadata["name"], metadata["version"])
    # already exists
    if pkg_path.exists() and pkg_path.is_dir():
        return
    if not pkg_path.exists():
        pkg_path.mkdir(parents=True, exist_ok=True)
    tar = tarfile.open(pkg_filepath, "r:gz")
    tar.extractall(pkg_path)
    tar.close()


def uninstall_entry(pkgs: List[str]):
    try:
        uninstall_packages(pkgs)
        refresh_package_index()
        package_util.dump_kuki(kuki_json)
        package_util.dump_pkg_index(package_index)
    except Exception as e:
        logger.error("failed to uninstall packages with error: {}".format(e))


def refresh_package_index():
    current_package_index = package_index.copy()
    package_index.clear()
    for name in kuki_json["dependencies"].keys():
        package_index[name] = current_package_index[name]
        resolve_dependencies(current_package_index, name)


def resolve_dependencies(current_package_index: Dict[str, package_util.Kuki], dep: str):
    deps = current_package_index[dep]["dependencies"]
    for name in deps.keys():
        if name not in package_index:
            package_index[name] = current_package_index[name]
            resolve_dependencies(current_package_index, name)


def newer_than(version1: str, version2: str) -> bool:
    major1, minor1, patch1 = map(int, version1.split("."))
    major2, minor2, patch2 = map(int, version2.split("."))
    return (
        major1 > major2
        or (major1 == major2 and minor1 > minor2)
        or (major1 == major2 and minor1 == minor2 and patch1 > patch2)
    )


def uninstall_packages(pkgs: List[str]):
    for pkg in pkgs:
        name = pkg.split("@")[0]
        if name in kuki_json["dependencies"]:
            logger.info("remove {} from dependencies".format(name))
            kuki_json["dependencies"].pop(name)
        else:
            logger.error("ERROR: '{}' not found in dependencies".format(name))


def dump_global_index():
    with open(global_index_path, "w") as file:
        json.dump(global_index, file, indent=2)


def install_dependencies():
    deps = kuki_json["dependencies"]
    pending = []
    for name, version in deps.items():
        if name in package_index and version == package_index[name]["version"]:
            continue
        pkg_id = get_pkg_id({"name": name, "version": version})
        logger.warning("missing '{}'".format(pkg_id))
        pending.append(pkg_id)
    install_packages(pending)
