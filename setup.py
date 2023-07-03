import sys

from setuptools import setup

if sys.version_info[:3] < (3, 7):
    raise RuntimeError("Python version >= 3.7 required.")

setup(
    entry_points={
        "console_scripts": [
            "kuki=kuki.kuki:main",
            "ktrl=kuki.ktrl:main",
            "kest=kuki.kest:main",
        ],
    },
)
