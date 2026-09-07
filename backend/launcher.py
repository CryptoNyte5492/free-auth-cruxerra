import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

execute_from_command_line([
    "manage.py",
    "runserver",
    "127.0.0.1:8000",
    "--noreload",
])