// main.js (Corrected to fix the timeout issue)

const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function getPaths() {
    const basePath = app.isPackaged
        ? process.resourcesPath
        : __dirname;

    const scriptPath = path.join(basePath, 'task_breakdown.py');

    let pythonExecutable;
    if (process.platform === 'win32') {
        pythonExecutable = path.join(basePath, 'task_breakdown_env', 'Scripts', 'python.exe');
    } else {
        pythonExecutable = path.join(basePath, 'task_breakdown_env', 'bin', 'python');
    }

    return { basePath, scriptPath, pythonExecutable };
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            webSecurity: true,
        },
        icon: path.join(__dirname, 'icon.png'),
        titleBarStyle: 'default',
        show: false,
        backgroundColor: '#667eea'
    });

    mainWindow.setMenuBarVisibility(false);
    mainWindow.loadURL('http://localhost:5000');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        if (process.platform === 'darwin') {
            app.dock.show();
        }
        mainWindow.focus();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    mainWindow.webContents.on('will-navigate', (event, url) => {
        if (url !== mainWindow.webContents.getURL()) {
            event.preventDefault();
            shell.openExternal(url);
        }
    });
}

function startPythonServer() {
    return new Promise((resolve, reject) => {
        const { basePath, scriptPath, pythonExecutable } = getPaths();

        console.log(`Using Python executable: ${pythonExecutable}`);
        console.log(`Running script: ${scriptPath}`);
        console.log(`Working directory: ${basePath}`);

        pythonProcess = spawn(pythonExecutable, [scriptPath], {
            cwd: basePath,
            stdio: 'pipe'
        });

        // --- START: MODIFIED LOGIC ---
        let serverReady = false;
        const readinessMessage = 'Running on http://';

        const onData = (data) => {
            const log = data.toString();
            // We log all output from Python for easier debugging
            console.log(`Python: ${log.trim()}`);

            // If we haven't resolved yet and the message is found, resolve the promise.
            if (!serverReady && log.includes(readinessMessage)) {
                serverReady = true;
                console.log('✅ Detected Flask server is running.');
                resolve();
            }

            // Also check for fatal Python errors
            if (log.includes('Traceback')) {
                reject(new Error(`Python script crashed: ${log}`));
            }
        };

        // Listen on BOTH stdout and stderr
        pythonProcess.stdout.on('data', onData);
        pythonProcess.stderr.on('data', onData);
        // --- END: MODIFIED LOGIC ---

        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
            if (!serverReady) {
                reject(new Error(`Python process exited unexpectedly with code ${code}`));
            }
        });
        
        // Timeout after 15 seconds ONLY if the server isn't ready
        setTimeout(() => {
            if (!serverReady) {
                reject(new Error('Python server startup timed out.'));
            }
        }, 15000).unref();
    });
}

function killPythonProcess() {
    if (pythonProcess && !pythonProcess.killed) {
        console.log('Killing Python process...');
        pythonProcess.kill();
        pythonProcess = null;
    }
}

app.on('will-quit', killPythonProcess);

app.whenReady().then(async () => {
    try {
        console.log('Starting Python server...');
        await startPythonServer();
        console.log('Python server started successfully. Creating window...');
        createWindow();
    } catch (error) {
        console.error('Failed to start application:', error);
        dialog.showErrorBox('Application Error', `Could not start the background server. Please check the logs.\n\n${error.message}`);
        app.quit();
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});