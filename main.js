const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;
let pythonProcess;
let serverCheckInterval;

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
}

function checkFlaskServer() {
    return new Promise((resolve) => {
        http.get('http://127.0.0.1:5000/clean', (res) => {
            if (res.statusCode === 404 || res.statusCode === 405) {
                clearInterval(serverCheckInterval);
                console.log('Flask server is ready');
                resolve(true);
            }
            res.resume();
        }).on('error', () => {
            resolve(false);
        });
    });
}

async function waitForFlaskServer() {
    let attempts = 0;
    const maxAttempts = 30;

    while (attempts < maxAttempts) {
        const isReady = await checkFlaskServer();
        if (isReady) {
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
    }
    return false;
}

async function startPythonProcess() {
    try {
        let pythonPath;
        let scriptPath;
        
        if (isDev) {
            // Development paths
            pythonPath = process.platform === 'win32'
                ? path.join(__dirname, 'myenv', 'Scripts', 'python.exe')
                : path.join(__dirname, 'myenv', 'bin', 'python3');
            scriptPath = path.join(__dirname, 'app.py');
        } else {
            // Production paths
            const resourcePath = process.platform === 'darwin'
                ? path.join(process.resourcesPath, '..', 'Resources')
                : process.resourcesPath;

            pythonPath = process.platform === 'win32'
                ? path.join(resourcePath, 'myenv', 'Scripts', 'python.exe')
                : path.join(resourcePath, 'myenv', 'bin', 'python3');
            scriptPath = path.join(resourcePath, 'app.py');
        }

        console.log('Python Path:', pythonPath);
        console.log('Script Path:', scriptPath);
        console.log('Current directory:', __dirname);
        console.log('Resource path:', process.resourcesPath);

        // Verify files exist
        if (!fs.existsSync(pythonPath)) {
            throw new Error(`Python executable not found at: ${pythonPath}`);
        }
        if (!fs.existsSync(scriptPath)) {
            throw new Error(`Script not found at: ${scriptPath}`);
        }

        // Start Python process
        pythonProcess = spawn(pythonPath, [scriptPath], {
            stdio: 'pipe',
            env: { 
                ...process.env, 
                PYTHONUNBUFFERED: '1',
                PATH: process.env.PATH
            }
        });

        pythonProcess.stdout.on('data', (data) => {
            console.log(`Python stdout: ${data}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python stderr: ${data}`);
        });

        pythonProcess.on('error', (err) => {
            console.error('Failed to start Python process:', err);
            dialog.showErrorBox('Python Error', `Failed to start Python process: ${err.message}`);
        });

        // Wait for Flask server to be ready
        const serverReady = await waitForFlaskServer();
        if (!serverReady) {
            throw new Error('Flask server failed to start within the timeout period');
        }

    } catch (error) {
        console.error('Error starting Python:', error);
        dialog.showErrorBox('Setup Error', error.message);
        throw error;
    }
}

// When Electron is ready
app.whenReady().then(async () => {
    try {
        await startPythonProcess();
        createWindow();
    } catch (error) {
        console.error('Failed to start application:', error);
        app.quit();
    }
});

// Cleanup on exit
app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    clearInterval(serverCheckInterval);
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

process.on('exit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    clearInterval(serverCheckInterval);
});
