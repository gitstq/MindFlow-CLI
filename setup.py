#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setup.py - Installation configuration for mindflow-cli.

Lightweight AI Knowledge Workflow Automation Engine.
"""

from setuptools import setup, find_packages

setup(
    name="mindflow-cli",
    version="1.0.0",
    description="Lightweight AI Knowledge Workflow Automation Engine",
    long_description=open("README.md", encoding="utf-8").read() if True else "",
    long_description_content_type="text/markdown",
    author="gitstq",
    author_email="",
    url="https://github.com/gitstq/mindflow-cli",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "mindflow=mindflow_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
    ],
    keywords=["mindflow", "knowledge", "workflow", "automation", "ai", "cli"],
    project_urls={
        "Bug Reports": "https://github.com/gitstq/mindflow-cli/issues",
        "Source": "https://github.com/gitstq/mindflow-cli",
    },
)
