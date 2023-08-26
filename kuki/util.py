from pathlib import Path
from typing import List

CMD_OPTION_MAP = {
    "console_size": "c",
    "error_traps": "e",
    "garbage_collection": "g",
    "memory_limit": "w",
    "offset_time": "o",
    "port": "p",
    "precision": "P",
    "quiet": "q",
    "threads": "s",
    "timeout": "T",
    "timer_period": "t",
    "disable_system_cmd": "u",
    "replicate": "r",
    "tls": "E",
    "blocked": "b",
}


PROCESS_DEFAULT = {
    "console_size": [25, 80],
    "error_traps": "none",
    "garbage_collection": "deferred",
    "memory_limit": 0,
    "offset_time": 0,
    "port": "0W",
    "precision": 7,
    "quiet": False,
    "threads": 0,
    "timeout": 0,
    "timer_period": 0,
    "disable_system_cmd": 0,
    "replicate": "",
    "tls": "plain",
    "blocked": False,
}


PROFILE_DEFAULT = {
    # source before running
    "envPath": "",
    "binary": "q",
    # q or k
    "binaryType": "q",
    "binaryHome": "",
    "licenseDir": "",
    # loaded as .ktrl.hostAlias
    "hostAlias": "",
}


def generate_process_options(args: List[str], process_cfg: dict[str, str]) -> List[str]:
    system_args = list(filter(lambda arg: arg[0] == "-" and len(arg) == 2, args))
    cmd = []
    for key, value in process_cfg.items():
        if key not in CMD_OPTION_MAP:
            continue
        option = "-" + CMD_OPTION_MAP.get(key)
        # skip command line specified process configuration
        # command line options overwrite kest.json
        if option in system_args:
            continue

        if key == "port":
            cmd.append(option)
            cmd.append(str(value))
            continue

        # skip non-exist configuration or default configuration
        if key not in PROCESS_DEFAULT or value == PROCESS_DEFAULT[key]:
            continue

        if key in ["quiet", "blocked"] and value:
            cmd.append(option)
            continue

        cmd.append(option)
        if key == "error_traps":
            cmd.append(str(["none", "suspend", "dump"].index(value)))
        elif key == "console_size":
            cmd.append(" ".join([str(c) for c in value]))
        elif key == "garbage_collection":
            cmd.append(str(["deferred", "immediate"].index(value)))
        elif key == "tls":
            cmd.append(str(["plain", "mixed", "tls"].index(value)))
        elif key == "replicate":
            cmd.append(value)
        else:
            cmd.append(str(value))
    return cmd


def generate_cmd(options: List[str], env_cfg: dict[str, str]) -> str:
    q_path = Path.joinpath(Path(__file__).parent, "q", "kuki.q").resolve()
    k_path = Path.joinpath(Path(__file__).parent, "k", "kuki.k").resolve()
    cmd = []
    if env_cfg:
        binary_type = env_cfg.get("binaryType", "q")
        if binary_type == "q":
            if env_cfg.get("envPath"):
                cmd.append("source " + env_cfg.get("envPath"))
            if env_cfg.get("binaryHome"):
                cmd.append("export QHOME='{}'".format(env_cfg.get("binaryHome")))
            if env_cfg.get("licenseDir"):
                cmd.append("export QLIC='{}'".format(env_cfg.get("licenseDir")))
            if env_cfg.get("binary"):
                cmd.append(" ".join([env_cfg.get("binary", "q"), str(q_path), *options]))
            else:
                raise Exception("missing binary configuration")
        elif binary_type == "k":
            if env_cfg.get("envPath"):
                cmd.append("source " + env_cfg.get("envPath"))
            if env_cfg.get("binary"):
                cmd.append(" ".join([env_cfg.get("binary", "k"), str(k_path), *options]))
            else:
                raise Exception("missing binary configuration")
            raise Exception("k is not support yet")
    return ";".join(cmd)
