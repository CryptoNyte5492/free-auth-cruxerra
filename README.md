# Cruxerra Coach desktop release

Cruxerra Coach is an Electron app that starts a local Django server. It has no
sign-up or login screen. Each installed copy stores its own SQLite database and
uploaded CSV files in that Windows user's application-data folder; no separate
server or PostgreSQL installation is needed.

## Build a Windows installer

Run these commands on a Windows computer, from a fresh copy of this project.
Install Python 3.12 and Node.js 22.13 or newer in the 22.x line first.

```powershell
cd backend
./build_windows.ps1
cd ../frontend
npm ci
npm run build:win
```

Send the generated installer in `frontend/release` to the coach.  It installs
Cruxerra and creates a normal Start-menu application entry.

The generated `backend/dist/CruxerraBackend.exe` must be built on Windows. A
Mac executable cannot run on Windows, and PyInstaller does not cross-compile
it reliably.

The script requires Python 3.12. Check that it is installed with
`py -3.12 --version` before building.

## First use

The coach can open the app and upload CSVs immediately. The app is completely
local, so its files and data do not sync between computers.
