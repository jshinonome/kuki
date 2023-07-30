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
import urllib3
from requests.auth import HTTPBasicAuth

from . import config_util, package_util

urllib3.disable_warnings()

logger = logging.getLogger()
config = config_util.load_config()
registry = config.get("registry", "https://kuki.ninja/")
token = config.get("token", "")
user = config.get("user", "")

global_cache_dir = Path.joinpath(config_util.global_kuki_root, "_cache")
global_index_path = Path.joinpath(config_util.global_kuki_root, ".index")

kuki_json = package_util.load_kuki()

if global_cache_dir.exists() and not global_cache_dir.is_dir():
    os.remove(str(global_cache_dir))

global_cache_dir.mkdir(parents=True, exist_ok=True)

user_url = registry + "-/user/org.couchdb.user:"
search_url = registry + "-/v1/search?text={}"

package_index = package_util.load_pkg_index()


class Metadata(TypedDict):
    name: str
    version: str
    dist: any
    dependencies: any
    type: str


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
    res = requests.put(user_url + user, json.dumps(payload), headers=headers, verify=False)

    if res.status_code == 201:
        logger.info("the user '{}' has been added".format(user))
        token = res.json()["token"]
        config_util.update_config("token", token)
        config_util.update_config("user", user)
    else:
        logger.error("failed to add user: " + user)
        logger.error("status code: {}, error: {}".format(res.status_code, res.json()["error"]))


def login(user: str, password: str):
    basic_auth = HTTPBasicAuth(user, password)
    payload = {"name": user, "password": password}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    res = requests.put(
        user_url + user, json.dumps(payload), headers=headers, auth=basic_auth, verify=False
    )
    if res.status_code == 201:
        logger.info("you are authenticated as '{}'".format(user))
        token = res.json()["token"]
        config_util.update_config("token", token)
        config_util.update_config("user", user)
    else:
        logger.error("failed to authenticated as '{}'".format(user))
        logger.error("status code: {}, error: {}".format(res.status_code, res.json()["error"]))


def search_package(package: str):
    res = requests.get(search_url.format(package), verify=False)
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


def get_publisher(pkg_name: str) -> str:
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    res = requests.get(registry + pkg_name, headers=headers, verify=False)
    if res.status_code == 404:
        return ""
    else:
        pkg = res.json()
        latest_version = pkg["dist-tags"]["latest"]
        return pkg["versions"][latest_version]["publisher"]


def publish_entry():
    try:
        if not user:
            logger.error(
                "run 'kuki --adduser' or 'kuki --login' first and then publish the package"
            )
            return
        publish_package()
    except Exception as e:
        logger.error("failed to publish")
        logger.error(e)


def pack_package(pkg_name: str, version: str):
    logger.info("📦  {}@{}".format(pkg_name, version))

    includes = package_util.load_include()
    tar_name = get_tar_name(pkg_name, version)

    files = set([])
    for pattern in includes:
        for file in glob.glob(pattern):
            files.add(file)

    logger.info("=== Tarball Contents === ")

    tar = tarfile.open(tar_name, "w:gz")
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

    return tar_name, tar_packed_size


def pack_entry():
    try:
        kuki = package_util.load_kuki()
        pkg_name = kuki.get("name")
        version = kuki.get("version")
        pack_package(pkg_name, version)
    except Exception as e:
        logger.error("failed to pack")
        logger.error(e)


def publish_package():
    kuki = package_util.load_kuki()
    pkg_name = kuki.get("name")
    version = kuki.get("version")

    publisher = get_publisher(pkg_name)
    if publisher and publisher != user:
        logger.error("not allowed to publish to other user's package")
        return

    package_util.is_valid_name(pkg_name)

    tar_name, tar_packed_size = pack_package(pkg_name, version)

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
                "publisher": user,
                "type": kuki["type"],
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
    res = requests.put(registry + pkg_name, data=json.dumps(data), headers=headers, verify=False)
    if res.status_code != 201:
        raise Exception(
            "failed to publish package '{}' with error: {}".format(pkg_name, res.json()["error"])
        )


def unpublish_package(pkg_id: str):
    pkg_name, version = (pkg_id if "@" in pkg_id else pkg_id + "@").split("@")

    headers = {
        "Authorization": "Bearer {}".format(token),
    }

    res = requests.get(registry + pkg_name, headers=headers, verify=False)
    pkg: dict = res.json()
    if res.status_code != 200:
        raise Exception(pkg.get("error"))
    dist_tags: Dict[str, str] = pkg["dist-tags"]
    latest_version = dist_tags["latest"]
    publisher = pkg["versions"][latest_version]["publisher"]
    if user != publisher:
        logger.error("not allowed to unpublish other user's package")
        return
    all_version = pkg.get("versions", {})
    only_version = len(all_version) == 1
    no_version = len(all_version) == 0

    if not version or no_version or (only_version and version in all_version):
        logger.info("unpublishing package '{}'".format(pkg_name))
        res = requests.delete(
            registry + pkg_name + "/-rev/" + pkg.get("_rev"),
            headers=headers,
            verify=False,
        )
        if res.status_code != 201:
            raise Exception(
                "failed to unpublish package '{}' with error: {}, status code: {}".format(
                    pkg_name,
                    res.json()["error"],
                    res.status_code,
                )
            )
        logger.info("successfully unpublish package '{}'".format(pkg_name))
    else:
        logger.info("unpublishing package '{}@{}'".format(pkg_name, version))
        if version not in all_version:
            logger.error("no version:{} available".format(version))
            return
        dist = all_version[version]["dist"]
        all_version.pop(version)

        for tag in list(dist_tags.keys()):
            if dist_tags[tag] == version:
                dist_tags.pop(tag)
        if latest_version == version:
            dist_tags["latest"] = max(all_version)
        pkg.pop("_revisions", None)
        pkg.pop("_attachments", None)
        pkg["dist-tags"] = dist_tags
        pkg["versions"] = all_version
        res = requests.put(
            registry + pkg_name + "/-rev/" + pkg.get("_rev"),
            json=pkg,
            headers=headers,
            verify=False,
        )
        if res.status_code != 201:
            raise Exception(
                "failed to unpublish package '{}' with error: {}, status code: {}".format(
                    pkg_name,
                    res.json()["error"],
                    res.status_code,
                )
            )
        new_pkg: dict = requests.get(registry + pkg_name, headers=headers, verify=False).json()
        tarball_url = dist["tarball"]
        res = requests.delete(
            tarball_url + "/-rev/" + new_pkg.get("_rev"),
            headers=headers,
            verify=False,
        )
        if res.status_code != 201:
            raise Exception(
                "failed to unpublish package '{}' with error: {}, status code: {}".format(
                    pkg_name,
                    res.json()["error"],
                    res.status_code,
                )
            )
        logger.info("successfully unpublishing package '{}@{}'".format(pkg_name, version))


