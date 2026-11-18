/**
 * =============================================================================
 * StudyAI — Unified Multi-Process Application Runner (start_all.js)
 * =============================================================================
 * Starts the Django backend and Vite React frontend concurrently with
 * environment-configurable hosts and ports, automatic virtual environment
 * resolution, migration checking, health probing, and unified graceful shutdown.
 * =============================================================================
 */

import { spawn, spawnSync, execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import http from 'http';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isBackendOnly = process.argv.includes('--backend-only');
const isFrontendOnly = process.argv.includes('--frontend-only');
const noBrowser = process.argv.includes('--no-browser');

// Configurable network host and ports
const BACKEND_PORT = process.env.BACKEND_PORT || process.env.PORT || '8000';
const BACKEND_HOST = process.env.BACKEND_HOST || '127.0.0.1';
const FRONTEND_PORT = process.env.FRONTEND_PORT || process.env.VITE_PORT || '5173';
const FRONTEND_HOST = process.env.FRONTEND_HOST || process.env.VITE_HOST || '127.0.0.1';

// Automatically open default browser (Windows/Mac/Linux)
function openBrowser(url) {
  if (noBrowser) return;
  try {
    const isWindows = process.platform === 'win32';
    const isMac = process.platform === 'darwin';
    if (isWindows) {
      execSync(`start "" "${url}"`, { stdio: 'ignore' });
    } else if (isMac) {
      execSync(`open "${url}"`, { stdio: 'ignore' });
    } else {
      execSync(`xdg-open "${url}"`, { stdio: 'ignore' });
    }
  } catch {
    // Ignore error if browser launch command is unavailable
  }
}

// 1. Resolve Python executable
function getPythonExecutable() {
  const candidates = [
    path.join(__dirname, '.venv', 'Scripts', 'python.exe'),
    path.join(__dirname, '.venv', 'bin', 'python'),
    path.join(__dirname, 'backend', 'venv', 'Scripts', 'python.exe'),
    path.join(__dirname, 'backend', 'venv', 'bin', 'python'),
    path.join(__dirname, 'venv', 'Scripts', 'python.exe'),
    path.join(__dirname, 'venv', 'bin', 'python'),
    'python',
    'python3',
    'py'
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate) || !path.isAbsolute(candidate)) {
      try {
        const res = spawnSync(candidate, ['-c', 'import django; print("ok")'], { stdio: 'pipe' });
        if (res.status === 0) {
          return { path: candidate, ok: true };
        }
      } catch {
        // Not a working django python
      }
    }
  }

  // Fallback to first existing candidate or default
  for (const c of candidates) {
    if (fs.existsSync(c)) return { path: c, ok: false };
  }
  return { path: 'python', ok: false };
}

const pyResolved = getPythonExecutable();
const pythonExe = pyResolved.path;
const backendDir = path.join(__dirname, 'backend');
const frontendDir = fs.existsSync(path.join(__dirname, 'frontend')) ? path.join(__dirname, 'frontend') : __dirname;

console.log('================================================================');
console.log('  StudyAI — AI Study Analyzer & Personalized Exam Generator');
console.log('================================================================');
console.log(`[Runtime] Python executable: ${pythonExe}`);
console.log(`[Runtime] Backend root:       ${backendDir} (Host: ${BACKEND_HOST}:${BACKEND_PORT})`);
console.log(`[Runtime] Frontend root:      ${frontendDir} (Host: ${FRONTEND_HOST}:${FRONTEND_PORT})`);

