@echo off
setlocal
TITLE social-auto-upload starter

cd /d "%~dp0"

set "ROOT_DIR=%CD%"
set "PYTHON_EXE="
set "PYTHON_SOURCE="
set "VENV_PYTHON_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"
set "BACKEND_ENTRY=%ROOT_DIR%\sau_backend.py"
set "BACKEND_DEPENDENCY_CHECK=%ROOT_DIR%\scripts\check_backend_dependencies.py"
set "PYTHON_BOOTSTRAP_SCRIPT=%ROOT_DIR%\scripts\ensure-backend-python.ps1"
set "DB_INIT_SCRIPT=%ROOT_DIR%\db\createTable.py"
set "BACKEND_CONF=%ROOT_DIR%\conf.py"
set "BACKEND_CONF_TEMPLATE=%ROOT_DIR%\conf.example.py"
set "FRONTEND_DIR=%ROOT_DIR%\sau_frontend"
set "WAIT_PORT_SCRIPT=%ROOT_DIR%\scripts\wait-port.ps1"
set "FRONTEND_START_SCRIPT=%ROOT_DIR%\scripts\start-frontend-dev.ps1"
set "BACKEND_STOP_SCRIPT=%ROOT_DIR%\scripts\stop-backend-processes.ps1"
set "BACKEND_PORT=5409"
set "PYPROJECT_FILE=%ROOT_DIR%\pyproject.toml"
set "UV_LOCK_FILE=%ROOT_DIR%\uv.lock"
set "REQUIREMENTS_FILE=%ROOT_DIR%\requirements.txt"
set "PYTHONUNBUFFERED=1"

echo ==================================================
echo  Starting social-auto-upload
echo ==================================================
echo.

if not exist "%BACKEND_ENTRY%" (
    echo [ERROR] Missing backend entry: %BACKEND_ENTRY%
    goto :fail
)

if not exist "%BACKEND_DEPENDENCY_CHECK%" (
    echo [ERROR] Missing backend dependency checker: %BACKEND_DEPENDENCY_CHECK%
    goto :fail
)

if not exist "%PYTHON_BOOTSTRAP_SCRIPT%" (
    echo [ERROR] Missing Python bootstrap helper: %PYTHON_BOOTSTRAP_SCRIPT%
    goto :fail
)

if not exist "%DB_INIT_SCRIPT%" (
    echo [ERROR] Missing database init script: %DB_INIT_SCRIPT%
    goto :fail
)

if not exist "%BACKEND_CONF%" (
    if not exist "%BACKEND_CONF_TEMPLATE%" (
        echo [ERROR] Missing backend config template: %BACKEND_CONF_TEMPLATE%
        goto :fail
    )

    REM 启动脚本自动补一份默认配置，避免首次启动时因为缺少 conf.py 直接崩溃。
    echo [preflight] Missing conf.py, creating it from conf.example.py...
    copy /Y "%BACKEND_CONF_TEMPLATE%" "%BACKEND_CONF%" >nul
    if errorlevel 1 (
        echo [ERROR] Failed to create backend config: %BACKEND_CONF%
        goto :fail
    )
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

for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%PYTHON_BOOTSTRAP_SCRIPT%" -VenvPythonExe "%VENV_PYTHON_EXE%" -PyprojectFile "%PYPROJECT_FILE%" -UvLockFile "%UV_LOCK_FILE%" -RequirementsFile "%REQUIREMENTS_FILE%" -DependencyCheckScript "%BACKEND_DEPENDENCY_CHECK%"`) do %%I
if errorlevel 1 (
    echo [ERROR] Failed to prepare backend Python environment.
    goto :fail
)

echo [preflight] Initializing database schema...
"%PYTHON_EXE%" "%DB_INIT_SCRIPT%"
if errorlevel 1 (
    echo [ERROR] Failed to initialize the database schema.
    goto :fail
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
