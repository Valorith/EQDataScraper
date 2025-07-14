@echo off
REM EQDataScraper Application Runner for Windows
REM Usage: run.bat [start|stop|status|install]

if "%1"=="" (
    echo Usage: run.bat [start^|stop^|status^|install]
    echo.
    echo Commands:
    echo   start   - Start both frontend and backend servers
    echo   stop    - Stop all running services
    echo   status  - Check service status
    echo   install - Install all dependencies
    exit /b 1
)

python3 run.py %1 2>nul || python run.py %1 2>nul || py -3 run.py %1