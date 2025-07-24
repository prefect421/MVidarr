@echo off
setlocal enabledelayedexpansion

REM MVidarr Enhanced - Windows Service Management Script
REM Easy control of MVidarr service on Windows

set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

:print_success
echo [92m✅ %~1[0m
goto :eof

:print_error
echo [91m❌ %~1[0m
goto :eof

:print_warning
echo [93m⚠️  %~1[0m
goto :eof

:print_info
echo [94mℹ️  %~1[0m
goto :eof

:start_service
echo Starting MVidarr service...

REM Check if it's a scheduled task
schtasks /query /tn "MVidarr Enhanced" >nul 2>&1
if not errorlevel 1 (
    schtasks /run /tn "MVidarr Enhanced" >nul 2>&1
    if not errorlevel 1 (
        call :print_success "MVidarr task started"
        call :print_info "Access at: http://localhost:5000"
    ) else (
        call :print_error "Failed to start MVidarr task"
    )
    goto :eof
)

REM Check if it's an NSSM service
sc query MVidarr >nul 2>&1
if not errorlevel 1 (
    net start MVidarr >nul 2>&1
    if not errorlevel 1 (
        call :print_success "MVidarr service started"
        call :print_info "Access at: http://localhost:5000"
    ) else (
        call :print_error "Failed to start MVidarr service"
    )
    goto :eof
)

REM Check for startup script
if exist "start_mvidarr.bat" (
    start "MVidarr Enhanced" "start_mvidarr.bat"
    call :print_success "MVidarr started manually"
    call :print_info "Access at: http://localhost:5000"
) else (
    call :print_error "No MVidarr service or script found"
    call :print_info "Run the installer to set up auto-start"
)
goto :eof

:stop_service
echo Stopping MVidarr service...

REM Stop NSSM service
sc query MVidarr >nul 2>&1
if not errorlevel 1 (
    net stop MVidarr >nul 2>&1
    if not errorlevel 1 (
        call :print_success "MVidarr service stopped"
    ) else (
        call :print_warning "MVidarr service was not running"
    )
    goto :eof
)

REM Kill process if running
tasklist /fi "windowtitle eq MVidarr Enhanced" 2>nul | find /i "cmd.exe" >nul
if not errorlevel 1 (
    taskkill /fi "windowtitle eq MVidarr Enhanced" /f >nul 2>&1
    call :print_success "MVidarr process stopped"
) else (
    call :print_warning "MVidarr process not found"
)
goto :eof

:restart_service
call :print_info "Restarting MVidarr service..."
call :stop_service
timeout /t 2 /nobreak >nul
call :start_service
goto :eof

:status_service
echo Checking MVidarr service status...

REM Check scheduled task
schtasks /query /tn "MVidarr Enhanced" >nul 2>&1
if not errorlevel 1 (
    call :print_info "Auto-start: Scheduled Task (runs on login)"
    for /f "tokens=2 delims=:" %%i in ('schtasks /query /tn "MVidarr Enhanced" /fo list ^| find "Status"') do (
        set task_status=%%i
    )
    call :print_info "Task Status: !task_status!"
)

REM Check NSSM service
sc query MVidarr >nul 2>&1
if not errorlevel 1 (
    call :print_info "Auto-start: Windows Service (NSSM)"
    for /f "tokens=4" %%i in ('sc query MVidarr ^| find "STATE"') do (
        set service_status=%%i
    )
    call :print_info "Service Status: !service_status!"
)

REM Check if process is running
netstat -an | find "LISTENING" | find ":5000" >nul 2>&1
if not errorlevel 1 (
    call :print_success "MVidarr is running on port 5000"
    call :print_info "Access at: http://localhost:5000"
) else (
    call :print_warning "MVidarr is not running on port 5000"
)

REM Check startup script
if exist "start_mvidarr.bat" (
    call :print_info "Manual start script: start_mvidarr.bat"
)

goto :eof

:logs_service
if exist "logs\mvidarr.log" (
    call :print_info "Showing MVidarr logs (Ctrl+C to exit)..."
    powershell -Command "Get-Content 'logs\mvidarr.log' -Wait -Tail 20"
) else (
    call :print_error "Log file not found: logs\mvidarr.log"
)
goto :eof

:enable_service
REM Check if scheduled task exists
schtasks /query /tn "MVidarr Enhanced" >nul 2>&1
if not errorlevel 1 (
    schtasks /change /tn "MVidarr Enhanced" /enable >nul 2>&1
    call :print_success "MVidarr scheduled task enabled"
    goto :eof
)

REM Check if NSSM service exists
sc query MVidarr >nul 2>&1
if not errorlevel 1 (
    sc config MVidarr start= auto >nul 2>&1
    call :print_success "MVidarr service set to automatic startup"
    goto :eof
)

call :print_error "No MVidarr service found to enable"
call :print_info "Run the installer to set up auto-start"
goto :eof

:disable_service
REM Disable scheduled task
schtasks /query /tn "MVidarr Enhanced" >nul 2>&1
if not errorlevel 1 (
    schtasks /change /tn "MVidarr Enhanced" /disable >nul 2>&1
    call :print_success "MVidarr scheduled task disabled"
)

REM Disable NSSM service
sc query MVidarr >nul 2>&1
if not errorlevel 1 (
    sc config MVidarr start= demand >nul 2>&1
    call :print_success "MVidarr service set to manual startup"
)
goto :eof

:show_help
echo MVidarr Enhanced - Windows Service Management
echo Usage: %~nx0 [command]
echo.
echo Commands:
echo   start     Start MVidarr service
echo   stop      Stop MVidarr service
echo   restart   Restart MVidarr service
echo   status    Show service status
echo   logs      Show service logs (real-time)
echo   enable    Enable auto-start
echo   disable   Disable auto-start
echo   help      Show this help message
echo.
echo Examples:
echo   %~nx0 start    # Start the service
echo   %~nx0 status   # Check if running
echo   %~nx0 logs     # View logs in real-time
echo.
echo Service Management:
echo   Scheduled Task: schtasks /query /tn "MVidarr Enhanced"
echo   NSSM Service: sc query MVidarr
echo   Manual Start: start_mvidarr.bat
goto :eof

REM Main script
if "%1"=="" (
    call :show_help
    goto :end
)

if /i "%1"=="start" (
    call :start_service
) else if /i "%1"=="stop" (
    call :stop_service
) else if /i "%1"=="restart" (
    call :restart_service
) else if /i "%1"=="status" (
    call :status_service
) else if /i "%1"=="logs" (
    call :logs_service
) else if /i "%1"=="enable" (
    call :enable_service
) else if /i "%1"=="disable" (
    call :disable_service
) else if /i "%1"=="help" (
    call :show_help
) else if /i "%1"=="-h" (
    call :show_help
) else if /i "%1"=="--help" (
    call :show_help
) else (
    call :print_error "Unknown command: %1"
    echo.
    call :show_help
)

:end
pause >nul
