import atexit
import json
import logging
import os
import signal
import subprocess
from pathlib import Path

from . import config_util
from .util import (
    PROCESS_DEFAULT,
    PROFILE_DEFAULT,
    generate_cmd,
    generate_process_options,
)

logger = logging.getLogger()

KTRL_PROFILE = PROFILE_DEFAULT
KTRL_INSTANCE = {
    "package": "",
    "version": "",
    "file": "",
    "dbPath": "",
    "args": [],
}
KTRL_PROCESS = KTRL_INSTANCE.copy()
KTRL_PROCESS.update(PROCESS_DEFAULT)


global_profile_dir = Path.joinpath(config_util.global_kuki_root, "_profile")
global_process_dir = Path.joinpath(config_util.global_kuki_root, "_process")
local_profile_dir = Path.joinpath(Path("ktrl"), "profile")
local_process_dir = Path.joinpath(Path("ktrl"), "process")


def dump_json(path: Path, config):
    with open(path, "w") as file:
        file.write(config)


def config_file(name: str, type: str, globalMode: False):
    if type == "profile":
        path = Path.joinpath(
            global_profile_dir if globalMode else local_profile_dir,
            name + ".profile.json",
        )
        config = KTRL_PROFILE
        all_keys = set(KTRL_PROFILE.keys())
    else:
        path = Path.joinpath(
            global_process_dir if globalMode else local_process_dir,
            name + ".process.json",
        )
        config = KTRL_INSTANCE.copy()
        all_keys = set(KTRL_PROCESS.keys())
        if not globalMode:
            config.pop("package")
            config.pop("version")

    default_keys = set(config.keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        config.update(json.loads(path.read_text()))
        for key in config.keys():
            if key not in all_keys:
                logger.warn("unrecognized key - {}".format(key))
                delattr(config, key)
        keys = config.keys()
    else:
        keys = default_keys

    for key in sorted(keys):
        current_value = config.get(key, "")
        input_value = input("{} ({}): ".format(key, current_value)).strip()
        if key == "args":
            input_value = input_value.split()
        config[key] = input_value if input_value else current_value
        if key in ["file", "package", "version"] and not config[key]:
            logger.error(key + " cannot be empty string")
            return

    config_json = json.dumps(config, indent=2)
    logger.info("About to write to {}".format(path))
    logger.info("\n" + config_json)
    proceed = input("Is this OK? (YES/no) ").strip()
    if not proceed or proceed.lower() == "yes":
        dump_json(path, config_json)


def list_config(type: str, globalMode: False):
    if type == "profile":
        path = global_profile_dir if globalMode else local_profile_dir
    else:
        path = global_process_dir if globalMode else local_process_dir

    for file in path.glob("*.json"):
        print(file)


def start(
    profile_name: str, process_name: str, globalMode: False, label="", debug=False, kargs=[]
):
    profile_path = Path.joinpath(
        local_profile_dir,
        profile_name + ".profile.json",
    )
    global_profile_path = Path.joinpath(
        global_profile_dir,
        profile_name + ".profile.json",
    )
    process_path = Path.joinpath(
        global_process_dir if globalMode else local_process_dir,
        process_name + ".process.json",
    )
    if profile_path.exists() and not globalMode:
        profile_json: dict = json.loads(profile_path.read_text())
    elif global_profile_path.exists():
        profile_json: dict = json.loads(global_profile_path.read_text())
    else:
        logger.error("No such file - {}".format(profile_path))
        exit(1)

    if process_path.exists():
        process_json: dict = json.loads(process_path.read_text())
    else:
        logger.error("No such file - {}".format(process_path))
        exit(1)

    if "port" not in process_json:
        process_json.setdefault("port", "0W")

    if globalMode:
        package_path = Path.joinpath(
            config_util.global_kuki_root,
            process_json.get("package"),
            process_json.get("version"),
        )
        if not package_path.exists():
            logger.error("No such folder - {}".format(package_path))
            return
        os.chdir(package_path)
    else:
        package_path = Path.cwd()

    file_name: str = process_json.get("file")

    file_path = Path.joinpath(
        package_path,
        "src",
        file_name[4:] if file_name.startswith("src/") else file_name,
    )

    options = generate_process_options([], process_json)
    # generate run command
    options = (
        ["-kScriptType", "ktrl"]
        + ["-kProcess", process_name]
        + ["-kHostAlias", profile_json.get("hostAlias", "''")]
        + ["-file", str(file_path)]
        + ["-dbPath", process_json.get("dbPath", [])]
        + (kargs.split() if kargs else process_json.get("args"))
        + options
    )
    if label:
        options += ["-kLabel", "ktrl-" + label]
    if debug:
        options += ["-debug"]

    cmd = generate_cmd(options, profile_json)

    logger.info("starting " + cmd)

    try:
        p = subprocess.Popen(cmd, shell=True)
        atexit.register(p.terminate)
        signal.signal(
            signal.SIGTERM,
            terminate_handler,
        )
        p.communicate()
        exit(p.returncode)
    except subprocess.CalledProcessError:
        exit(1)


def terminate_handler(sig_num, _):
    sig_name = signal.Signals(sig_num).name
    logger.error("Signal hander called with signal %s (%d)", sig_name, sig_num)
    exit(1)
