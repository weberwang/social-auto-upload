@echo off
setlocal
TITLE social-auto-upload starter

cd /d "%~dp0"

set "ROOT_DIR=%CD%"
set "PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
set "BACKEND_ENTRY=%ROOT_DIR%\sau_backend.py"
set "BACKEND_DEPENDENCY_CHECK=%ROOT_DIR%\scripts\check_backend_dependencies.py"
set "FRONTEND_DIR=%ROOT_DIR%\sau_frontend"
set "WAIT_PORT_SCRIPT=%ROOT_DIR%\scripts\wait-port.ps1"
set "FRONTEND_START_SCRIPT=%ROOT_DIR%\scripts\start-frontend-dev.ps1"
set "BACKEND_STOP_SCRIPT=%ROOT_DIR%\scripts\stop-backend-processes.ps1"
set "BACKEND_PORT=5409"
set "REQUIREMENTS_FILE=%ROOT_DIR%\requirements.txt"
set "PYTHONUNBUFFERED=1"

echo ==================================================
echo  Starting social-auto-upload
echo ==================================================
echo.

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Missing virtualenv interpreter: %PYTHON_EXE%
    echo [HINT] Create the project .venv before running this script.
    goto :fail
)

if not exist "%BACKEND_ENTRY%" (
    echo [ERROR] Missing backend entry: %BACKEND_ENTRY%
    goto :fail
)

if not exist "%BACKEND_DEPENDENCY_CHECK%" (
    echo [ERROR] Missing backend dependency checker: %BACKEND_DEPENDENCY_CHECK%
    goto :fail
)

if not exist "%WAIT_PORT_SCRIPT%" (
    echo [ERROR] Missing port wait helper: %WAIT_PORT_SCRIPT%
    goto :fail
)

if not exist "%FRONTEND_START_SCRIPT%" (
    echo [ERROR] Missing frontend start helper: %FRONTEND_START_SCRIPT%
    goto :fail
)

if not exist "%BACKEND_STOP_SCRIPT%" (
    echo [ERROR] Missing backend stop helper: %BACKEND_STOP_SCRIPT%
    goto :fail
)

if not exist "%REQUIREMENTS_FILE%" (
    echo [ERROR] Missing requirements file: %REQUIREMENTS_FILE%
    goto :fail
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] Missing frontend directory: %FRONTEND_DIR%
    goto :fail
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm was not found. Install Node.js and make sure npm is on PATH.
    goto :fail
)

echo [preflight] Checking backend Python dependencies...
"%PYTHON_EXE%" "%BACKEND_DEPENDENCY_CHECK%"
if errorlevel 1 (
    echo [INFO] Backend dependencies are incomplete. Installing from requirements.txt...
    "%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies.
        goto :fail
    )

    echo [preflight] Re-checking backend Python dependencies...
    "%PYTHON_EXE%" "%BACKEND_DEPENDENCY_CHECK%"
    if errorlevel 1 (
        echo [ERROR] Backend dependencies are still incomplete after installation.
        goto :fail
    )
)

echo [0/2] Stopping old backend processes...
powershell -NoProfile -ExecutionPolicy Bypass -File "%BACKEND_STOP_SCRIPT%" -BackendEntry "%BACKEND_ENTRY%" -BackendPort %BACKEND_PORT%
if errorlevel 1 (
    echo [ERROR] Failed to stop old backend processes.
    goto :fail
)

echo [1/2] Starting frontend window...
start "SAU Frontend" powershell -NoProfile -ExecutionPolicy Bypass -File "%FRONTEND_START_SCRIPT%" -FrontendDir "%FRONTEND_DIR%" -WaitPortScript "%WAIT_PORT_SCRIPT%" -BackendPort %BACKEND_PORT%

echo.
echo ==================================================
echo  Frontend window has been started
echo  Backend will run in this window with live logs
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:%BACKEND_PORT%
echo ==================================================
echo.

echo [2/2] Starting backend in current window...
echo [INFO] Keep this window open to view backend logs.
echo [INFO] Running: "%PYTHON_EXE%" -u "%BACKEND_ENTRY%"
echo.
"%PYTHON_EXE%" -u "%BACKEND_ENTRY%"
if errorlevel 1 (
    echo.
    echo [ERROR] Backend exited unexpectedly. Press any key to exit...
    pause >nul
    exit /b 1
)

exit /b 0

:fail
echo.
echo Startup failed. Press any key to exit...
pause >nul
exit /b 1
