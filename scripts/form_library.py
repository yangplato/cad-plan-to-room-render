#!/usr/bin/env python3
"""Thin local adapter to the independent form library; preserves existing tools."""
import os
from pathlib import Path
import runpy
import sys

configured = os.environ.get('INTERIOR_FORM_LIBRARY_ROOT')
library = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[3] / '05-室内设计造型知识库'
script = library / '辅助资料' / 'formlib.py'
if not script.is_file():
    sys.stderr.write('未找到独立室内设计造型库。请保留同级项目目录，或设置 INTERIOR_FORM_LIBRARY_ROOT。\n')
    sys.exit(2)
sys.argv = [str(script), '--root', str(library.resolve()), *sys.argv[1:]]
runpy.run_path(str(script), run_name='__main__')
