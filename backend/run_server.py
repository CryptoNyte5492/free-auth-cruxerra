import os
import sys
from django.core.management import execute_from_command_line


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

    # A coach's installed desktop app starts with an empty local database.
    # Apply Django's schema before accepting requests from Electron.
    execute_from_command_line([
        "manage.py",
        "migrate",
        "--noinput",
    ])

    execute_from_command_line([
        "manage.py",
        "runserver",
        "127.0.0.1:8000",
        "--noreload",
    ])
