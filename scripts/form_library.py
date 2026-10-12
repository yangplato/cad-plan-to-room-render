#!/usr/bin/env python3
"""Use the configured, existing local, or bundled form library."""
import os
from pathlib import Path
import runpy
import sys

def main():
    skill = Path(__file__).resolve().parent.parent
    configured = os.environ.get('INTERIOR_FORM_LIBRARY_ROOT')
    local = skill.parent.parent / '05-室内设计造型知识库'
    bundled = skill / 'references' / 'form-library'
    if configured:
        library = Path(configured).expanduser()
    elif (local / '辅助资料' / 'formlib.py').is_file():
        library = local
    else:
        library = bundled
    script = library / '辅助资料' / 'formlib.py'
    if not script.is_file():
        sys.stderr.write('未找到造型库检索工具。检查 INTERIOR_FORM_LIBRARY_ROOT 配置，或重新解压完整Skill包。\n')
        return 2
    sys.argv = [str(script), '--root', str(library.resolve()), *sys.argv[1:]]
    runpy.run_path(str(script), run_name='__main__')
    return 0


if __name__ == '__main__':
    sys.exit(main())
