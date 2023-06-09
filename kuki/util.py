from argparse import Namespace
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
    "error_traps": "none",
    "garbage_collection": "deferred",
    "memory_limit": 0,
    "offset_time": 0,
    "port": 31800,
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


def generate_cmd(args: Namespace) -> List[str]:
    input_args = vars(args)
    input_args.pop("init")
    cmd = []
    for key, value in PROCESS_DEFAULT.items():
        if key not in input_args or value == input_args[key]:
            continue

        cmd.append("-" + CMD_OPTION_MAP[key])
        arg = input_args[key]
        if key == "error_traps":
            cmd.append(["none", "suspend", "dump"].index(arg))
        elif key == "garbage_collection":
            cmd.append(["deferred", "immediate"].index(arg))
        elif key == "tls":
            cmd.append(["plain", "mixed", "tls"].index(arg))
        elif key == "consoleSize":
            cmd.append(" ".join([str(c) for c in arg]))
        elif key in ["quiet", "blocked"] and not arg:
            cmd.remove("-" + CMD_OPTION_MAP[key])
        elif key == "replicate":
            cmd.append(arg)
        else:
            cmd.append(str(arg))
    return cmd
