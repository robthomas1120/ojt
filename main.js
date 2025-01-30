const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const isDev = process.env.NODE_ENV !== 'production';

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false
        }
    });

    mainWindow.loadFile('index.html');
    mainWindow.webContents.openDevTools();
}

function startPythonProcess() {
    try {
        // Changed script.py to app.py
        const pythonPath = path.join(__dirname, 'myenv', 'bin', 'python3');
        const scriptPath = path.join(__dirname, 'app.py');

        console.log('Current directory:', __dirname);
        console.log('Looking for Python at:', pythonPath);
        console.log('Looking for script at:', scriptPath);

        // Check if files exist
        if (!fs.existsSync(pythonPath)) {
            throw new Error(`Python not found at: ${pythonPath}\nPlease ensure your virtual environment is set up correctly.`);
        }
        if (!fs.existsSync(scriptPath)) {
            throw new Error(`Script not found at: ${scriptPath}`);
        }

        // Start Python process
        pythonProcess = spawn(pythonPath, [scriptPath], {
            stdio: 'pipe',
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

        pythonProcess.stdout.on('data', (data) => {
            console.log(`Python stdout: ${data.toString()}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python stderr: ${data.toString()}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
            if (code !== 0) {
                dialog.showErrorBox('Python Error', 
                    `Python process exited with code ${code}. Check the console for details.`);
            }
        });

        pythonProcess.on('error', (err) => {
            console.error('Failed to start Python process:', err);
            dialog.showErrorBox('Python Error', 
                `Failed to start Python process: ${err.message}`);
        });

    } catch (error) {
        console.error('Error starting Python:', error);
        dialog.showErrorBox('Setup Error', error.message);
    }
}

// When Electron is ready
app.whenReady().then(() => {
    createWindow();
    startPythonProcess();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Cleanup on exit
app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

process.on('exit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});