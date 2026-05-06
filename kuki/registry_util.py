import base64
import glob
import hashlib
import json
import logging
import os
import re
import shutil
import tarfile
from pathlib import Path
from typing import Any, Dict, List, TypedDict

import requests
import urllib3
from requests.auth import HTTPBasicAuth

from . import config_util, package_util

logger = logging.getLogger()

SEARCH_API = "-/v1/search?text="
USER_API = "-/user/org.couchdb.user:"
global_cache_dir = Path.joinpath(config_util.global_kuki_root, "_cache")
global_index_path = Path.joinpath(config_util.global_kuki_root, ".index")

# TLS verification — secure by default, toggled via set_insecure()
_verify_tls = True


def set_insecure(insecure: bool):
    """Enable or disable TLS certificate verification for all HTTP requests."""
    global _verify_tls
    _verify_tls = not insecure
    if insecure:
        urllib3.disable_warnings()


# --- Lazy initialization of module-level state ---
# These are initialized on first access to avoid side effects at import time.

_kuki_json = None
_package_index = None
_global_index = None
_cache_dir_initialized = False


def _ensure_cache_dir():
    global _cache_dir_initialized
    if not _cache_dir_initialized:
        if global_cache_dir.exists() and not global_cache_dir.is_dir():
            os.remove(str(global_cache_dir))
        global_cache_dir.mkdir(parents=True, exist_ok=True)
        _cache_dir_initialized = True


def _get_kuki_json() -> dict:
    global _kuki_json
    if _kuki_json is None:
        _kuki_json = package_util.load_kuki()
    return _kuki_json


def _get_package_index() -> Dict[str, package_util.Kuki]:
    global _package_index
    if _package_index is None:
        _package_index = package_util.load_pkg_index()
    return _package_index


def _get_global_index() -> Dict[str, package_util.Kuki]:
    global _global_index
    if _global_index is None:
        _global_index = load_global_index()
    return _global_index


class Metadata(TypedDict):
    name: str
    version: str
    dist: Any
    dependencies: Any
    type: str


def load_global_index() -> Dict[str, package_util.Kuki]:
    if global_index_path.exists():
        with open(global_index_path, "r") as file:
            return json.load(file)
    else:
        return {}


def _safe_extractall(tar: tarfile.TarFile, path: Path):
    """Extract tarball with path traversal protection."""
    import sys

    if sys.version_info >= (3, 12):
        tar.extractall(path, filter="data")
    else:
        resolved_path = os.path.realpath(str(path))
        for member in tar.getmembers():
            member_path = os.path.realpath(os.path.join(resolved_path, member.name))
            if not member_path.startswith(resolved_path + os.sep) and member_path != resolved_path:
                raise Exception("Attempted path traversal in tar file: {}".format(member.name))
        tar.extractall(path)


def add_user(user: str, password: str, email: str, scope: str, registry: str):
    user_url = registry + USER_API
    payload = {"name": user, "password": password, "email": email}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    res = requests.put(user_url + user, json.dumps(payload), headers=headers, verify=_verify_tls)

    if res.status_code == 201:
        logger.info("the user '{}' has been added for {}".format(user, registry))
        token = res.json()["token"]
        config_util.update_config("token", token, scope)
        config_util.update_config("user", user, scope)
    else:
        logger.error("failed to add user: " + user)
        logger.error("status code: {}, error: {}".format(res.status_code, res.json()["error"]))


def login(user: str, password: str, scope: str, registry: str):
    config_util.validate_scope(scope)
    user_url = registry + USER_API

    basic_auth = HTTPBasicAuth(user, password)
    payload = {"name": user, "password": password}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    res = requests.put(
        user_url + user, json.dumps(payload), headers=headers, auth=basic_auth, verify=_verify_tls
    )
    if res.status_code == 201:
        logger.info("you are authenticated as '{}'".format(user))
        token = res.json()["token"]
        config_util.update_config("token", token, scope)
        config_util.update_config("user", user, scope)
        config_util.update_config("registry", registry, scope)
    else:
        logger.error("failed to authenticated as '{}'".format(user))
        try:
            error_msg = res.json().get("error", "")
        except Exception:
            error_msg = res.text
        logger.error("status code: {}, error: {}".format(res.status_code, error_msg))


