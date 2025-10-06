#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for z-ai2api-python
Fallback for older pip versions that don't support pyproject.toml
"""

from setuptools import setup, find_packages

# Read the README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "OpenAI-compatible multi-provider AI API server"

# Read requirements
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "fastapi>=0.116.1",
        "granian[reload,pname]>=2.5.2",
        "httpx>=0.28.1",
        "pydantic>=2.11.7",
        "pydantic-settings>=2.10.1",
        "rich>=13.7.0",
    ]

setup(
    name="z-ai2api-python",
    version="0.2.0",
    author="Z.AI2API Contributors",
    description="OpenAI-compatible multi-provider AI API server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Zeeeepa/z.ai2api_python",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "z-ai2api=app.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

