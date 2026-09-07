const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const fs = require("fs");

let djangoProcess;
let backendLogPath;

function logBackend(message) {
    const line = `[${new Date().toISOString()}] ${message}\n`;
    console.log(line.trim());
    fs.appendFileSync(backendLogPath, line, "utf8");
}

function startDjango() {
    const backendName =
        process.platform === "win32"
            ? "CruxerraBackend.exe"
            : "cruxerra-backend";

    const backendDirectory = app.isPackaged
        ? path.join(process.resourcesPath, "backend")
        : path.join(__dirname, "..", "..", "backend", "dist");
    const backendPath = path.join(backendDirectory, backendName);

    logBackend(`Starting backend: ${backendPath}`);

    if (!fs.existsSync(backendPath)) {
        logBackend("ERROR: Backend executable was not found.");
        return;
    }

    djangoProcess = spawn(backendPath, [], {
        shell: false,
        env: {
            ...process.env,
            // Program Files is read-only, so keep the local database and CSVs
            // in the coach's per-user application-data directory.
            CRUXERRA_DATA_DIR: app.getPath("userData"),
        },
    });

    djangoProcess.stdout.on("data", (data) => {
        logBackend(`Django: ${data}`);
    });

    djangoProcess.stderr.on("data", (data) => {
        logBackend(`Django error: ${data}`);
    });

    djangoProcess.on("error", (error) => {
        logBackend(`ERROR: Failed to start backend: ${error.stack || error}`);
    });

    djangoProcess.on("exit", (code, signal) => {
        logBackend(`Backend exited (code: ${code}, signal: ${signal || "none"}).`);
    });
}

function waitForBackend(timeoutMs = 30000) {
    const startedAt = Date.now();

    return new Promise((resolve, reject) => {
        const attempt = () => {
            const request = http.get("http://127.0.0.1:8000/api/", (response) => {
                // A 404 is fine here: it proves Django is listening.
                response.resume();
                resolve();
            });

            request.on("error", () => {
                if (Date.now() - startedAt >= timeoutMs) {
                    reject(new Error("The local Cruxerra server did not start."));
                    return;
                }
                setTimeout(attempt, 250);
            });
            request.setTimeout(1000, () => request.destroy());
        };
        attempt();
    });
}

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        }
    });

    mainWindow.loadFile(
        path.join(app.getAppPath(), "renderer", "index.html")
    );

    if (!app.isPackaged) {
        mainWindow.webContents.openDevTools();
    }
}

app.whenReady().then(async () => {
    backendLogPath = path.join(app.getPath("userData"), "backend.log");
    logBackend("Cruxerra started.");
    startDjango();
    try {
        await waitForBackend();
    } catch (error) {
        logBackend(`ERROR: ${error.message}`);
        dialog.showErrorBox(
            "Cruxerra could not start",
            `The local server did not start.\n\nPlease send this log file to the developer:\n${backendLogPath}`
        );
        app.quit();
        return;
    }
    createWindow();
});

app.on("window-all-closed", () => {
    if (djangoProcess) {
        djangoProcess.kill();
    }

    if (process.platform !== "darwin") {
        app.quit();
    }
});
