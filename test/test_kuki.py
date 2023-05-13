import json
import logging
import tarfile
from pathlib import Path
from typing import List

import pytest
import responses

from kuki import config_util, kuki, package_util, registry_util

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function", autouse=True)
def tmp_dir(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch):
    # generate new dir every run
    dir = tmp_path_factory.mktemp("kuki")

    home = Path.joinpath(dir, "home")
    home.mkdir(parents=True, exist_ok=True)

    global_kuki_root = Path.joinpath(home, "kuki")
    global_kuki_root.mkdir(parents=True, exist_ok=True)
    config_util.global_kuki_root = global_kuki_root

    config_util.global_config_dir = Path.joinpath(config_util.global_kuki_root, "config")

    config_util.global_config_dir.mkdir(parents=True, exist_ok=True)
    config_util.global_config_path = Path.joinpath(config_util.global_config_dir, config_util.config_file)

    global_cache_path = Path.joinpath(global_kuki_root, ".cache")
    global_cache_path.mkdir(parents=True, exist_ok=True)
    registry_util.global_cache_path = global_cache_path

    global_index_path = Path.joinpath(global_kuki_root, ".index")
    registry_util.global_index_path = global_index_path

    dummy_package = Path.joinpath(dir, "dummy")
    dummy_package.mkdir(parents=True, exist_ok=True)

    package_util.package_path = dummy_package
    package_util.package_config_path = Path.joinpath(dummy_package, package_util.config_file)
    monkeypatch.chdir(dummy_package)

    registry_util.package_index = package_util.load_pkg_index()
    registry_util.global_index = registry_util.load_global_index()
    return dir


@pytest.fixture(scope="function")
def mock_package_api(request: pytest.FixtureRequest):
    registry = registry_util.registry
    older_pkg_ids = ["csv-v0.0.1.tgz", "file-v1.0.0.tgz", "log-v0.1.0.tgz"]
    for pkg in Path.joinpath(request.path.parent, "data").glob("**/*"):
        name, version = str(pkg.name)[:-4].split("-v")
        tar = tarfile.open(str(pkg), "r:gz")
        kuki = json.load(tar.extractfile(package_util.config_file))
        kuki["author"] = {"name": kuki["author"]}
        tar_url = "{}{}/-/{}".format(registry, name, pkg.name)
        kuki["dist"] = {"tarball": tar_url}
        pkg_json = {
            "dist-tags": {"latest": version},
            "versions": {version: kuki},
        }
        if str(pkg.name) not in older_pkg_ids:
            responses.add(responses.GET, registry + name, json=pkg_json, status=200)
        responses.add(
            responses.GET, "{}{}/{}".format(registry, name, version), json=kuki, status=200
        )
        with open(pkg, "rb") as file:
            responses.add(
                responses.GET,
                tar_url,
                content_type="application/octet-stream",
                body=file.read(),
                status=200,
            )


def run_kuki(arg: str):
    args = kuki.parser.parse_args(arg.split())
    kuki.kuki(args)