def get_tar_name(name: str, version: str):
    return "{}-v{}.tgz".format(name, version)


def get_pkg_path(name: str, version: str):
    return Path.joinpath(config_util.global_kuki_root, name, version)


def get_pkg_id(metadata: Metadata):
    return "{}@{}".format(metadata["name"], metadata["version"])


def get_metadata(name: str) -> Metadata:
    pkg_name, version = (name if "@" in name else name + "@").split("@")
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    if not version:
        res = requests.get(registry + name, headers=headers, verify=False)
        res_json = res.json()
        if res.status_code != 200:
            raise Exception(res_json.get("error"))
        version: str = res_json["dist-tags"]["latest"]
        metadata = res_json["versions"][version]
    else:
        res = requests.get(
            "{}{}/{}".format(registry, pkg_name, version), headers=headers, verify=False
        )
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
    return str(Path.joinpath(global_cache_dir, tar_name))


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
        res = requests.get(tar_url, headers=headers, verify=False)
        if len(res.content) > 0:
            with open(cached_filepath, "wb") as file:
                file.write(res.content)
        else:
            raise Exception("empty tar file - " + tar_name)
    return cached_filepath


def install_entry(pkgs: List[str]):
    try:
        for pkg in pkgs:
            if pkg.startswith("."):
                install_local_package(pkg)
            else:
                install_package(pkg, False)
        install_dependencies()
        package_util.dump_kuki(kuki_json)
        package_util.dump_pkg_index(package_index)
        dump_global_index()
    except Exception as e:
        logger.error("failed to install packages with error: {}".format(e))


def install_package(pkg: str, skip_updating_pkg_index=True, globalMode=False):
    package_type = kuki_json.get("type", "q")

    if package_type == "k":
        allow_package_types = ["k"]
    elif package_type == "k9":
        allow_package_types = ["k9"]
    else:
        allow_package_types = ["q", "k"]

    if skip_updating_pkg_index:
        logger.info("installing dependency package '{}'".format(pkg))
    else:
        logger.info("installing package '{}'".format(pkg))
    metadata = get_metadata(pkg)

    if not metadata.get("type", "q") in allow_package_types and not globalMode:
        logger.error(
            "Only allows to install package type '{}', Got package type '{}'".format(
                allow_package_types, metadata.get("type", "q")
            )
        )
        return
    name = metadata["name"]
    if not globalMode and name == kuki_json["name"]:
        logger.warning("shouldn't install itself, skip...")
        return

    version = metadata["version"]
    pkg_id = get_pkg_id(metadata)

    if not skip_updating_pkg_index and not globalMode:
        kuki_json["dependencies"][name] = version

    if not globalMode:
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
                return

        package_index[name] = metadata

    if pkg_id in global_index and name in package_index:
        logger.warning("{} is already installed in kuki root, skip...".format(pkg_id))
        return
    if pkg_id not in global_index:
        # global index uses package id as keys, package index uses package name as keys
        global_index[pkg_id] = metadata
        for dep in [k + "@" + v for k, v in metadata["dependencies"].items()]:
            install_package(dep, True, globalMode)
        extract_package(metadata)


def install_local_package(
    local_pkg_tar: str,
    skip_updating_pkg_index=True,
    globalMode=False,
):
    logger.info("installing local package '{}'".format(local_pkg_tar))
    local_pkg_tar_path = Path(local_pkg_tar)
    if local_pkg_tar_path.exists():
        tar = tarfile.open(local_pkg_tar_path)
        file = tar.extractfile("kuki.json")
        pkg_kuki_json: package_util.Kuki = json.load(file)
    name = pkg_kuki_json["name"]
    version = pkg_kuki_json["version"]
    install_pkg_path = get_pkg_path(name, version)
    if not install_pkg_path.exists():
        install_pkg_path.mkdir(parents=True, exist_ok=True)
    tar.extractall(install_pkg_path)
    tar.close()

    if not skip_updating_pkg_index and not globalMode:
        kuki_json["dependencies"][name] = version

    if not globalMode:
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
                return

        package_index[name] = pkg_kuki_json
    else:
        global_index[get_pkg_id(pkg_kuki_json)] = pkg_kuki_json
    logger.info("installed local package '{}'".format(local_pkg_tar))


def extract_package(metadata: Metadata):
    pkg_filepath = download_package(metadata)
    pkg_path = get_pkg_path(metadata["name"], metadata["version"])
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
    for pkg in pending:
        install_package(pkg)
