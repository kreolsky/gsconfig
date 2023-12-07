#!/usr/bin/env python

import os.path
import re
import sys
from setuptools import setup, find_packages

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel')
    sys.exit()

def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


description = 'Game Config Tools over gspread (Google Spreadsheets library).'
version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                    read('gsconfig/__init__.py'), re.MULTILINE).group(1)

setup(
    name='gsconfig',
    packages=find_packages(),
    description=description,
    version=version,
    author='Serge Zaigraeff',
    author_email='zaigraeff@gmail.com',
    url='https://github.com/kreolsky/gsconfig',
    keywords=['spreadsheets', 'google-spreadsheets', 'game-config'],
    install_requires=['gspread'],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Topic :: Gamedesign :: Spreadsheet",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    license='MIT'
    )
