#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def _get_project_python():
    project_dir = Path(__file__).resolve().parent
    windows_python = project_dir / '.venv' / 'Scripts' / 'python.exe'
    unix_python = project_dir / '.venv' / 'bin' / 'python'

    if windows_python.exists():
        return windows_python
    if unix_python.exists():
        return unix_python
    return None


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        project_python = _get_project_python()
        current_python = Path(sys.executable).resolve()

        if project_python and current_python != project_python.resolve():
            os.execv(str(project_python), [str(project_python), __file__, *sys.argv[1:]])

        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