def search_package(package: str, scope: str):
    registry, _, _ = config_util.get_reg_cfg(scope)
    search_url = registry + SEARCH_API
    res = requests.get(search_url + package, verify=_verify_tls)
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
        logger.error(e, exc_info=True)


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
        _, pkg_name, _ = parse_package_name(kuki.get("name"))
        version = kuki.get("version")
        pack_package(pkg_name, version)
    except Exception as e:
        logger.error("failed to pack", exc_info=True)


def publish_package():
    kuki = package_util.load_kuki()
    scope, pkg_name, _ = parse_package_name(kuki.get("name"))
    version = kuki.get("version")

    registry, token, user = config_util.get_reg_cfg(scope)
    if not user:
        logger.error("run 'kuki --adduser' or 'kuki --login' first and then publish the package")
        return

    package_util.is_valid_name(scope + pkg_name)

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

    pkg_info = kuki.copy()

    pkg_info.update(
        {
            "_id": "{}@{}".format(scope + pkg_name, version),
            "author": {"name": kuki.get("author", "unknown")},
            "readme": package_util.load_readme(),
            "dist": {
                "shasum": shasum.hexdigest(),
                "tarball": "{}{}/-/{}".format(registry, scope + pkg_name, tar_name),
            },
        }
    )

    data = {
        "_id": scope + pkg_name,
        "name": scope + pkg_name,
        "description": kuki.get("package", ""),
        "dist-tags": {
            "latest": version,
        },
        "versions": {version: pkg_info},
        "_attachments": {
            (scope + tar_name): {
                "content_type": "application/octet-stream",
                "data": tar_base64.decode("ascii"),
                "length": tar_packed_size,
            },
        },
    }

    if kuki.get("publishConfig") and kuki.get("publishConfig").get("registry"):
        registry = kuki.get("publishConfig").get("registry")

    res = requests.put(
        registry + scope.replace("/", "%2f") + pkg_name,
        data=json.dumps(data),
        headers=headers,
        verify=_verify_tls,
    )
    if res.status_code not in [200, 201]:
        try:
            error_msg = res.json().get("error", "")
        except Exception:
            error_msg = res.text
        logger.error("status code: {}, error: {}".format(res.status_code, error_msg))

        raise Exception(
            "failed to publish package '{}' with error: {}".format(
                scope + pkg_name,
                error_msg,
            )
        )
    logger.info("successfully published {}{}@{}".format(scope, pkg_name, version))


