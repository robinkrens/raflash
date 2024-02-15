#!/usr/bin/env python3
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "raflash",
    version = "0.0.1",
    author = "Robin Krens",
    description = ("Flasher for the built in ROM bootloader for Renesas RA microcontrollers"),
    license = "GNU",
    keywords = "Renesas RA chipset flasher",
    packages=['src', 'tests'],
    entry_points={
        'console_scripts': [
            'raflash = src.RAFlasher:main',
        ],
    },
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1",
    ],
)
