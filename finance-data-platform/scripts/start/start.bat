@echo off
REM Automotive Finance Data Platform - Docker Startup (Windows)
REM Starts the complete platform from the repository root.

setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..\..") do set "REPO_ROOT=%%~fI"

echo.
echo Automotive Finance Data Platform - Docker Startup
echo =================================================
echo.

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Docker not found. Install Docker Desktop first.
    exit /b 1
)

docker compose version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "COMPOSE_CMD=docker compose"
) else (
    where docker-compose >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Neither 'docker compose' nor 'docker-compose' is available.
        exit /b 1
    )
    set "COMPOSE_CMD=docker-compose"
)

if not exist "%REPO_ROOT%\.env" (
    echo .env file not found in %REPO_ROOT%
    if exist "%REPO_ROOT%\.env.example" (
        echo Creating .env from .env.example...
        copy "%REPO_ROOT%\.env.example" "%REPO_ROOT%\.env" >nul
        echo Created .env. Update it with real credentials before running the pipeline.
    ) else (
        echo .env.example not found in %REPO_ROOT%
        exit /b 1
    )
)

echo Starting Docker services from %REPO_ROOT%
pushd "%REPO_ROOT%"
call %COMPOSE_CMD% -f docker-compose.yml up -d
if %ERRORLEVEL% NEQ 0 (
    popd
    exit /b 1
)

echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo.
echo Active services:
call %COMPOSE_CMD% -f docker-compose.yml ps
echo.
echo Airflow UI: http://localhost:8081
echo Next steps:
echo   1. Open the Airflow UI.
echo   2. Enable the automotive_finance_orchestration DAG.
echo   3. Upload files to the RAW bucket.
echo.
echo Stop services with:
echo   %COMPOSE_CMD% -f docker-compose.yml down
popd

endlocal