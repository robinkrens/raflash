#!/usr/bin/env python3
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="raflash",
    version="0.0.1",
    author="Robin Krens",
    description=("Flasher for the built in ROM bootloader for Renesas RA microcontrollers"),
    license="GNU",
    keywords="Renesas RA chipset flasher",
    packages=['raflash', 'tests'],
    install_requires=[
        'exceptiongroup>=1.2.0',
        'future>=0.18.3',
        'iniconfig>=2.0.0',
        'iso8601>=2.1.0',
        'packaging>=23.2',
        'pluggy>=1.4.0',
        'pytest>=8.0.0',
        'pyusb>=1.2.1',
        'PyYAML>=6.0.1',
        'tomli>=2.0.1',
        'tqdm>=4.66.2',
    ],
    entry_points={
        'console_scripts': [
            'raflash = raflash.RAFlasher:main',
        ],
    },
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1",
    ],
)
