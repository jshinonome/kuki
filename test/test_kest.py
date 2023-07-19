import logging

from kuki.util import generate_process_options

logger = logging.getLogger(__name__)


def test_load_kest_json():
    kest_json = {
        "console_size": [50, 160],
        "error_traps": "suspend",
        "garbage_collection": "immediate",
        "memory_limit": 30,
        "offset_time": 8,
        "port": 1800,
        "precision": 3,
        "quiet": True,
        "threads": 3,
        "timeout": 10,
        "timer_period": 1000,
        "disable_system_cmd": 1,
        "replicate": ":localhost:1800",
        "tls": "mixed",
        "blocked": True,
    }

    expect_args = [
        "-c",
        "50 160",
        "-e",
        "1",
        "-g",
        "1",
        "-w",
        "30",
        "-o",
        "8",
        "-p",
        "1800",
        "-P",
        "3",
        "-q",
        "-s",
        "3",
        "-T",
        "10",
        "-t",
        "1000",
        "-u",
        "1",
        "-r",
        ":localhost:1800",
        "-E",
        "1",
        "-b",
    ]
    assert generate_process_options([], kest_json) == expect_args


def test_skip_args():
    kest_json = {
        "console_size": [50, 160],
        "error_traps": "suspend",
        "garbage_collection": "immediate",
    }
    args = ["-c", "100 320"]

    expect_args = [
        "-e",
        "1",
        "-g",
        "1",
    ]
    assert generate_process_options(args, kest_json) == expect_args
