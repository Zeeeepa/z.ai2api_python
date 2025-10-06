#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
z-ai2api-python: OpenAI-compatible multi-provider AI API server
"""

__version__ = "0.2.0"
__author__ = "Z.AI2API Contributors"
__license__ = "MIT"

from app import core, models, utils

__all__ = ["core", "models", "utils", "__version__"]