// 2. Health check helper
function pingBackend(timeoutMs = 2000) {
  return new Promise((resolve) => {
    const probeHost = BACKEND_HOST === '0.0.0.0' ? '127.0.0.1' : BACKEND_HOST;
    const req = http.get(`http://${probeHost}:${BACKEND_PORT}/api/health/`, { timeout: timeoutMs }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Track active child processes
const children = [];

function cleanup() {
  console.log('\n[StudyAI] Shutting down all processes cleanly...');
  for (const child of children) {
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /pid ${child.pid} /T /F`, { stdio: 'ignore' });
      } else {
        child.kill('SIGINT');
      }
    } catch {
      // Process might already be stopped
    }
  }
  process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', () => {});

async function main() {
  if (!isFrontendOnly) {
    if (!pyResolved.ok) {
      console.warn('\x1b[33m[Notice] Django was not detected with the resolved python executable.\x1b[0m');
      console.warn('If startup fails, run setup first: setup_studyai.bat or ./setup_studyai.sh\n');
    }

    // 3. Migrate DB if needed
    console.log('[1/2] Checking database migrations...');
    try {
      execSync(`"${pythonExe}" manage.py migrate --noinput`, {
        cwd: backendDir,
        stdio: 'inherit'
      });
      console.log('[1/2] Database ready (SQLite / Postgres).');
    } catch (err) {
      console.warn('[WARNING] Migration warning; continuing with existing SQLite database.');
    }

    // 4. Start Django Backend
    const backendBind = `${BACKEND_HOST}:${BACKEND_PORT}`;
    console.log(`[2/2] Launching Django backend on http://${backendBind} ...`);
    const backendProc = spawn(pythonExe, ['manage.py', 'runserver', backendBind], {
      cwd: backendDir,
      stdio: ['pipe', 'inherit', 'inherit']
    });
    children.push(backendProc);

    backendProc.on('error', (err) => {
      console.error('[Backend Error] Failed to start Django:', err.message);
    });

    backendProc.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        console.error(`[Backend] Django server exited with code ${code}`);
      }
    });

    // Wait for Django to be responsive
    let healthy = false;
    for (let i = 0; i < 20; i++) {
      await new Promise((r) => setTimeout(r, 600));
      healthy = await pingBackend(1000);
      if (healthy) break;
    }

    const displayBackend = BACKEND_HOST === '0.0.0.0' ? 'localhost' : BACKEND_HOST;
    if (healthy) {
      console.log('================================================================');
      console.log(`  \x1b[32m✔ Django Backend is ONLINE\x1b[0m at http://${displayBackend}:${BACKEND_PORT}/`);
      console.log(`  \x1b[32m✔ API Health Check:\x1b[0m http://${displayBackend}:${BACKEND_PORT}/api/health/`);
      console.log('================================================================');
    } else {
      console.warn(`[Notice] Backend process started; waiting for requests at http://${displayBackend}:${BACKEND_PORT}/`);
    }
  }

  if (!isBackendOnly) {
    // 5. Start Vite Frontend
    const viteBin = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js');
    let viteProc;

    const frontendEnv = {
      ...process.env,
      VITE_PORT: FRONTEND_PORT,
      VITE_HOST: FRONTEND_HOST
    };

    if (fs.existsSync(viteBin)) {
      viteProc = spawn(process.execPath, [viteBin, '--host', FRONTEND_HOST, '--port', FRONTEND_PORT], {
        cwd: frontendDir,
        env: frontendEnv,
        stdio: 'inherit'
      });
    } else {
      const isWindows = process.platform === 'win32';
      const npmCmd = isWindows ? 'npx.cmd' : 'npx';
      viteProc = spawn(npmCmd, ['vite', '--host', FRONTEND_HOST, '--port', FRONTEND_PORT], {
        cwd: frontendDir,
        env: frontendEnv,
        stdio: 'inherit',
        shell: isWindows
      });
    }

    children.push(viteProc);

    viteProc.on('error', (err) => {
      console.error('[Frontend Error] Failed to start Vite:', err.message);
    });

    viteProc.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        console.error(`[Frontend] Vite server exited with code ${code}`);
      }
    });

    const displayFrontend = FRONTEND_HOST === '0.0.0.0' ? 'localhost' : FRONTEND_HOST;
    const browserUrl = `http://${displayFrontend}:${FRONTEND_PORT}/`;

    setTimeout(() => {
      console.log('\n================================================================');
      console.log('  \x1b[32m🚀 StudyAI IS LIVE!\x1b[0m');
      console.log(`  \x1b[36m👉 Opening browser at: ${browserUrl}\x1b[0m`);
      console.log(`  \x1b[90mBackend running at:   http://${BACKEND_HOST === '0.0.0.0' ? 'localhost' : BACKEND_HOST}:${BACKEND_PORT}/\x1b[0m`);
      console.log('================================================================\n');
      openBrowser(browserUrl);
    }, 1500);
  }
}

main().catch((err) => {
  console.error('[Fatal Error]', err);
  cleanup();
});
