#!/usr/bin/env python3
"""Обёртка: python meta/scripts/run_comment_moderation.py"""
from pathlib import Path
import runpy
import sys

sys.argv[0] = str(Path(__file__).resolve())
runpy.run_path(str(Path(__file__).resolve().parents[1] / "src/comment_moderation/__main__.py"), run_name="__main__")
