import logging

from kuki.kest import parser
from kuki.util import generate_options

logger = logging.getLogger(__name__)


def test_parser():
    actual_args1 = parser.parse_args(
        [
            "-e",
            "suspend",
            "--tls",
            "mixed",
            "-g",
            "immediate",
            "-o",
            "8",
            "-p",
            "1800",
            "--precision",
            "3",
            "-q",
            "-s",
            "3",
            "-t",
            "1000",
            "--timeout",
            "10",
            "-w",
            "30",
        ]
    )
    actual_args2 = parser.parse_args(
        [
            "--errorTraps",
            "suspend",
            "--tls",
            "mixed",
            "--gc",
            "immediate",
            "--offsetTime",
            "8",
            "--port",
            "1800",
            "--precision",
            "3",
            "--quiet",
            "--threads",
            "3",
            "--timerPeriod",
            "1000",
            "--timeout",
            "10",
            "--memoryLimit",
            "30",
        ]
    )
    expect_args = [
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
        "True",
        "-s",
        "3",
        "-T",
        "10",
        "-t",
        "1000",
        "-E",
        "1",
    ]
    assert generate_options(actual_args1) == expect_args
    assert generate_options(actual_args2) == expect_args