def unpublish_package(pkg_id: str):
    scope, pkg_name, version = parse_package_name(pkg_id)
    registry, token, user = config_util.get_reg_cfg(scope)
    if not user:
        logger.error("run 'kuki --adduser' or 'kuki --login' first and then unpublish the package")
        return

    headers = {
        "Authorization": "Bearer {}".format(token),
    }

    res = requests.get(registry + scope + pkg_name, headers=headers, verify=_verify_tls)
    pkg: dict = res.json()
    if res.status_code != 200:
        logger.error(pkg.get("error"))
        return
    dist_tags: Dict[str, str] = pkg["dist-tags"]
    latest_version = dist_tags.get("latest", "")

    all_version = pkg.get("versions", {})
    only_version = len(all_version) == 1
    no_version = len(all_version) == 0

    if not version or no_version or (only_version and version in all_version):
        logger.info("unpublishing package '{}'".format(pkg_name))
        res = requests.delete(
            registry + scope + pkg_name + "/-rev/" + pkg.get("_rev", ""),
            headers=headers,
            verify=_verify_tls,
        )
        if res.status_code not in [200, 201]:
            try:
                error_msg = res.json().get("error", "")
            except Exception:
                error_msg = res.text
            raise Exception(
                "failed to unpublish package '{}' with error: {}, status code: {}".format(
                    pkg_name,
                    error_msg,
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
        pkg["time"].pop(version)
        res = requests.put(
            registry + scope + pkg_name + "/-rev/" + pkg.get("_rev", ""),
            json=pkg,
            headers=headers,
            verify=_verify_tls,
        )
        if res.status_code != 201:
            raise Exception(
                "failed to unpublish package '{}' with error: {}, status code: {}".format(
                    pkg_name,
                    res.json()["error"],
                    res.status_code,
                )
            )
        new_pkg: dict = requests.get(
            registry + scope + pkg_name, headers=headers, verify=_verify_tls
        ).json()
        tarball_url = dist["tarball"]
        res = requests.delete(
            tarball_url + "/-rev/" + new_pkg.get("_rev", ""),
            headers=headers,
            verify=_verify_tls,
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
    # github requires this format
    return "{}-{}.tgz".format(name, version)


def get_pkg_path(name: str, version: str):
    return Path.joinpath(
        config_util.global_kuki_root,
        name.replace("/", os.sep),
        version,
    )


# name@version
def get_pkg_id(metadata: Metadata):
    return "{}@{}".format(metadata["name"], metadata["version"])


def get_metadata(name: str) -> Metadata:
    scope, pkg_name, version = parse_package_name(name)
    registry, token, _ = config_util.get_reg_cfg(scope)

    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    if not version:
        res = requests.get(registry + scope + pkg_name, headers=headers, verify=_verify_tls)
        res_json = res.json()
        if res.status_code != 200:
            raise Exception(res_json.get("error"))
        version: str = res_json["dist-tags"]["latest"]
        metadata = res_json["versions"][version]
    else:
        res = requests.get(
            "{}{}/{}".format(registry, scope + pkg_name, version),
            headers=headers,
            verify=_verify_tls,
        )
        if res.status_code in [405, 404]:
            res = requests.get(registry + scope + pkg_name, headers=headers, verify=_verify_tls)
            res_json = res.json()
            if res.status_code == 403:
                raise Exception("'{}{}@{}' forbidden".format(scope, pkg_name, version))
            if version not in res_json["versions"]:
                raise Exception("'{}{}@{}' not found".format(scope, pkg_name, version))
            metadata = res_json["versions"][version]
        elif res.status_code == 200:
            metadata = res.json()
        else:
            logger.error("failed to get metadata, status code {}".format(res.status_code))
            raise Exception(res.json().get("error"))
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
        _ensure_cache_dir()
        metadata = get_metadata(name)
        pkg_filepath = download_package(metadata)
        shutil.copy(pkg_filepath, os.path.basename(pkg_filepath))
    except Exception as e:
        logger.error("failed to download package '{}' with error: {}".format(name, e))


def download_package(metadata: Metadata, force=False) -> str:
    _ensure_cache_dir()
    scope, _, _ = parse_package_name(metadata["name"])
    _, token, _ = config_util.get_reg_cfg(scope)

    tar_url = metadata["dist"]["tarball"]
    tar_name = os.path.basename(tar_url)
    cached_filepath = get_cached_filepath(tar_name)
    logger.info("download package '{}'".format(tar_name))
    if not is_cached(tar_name) or force:
        headers = {
            "Authorization": "Bearer {}".format(token),
        }
        res = requests.get(tar_url, headers=headers, verify=_verify_tls)
        if len(res.content) > 0:
            with open(cached_filepath, "wb") as file:
                file.write(res.content)
        else:
            raise Exception("empty tar file - " + tar_name)
    return cached_filepath


def install_global_entry(pkgs: List[str], force: bool):
    kuki_json = _get_kuki_json()
    global_index = _get_global_index()
    package_index = _get_package_index()
    try:
        for pkg in pkgs:
            if pkg.startswith("."):
                install_local_package(pkg, False, True)
            else:
                install_package(pkg, False, True, force)
            dump_global_index()
    except Exception as e:
        logger.error("failed to install packages with error: {}".format(e), exc_info=True)


def install_entry(pkgs: List[str], force: bool):
    kuki_json = _get_kuki_json()
    global_index = _get_global_index()
    package_index = _get_package_index()
    try:
        for pkg in pkgs:
            if pkg.startswith("."):
                install_local_package(pkg)
            else:
                install_package(pkg, False, False, force)
        install_dependencies()
        package_util.dump_kuki(kuki_json)
        package_util.dump_pkg_index(package_index)
        dump_global_index()
    except Exception as e:
        logger.error("failed to install packages with error: {}".format(e), exc_info=True)


def install_package(pkg: str, skip_updating_pkg_index=True, globalMode=False, force=False):
    kuki_json = _get_kuki_json()
    global_index = _get_global_index()
    package_index = _get_package_index()
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
        logger.info("updating dependencies")
        package_index[name] = metadata

    if pkg_id in global_index and name in package_index and not force:
        logger.info("{} is already installed in kuki root".format(pkg_id))
        return
    if pkg_id not in global_index or force:
        # global index uses package id as keys, package index uses package name as keys
        global_index[pkg_id] = metadata
        for dep in [k + "@" + v for k, v in metadata.get("dependencies", {}).items()]:
            install_package(dep, True, globalMode)
        extract_package(metadata, force)
        logger.info("installed %s@%s", metadata["name"], metadata["version"])


def install_local_package(
    local_pkg_tar: str,
    skip_updating_pkg_index=True,
    globalMode=False,
):
    kuki_json = _get_kuki_json()
    global_index = _get_global_index()
    package_index = _get_package_index()
    logger.info("installing local package '{}'".format(local_pkg_tar))
    local_pkg_tar_path = Path(local_pkg_tar)
    if not local_pkg_tar_path.exists():
        logger.error("local package tar not found: '{}'".format(local_pkg_tar))
        return
    tar = tarfile.open(local_pkg_tar_path)
    file = tar.extractfile("kuki.json")
    pkg_kuki_json: package_util.Kuki = json.load(file)
    name = pkg_kuki_json["name"]
    version = pkg_kuki_json["version"]
    install_pkg_path = get_pkg_path(name, version)
    if not install_pkg_path.exists():
        install_pkg_path.mkdir(parents=True, exist_ok=True)
    _safe_extractall(tar, install_pkg_path)
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


def extract_package(metadata: Metadata, force=False):
    _ensure_cache_dir()
    pkg_filepath = download_package(metadata, force)
    pkg_path = get_pkg_path(metadata["name"], metadata["version"])
    latest_path = get_pkg_path(metadata["name"], "latest")
    if not pkg_path.exists():
        pkg_path.mkdir(parents=True, exist_ok=True)
    tar = tarfile.open(pkg_filepath, "r:gz")
    _safe_extractall(tar, pkg_path)
    tar.close()
    if latest_path.exists():
        latest_path.unlink()
    logger.info("update latest link to %s", metadata["version"])
    os.symlink(metadata["version"], latest_path)


def uninstall_entry(pkgs: List[str]):
    kuki_json = _get_kuki_json()
    package_index = _get_package_index()
    try:
        uninstall_packages(pkgs)
        refresh_package_index()
        package_util.dump_kuki(kuki_json)
        package_util.dump_pkg_index(package_index)
    except Exception as e:
        logger.error("failed to uninstall packages with error: {}".format(e), exc_info=True)


def refresh_package_index():
    kuki_json = _get_kuki_json()
    package_index = _get_package_index()
    current_package_index = package_index.copy()
    package_index.clear()
    for name in kuki_json["dependencies"].keys():
        package_index[name] = current_package_index[name]
        resolve_dependencies(current_package_index, name)


def resolve_dependencies(current_package_index: Dict[str, package_util.Kuki], dep: str):
    package_index = _get_package_index()
    deps = current_package_index[dep].get("dependencies", {})
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
    kuki_json = _get_kuki_json()
    for pkg in pkgs:
        scope, pkg_name, _ = parse_package_name(pkg)
        name = scope + pkg_name
        if name in kuki_json["dependencies"]:
            logger.info("remove {} from dependencies".format(name))
            kuki_json["dependencies"].pop(name)
        else:
            logger.error("ERROR: '{}' not found in dependencies".format(name))


def dump_global_index():
    global_index = _get_global_index()
    with open(global_index_path, "w") as file:
        json.dump(global_index, file, indent=2)


def install_dependencies():
    kuki_json = _get_kuki_json()
    global_index = _get_global_index()
    package_index = _get_package_index()
    deps = kuki_json.get("dependencies", [])
    pending = []
    for name, version in deps.items():
        pkg_id = get_pkg_id({"name": name, "version": version})
        if (
            name in package_index
            and version == package_index[name]["version"]
            and pkg_id in global_index
        ):
            continue
        logger.warning("missing '{}'".format(pkg_id))
        pending.append(pkg_id)
    for pkg in pending:
        install_package(pkg)


def parse_package_name(pkg_name: str) -> tuple[str, str, str]:
    pattern = r"(@[a-z-]+/)?([a-z-]+)(?:@([0-9]+\.[0-9]+\.[0-9]+))?"
    if re.fullmatch(pattern, pkg_name):
        groups = re.match(pattern, pkg_name).groups()
        return tuple(g if g else "" for g in groups)
    else:
        raise Exception("failed to parse package name - " + pkg_name)
