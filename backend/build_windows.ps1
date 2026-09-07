$ErrorActionPreference = "Stop"

# Run this script in PowerShell from the backend folder on Windows.
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --clean --onefile --name CruxerraBackend run_server.py
