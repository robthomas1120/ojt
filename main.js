const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('index.html');

    if (isDev) {
        mainWindow.webContents.openDevTools();
    }
}

function startPythonProcess() {
    // Path to the Python executable in your virtual environment
    const pythonPath = isDev 
        ? 'venv/bin/python'  // Development environment
        : path.join(process.resourcesPath, 'venv/bin/python');  // Production environment

    // Path to your script
    const scriptPath = isDev
        ? 'script.py'
        : path.join(process.resourcesPath, 'script.py');

    pythonProcess = spawn(pythonPath, [scriptPath]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });
}

app.whenReady().then(() => {
    createWindow();
    startPythonProcess();

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
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

process.on('exit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});