@responses.activate
def test_adduser(monkeypatch: pytest.MonkeyPatch):
    responses.add(
        responses.PUT,
        registry_util.user_url + "test",
        json={"token": "7IForS1HdYwD7wgFxXGMTA=="},
        status=201,
    )
    inputs = iter(["test", "password", "test@test.com"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    run_kuki("--adduser")
    assert config_util.load_config()["token"] == "7IForS1HdYwD7wgFxXGMTA=="


@pytest.mark.parametrize(
    "command_params, expected_token, expected_registry",
    [
        ("--config token=t0ken", "t0ken", ""),
        ("--config registry=http://localhost", "", "http://localhost"),
        ("--config token=t0ken registry=http://localhost", "t0ken", "http://localhost"),
    ],
)
def test_config(command_params, expected_token, expected_registry):
    run_kuki(command_params)
    config = config_util.load_config()
    assert config.get("token", "") == expected_token
    assert config.get("registry", "") == expected_registry


def test_init(monkeypatch: pytest.MonkeyPatch):
    inputs = iter(
        [
            "dummy",
            "a dummy package",
            "Saitama",
            "https://github.com/saitama/dummy",
            "yes",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    run_kuki("--init")
    kuki_json = package_util.load_kuki()

    assert kuki_json.get("name") == "dummy"
    assert kuki_json.get("description") == "a dummy package"
    assert kuki_json.get("author") == "Saitama"
    assert kuki_json.get("git") == "https://github.com/saitama/dummy"
    assert kuki_json.get("version") == "0.0.1"
    assert kuki_json.get("dependencies") == {}

    monkeypatch.setattr("builtins.input", lambda _: "no")
    package_util.generate_json(
        "dummy1", "a dummy package", "Saitama", "https://github.com/saitama/dummy"
    )

    kuki_json = package_util.load_kuki()

    assert kuki_json.get("name") == "dummy"

    inputs = iter(["yes", "yes"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    package_util.generate_json(
        "dummy1", "a dummy package", "Saitama", "https://github.com/saitama/dummy"
    )

    kuki_json = package_util.load_kuki()

    assert kuki_json.get("name") == "dummy1"


@responses.activate
def test_login(monkeypatch: pytest.MonkeyPatch):
    responses.add(
        responses.PUT,
        registry_util.user_url + "test",
        json={"token": "7IForS1HdYwD7wgFxXGMTA=="},
        status=201,
    )
    inputs = iter(
        [
            "test",
            "password",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    run_kuki("--login")
    assert config_util.load_config()["token"] == "7IForS1HdYwD7wgFxXGMTA=="


@responses.activate
def test_search():
    search_result = {
        "objects": [
            {
                "package": {
                    "name": "dummy",
                    "description": "a dummy package",
                    "dist-tags": {"latest": "1.1.5"},
                    "author": {"name": "Saitama"},
                    "repository": {
                        "type": "git",
                        "url": "git+https://github.com/saitama/dummy",
                    },
                    "readmeFilename": "README.md",
                    "homepage": "https://github.com/saitama/dummy#readme",
                    "keywords": ["q", "kx", "kdb+"],
                    "time": {"modified": "2023-04-23T11:36:41.844Z"},
                    "license": "Apache-2.0",
                    "versions": {"1.1.5": "latest"},
                },
            }
        ],
        "total": 1,
        "time": "Sun, 23 Apr 2023 11:39:23 GMT",
    }
    responses.add(
        responses.GET,
        registry_util.search_url.format("dummy"),
        json=search_result,
        status=201,
    )
    run_kuki("--search dummy")


def test_version(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    package_util.generate_json(
        "dummy", "a dummy package", "Saitama", "https://github.com/saitama/dummy"
    )

    run_kuki("--version patch")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "0.0.2"

    run_kuki("--version patch")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "0.0.3"

    run_kuki("--version minor")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "0.1.0"

    run_kuki("--version minor")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "0.2.0"

    run_kuki("--version patch")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "0.2.1"

    run_kuki("--version major")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "1.0.0"

    run_kuki("--version major")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "2.0.0"

    run_kuki("--version minor")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "2.1.0"

    run_kuki("--version patch")
    kuki_json = package_util.load_kuki()
    assert kuki_json["version"] == "2.1.1"


@responses.activate
def test_publish(monkeypatch: pytest.MonkeyPatch):
    package_name = "dummy"
    responses.add(
        responses.PUT,
        registry_util.registry + package_name,
        status=201,
    )

    monkeypatch.setattr("builtins.input", lambda _: "yes")
    package_util.generate_json(
        package_name, "a dummy package", "Saitama", "https://github.com/saitama/dummy"
    )

    source_files = [
        "src/dummy.q",
        "src/lib/util.q",
        "conf/exchange.csv",
    ]

    for file in source_files:
        filepath = Path(file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()

    run_kuki("--publish")

    tar_path = Path(registry_util.get_tar_name(package_name, "0.0.1"))

    assert tar_path.exists()

    tar = tarfile.open(str(tar_path), "r:gz")
    tar_files = tar.getnames()

    source_files.remove("conf/exchange.csv")
    source_files.append("src/lib")
    source_files.append("README.md")
    source_files.append(package_util.config_file)

    assert len(source_files) == len(tar_files)

    sorted_source_files = sorted(source_files)
    sorted_tar_files = sorted(tar_files)
    for i, file in enumerate(sorted_tar_files):
        assert file == sorted_source_files[i]

    tar.close()

    # test includes
    with open(package_util.package_include_path, "w") as file:
        file.writelines(["conf*", ""])

    run_kuki("--publish")

    assert tar_path.exists()

    tar = tarfile.open(str(tar_path), "r:gz")
    tar_files = tar.getnames()

    source_files.append("conf")
    source_files.append("conf/exchange.csv")

    assert len(source_files) == len(tar_files)

    sorted_source_files = sorted(source_files)
    sorted_tar_files = sorted(tar_files)
    for i, file in enumerate(sorted_tar_files):
        assert file == sorted_source_files[i]

    tar.close()


@pytest.mark.parametrize(
    "command_params, expected_tar",
    [
        ("--download log", "log-v0.1.1.tgz"),
        ("--download log@0.1.0", "log-v0.1.0.tgz"),
        ("--download file", "file-v1.0.1.tgz"),
    ],
)
@responses.activate
def test_download(
    tmp_dir,
    mock_package_api,
    command_params,
    expected_tar,
):
    run_kuki(command_params)
    assert Path.joinpath(tmp_dir, "dummy", expected_tar).exists()


@pytest.mark.parametrize(
    "command_params, expected_index, expected_pkg_index, expected_deps",
    [
        ("--install log", ["log@0.1.1"], ["log"], ["log"]),
        ("--install file", ["file@1.0.1", "log@0.1.1"], ["file", "log"], ["file"]),
        (
            "--install csv",
            ["csv@0.0.2", "file@1.0.0", "log@0.1.0"],
            ["csv", "file", "log"],
            ["csv"],
        ),
        (
            "--install csv@0.0.1",
            ["csv@0.0.1", "file@1.0.0", "log@0.1.0"],
            ["csv", "file", "log"],
            ["csv"],
        ),
        (
            "--install file log",
            ["file@1.0.1", "log@0.1.1"],
            ["file", "log"],
            ["file", "log"],
        ),
        (
            "--install file log@0.1.0",
            ["file@1.0.1", "log@0.1.1", "log@0.1.0"],
            ["file", "log"],
            ["file", "log"],
        ),
    ],
)
@responses.activate
def test_install(
    monkeypatch: pytest.MonkeyPatch,
    mock_package_api,
    command_params,
    expected_index: List[str],
    expected_pkg_index,
    expected_deps,
):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    package_util.generate_json(
        "dummy", "a dummy package", "Saitama", "https://github.com/saitama/dummy"
    )
    registry_util.kuki_json = package_util.load_kuki()
    run_kuki(command_params)
    global_index = registry_util.load_global_index()
    assert len(global_index) == len(expected_index)

    for pkg_id in expected_index:
        assert pkg_id in global_index
        name, version = pkg_id.split("@")
        pkg_dir = Path.joinpath(config_util.global_kuki_root, name, version)
        assert Path.joinpath(pkg_dir, package_util.config_file).exists()

    pkg_index = package_util.load_pkg_index()
    assert len(pkg_index) == len(expected_pkg_index)
    for pkg in expected_pkg_index:
        assert pkg in pkg_index

    dependencies = package_util.load_kuki()["dependencies"]
    assert len(dependencies) == len(expected_deps)
    for dep in expected_deps:
        assert dep in dependencies


@pytest.mark.parametrize(
    "command_params, expected_index, expected_pkg_index, expected_deps",
    [
        (
            "--uninstall csv",
            ["csv@0.0.2", "file@1.0.1", "file@1.0.0", "log@0.1.1", "log@0.1.0"],
            ["file", "log"],
            ["file"],
        ),
        (
            "--uninstall csv file",
            ["csv@0.0.2", "file@1.0.1", "file@1.0.0", "log@0.1.1", "log@0.1.0"],
            [],
            [],
        ),
        (
            "--uninstall csv file dummy",
            ["csv@0.0.2", "file@1.0.1", "file@1.0.0", "log@0.1.1", "log@0.1.0"],
            [],
            [],
        ),
    ],
)
@responses.activate
def test_uninstall(
    monkeypatch: pytest.MonkeyPatch,
    mock_package_api,
    command_params,
    expected_index: List[str],
    expected_pkg_index,
    expected_deps,
):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    package_util.generate_json(
        "dummy", "a dummy package", "Saitama", "https://github.com/saitama/dummy"
    )
    registry_util.kuki_json = package_util.load_kuki()

    run_kuki("--install csv file")

    run_kuki(command_params)
    global_index = registry_util.load_global_index()
    assert len(global_index) == len(expected_index)

    for pkg_id in expected_index:
        assert pkg_id in global_index
        name, version = pkg_id.split("@")
        pkg_dir = Path.joinpath(config_util.global_kuki_root, name, version)
        assert Path.joinpath(pkg_dir, package_util.config_file).exists()

    pkg_index = package_util.load_pkg_index()
    assert len(pkg_index) == len(expected_pkg_index)
    for pkg in expected_pkg_index:
        assert pkg in pkg_index

    dependencies = package_util.load_kuki()["dependencies"]
    assert len(dependencies) == len(expected_deps)
    for dep in expected_deps:
        assert dep in dependencies
