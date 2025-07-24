@echo off
setlocal enabledelayedexpansion

REM MVidarr Enhanced v2.0 - Windows Installation Script
REM This script handles the complete setup of MVidarr Enhanced on Windows

echo.
echo ===============================================
echo  MVidarr Enhanced v2.0 - Installation Script
echo ===============================================
echo.
echo This script will install and configure MVidarr Enhanced
echo Press Ctrl+C to cancel, or press any key to continue...
pause >nul

REM Configuration
set PYTHON_MIN_VERSION=3.8
set MVIDARR_DIR=%CD%

REM Colors (limited on Windows CMD)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set PURPLE=[95m
set CYAN=[96m
set NC=[0m

REM Function to print colored output (limited)
:print_step
echo [94m🔧 %~1[0m
goto :eof

:print_success
echo [92m✅ %~1[0m
goto :eof

:print_warning
echo [93m⚠️  %~1[0m
goto :eof

:print_error
echo [91m❌ %~1[0m
goto :eof

:print_header
echo.
echo [96m==================================================[0m
echo [96m%~1[0m
echo [96m==================================================[0m
goto :eof

REM Check if Python is installed and get version
:check_python
call :print_step "Checking Python installation..."

python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        call :print_error "Python not found. Please install Python 3.8+ first."
        goto :error_exit
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Check Python version
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i

REM Extract major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    call :print_error "Python %PYTHON_VERSION% found, but Python 3.8+ is required"
    goto :error_exit
)

if %MAJOR% EQU 3 if %MINOR% LSS 8 (
    call :print_error "Python %PYTHON_VERSION% found, but Python 3.8+ is required"
    goto :error_exit
)

call :print_success "Python %PYTHON_VERSION% found"
goto :eof

REM Install pip if not available
:install_pip
call :print_step "Installing pip..."

REM Try to install pip using get-pip.py
curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
if errorlevel 1 (
    call :print_warning "Failed to download get-pip.py, trying alternative method..."
    REM Try using python -m ensurepip
    %PYTHON_CMD% -m ensurepip --upgrade 2>nul
    if errorlevel 1 (
        call :print_error "Failed to install pip using ensurepip"
        goto :eof
    ) else (
        call :print_success "pip installed using ensurepip"
        goto :eof
    )
)

%PYTHON_CMD% get-pip.py
if errorlevel 1 (
    call :print_error "Failed to install pip using get-pip.py"
    del get-pip.py 2>nul
    goto :eof
)

del get-pip.py 2>nul
call :print_success "pip installed successfully"
goto :eof

REM Install Python dependencies
:install_dependencies
call :print_header "Installing Python Dependencies"

REM Check if pip is available, install if missing
pip --version >nul 2>&1
if errorlevel 1 (
    call :print_warning "pip not found. Attempting to install pip..."
    call :install_pip
    if errorlevel 1 (
        call :print_error "Failed to install pip. Please install pip manually."
        goto :error_exit
    )
)

call :print_step "Installing core dependencies..."
pip install flask==2.3.3 requests==2.31.0
if errorlevel 1 (
    call :print_error "Failed to install core dependencies"
    goto :error_exit
)

call :print_step "Installing recommended dependencies..."
pip install mysql-connector-python==8.1.0 bcrypt==4.0.1 flask-cors==4.0.0 python-dotenv==1.0.0
if errorlevel 1 (
    call :print_warning "Some recommended dependencies failed to install"
)

call :print_step "Installing optional dependencies..."
pip install schedule==1.2.0 yt-dlp==2023.7.6
if errorlevel 1 (
    call :print_warning "Some optional dependencies failed to install"
)

call :print_success "Python dependencies installation completed"
goto :eof

REM Create environment file
:create_environment
call :print_step "Creating environment configuration..."

if not exist ".env" (
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        call :print_success "Environment file created from template"
    ) else (
        (
            echo # MVidarr Enhanced Configuration
            echo.
            echo # MariaDB Configuration
            echo MARIADB_HOST=localhost
            echo MARIADB_PORT=3306
            echo MARIADB_USER=mvidarr
            echo MARIADB_PASSWORD=mvidarr123
            echo MARIADB_DATABASE=mvidarr_db
            echo.
            echo # Application Settings
            echo APP_SECRET_KEY=change-this-secret-key-in-production
            echo APP_DEBUG=false
            echo APP_HOST=0.0.0.0
            echo APP_PORT=5000
            echo.
            echo # MeTube Configuration
            echo METUBE_URL=http://localhost:8081
            echo.
            echo # Logging
            echo LOG_LEVEL=INFO
            echo LOG_FILE=logs/mvidarr.log
        ) > .env
        call :print_success "Environment file created with defaults"
    )
) else (
    call :print_warning "Environment file already exists, skipping"
)
goto :eof

REM Create directory structure
:create_directories
call :print_step "Creating directory structure..."

mkdir logs 2>nul
mkdir downloads 2>nul
mkdir downloads\music_videos 2>nul
mkdir downloads\audio 2>nul
mkdir downloads\thumbnails 2>nul
mkdir data 2>nul
mkdir data\backups 2>nul

call :print_success "Directory structure created"
goto :eof

REM Test installation
:test_installation
call :print_step "Testing installation..."

REM Test Python dependencies
%PYTHON_CMD% -c "import flask, requests; print('✅ Core dependencies OK')" 2>nul
if errorlevel 1 (
    call :print_error "Core dependencies test failed"
    goto :error_exit
)

REM Test optional dependencies
%PYTHON_CMD% -c "import mysql.connector, bcrypt; print('✅ Database dependencies OK')" 2>nul
if errorlevel 1 (
    call :print_warning "Optional dependencies missing - some features may be limited"
)

call :print_success "Installation test completed"
goto :eof

REM Setup MariaDB (Windows)
:setup_mariadb
call :print_header "MariaDB Setup"
call :print_step "MariaDB installation on Windows:"
echo.
echo 1. Download MariaDB from: https://mariadb.org/download/
echo 2. Run the installer as Administrator
echo 3. During installation:
echo    - Set root password
echo    - Enable "Use UTF8 as default server charset"
echo 4. After installation, open MariaDB Command Prompt and run:
echo.
echo    CREATE DATABASE mvidarr_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
echo    CREATE USER 'mvidarr'@'localhost' IDENTIFIED BY 'mvidarr123';
echo    GRANT ALL PRIVILEGES ON mvidarr_db.* TO 'mvidarr'@'localhost';
echo    FLUSH PRIVILEGES;
echo.
set /p mariadb_installed="Have you completed MariaDB installation? (y/N): "
if /i "!mariadb_installed!"=="y" (
    call :print_success "MariaDB setup marked as complete"
) else (
    call :print_warning "MariaDB not installed - application will run in mock mode"
)
goto :eof

REM Create Windows service
:create_windows_service
call :print_header "Windows Auto-Start Setup"
call :print_step "Setting up Windows auto-start options..."
echo.
echo Choose your preferred auto-start method:
echo 1. Task Scheduler (Recommended - runs on user login)
echo 2. Windows Service with NSSM (Advanced - runs on system boot)
echo 3. Manual startup script
echo 4. Skip auto-start setup
echo.
set /p startup_choice="Enter your choice (1-4): "

if "!startup_choice!"=="1" (
    call :create_task_scheduler
) else if "!startup_choice!"=="2" (
    call :create_nssm_service
) else if "!startup_choice!"=="3" (
    call :create_startup_script
) else (
    call :print_warning "Skipping auto-start setup"
)
goto :eof

:create_task_scheduler
call :print_step "Creating Task Scheduler entry..."

REM Create a batch file to start MVidarr
echo @echo off > "%MVIDARR_DIR%\start_mvidarr.bat"
echo cd /d "%MVIDARR_DIR%" >> "%MVIDARR_DIR%\start_mvidarr.bat"
echo %PYTHON_CMD% app.py >> "%MVIDARR_DIR%\start_mvidarr.bat"

REM Create the scheduled task
schtasks /create /tn "MVidarr Enhanced" /tr "\"%MVIDARR_DIR%\start_mvidarr.bat\"" /sc onlogon /ru "%USERNAME%" /f >nul 2>&1

if errorlevel 1 (
    call :print_warning "Failed to create scheduled task automatically"
    call :print_step "Manual Task Scheduler setup:"
    echo 1. Open Task Scheduler (taskschd.msc)
    echo 2. Create Basic Task
    echo 3. Name: MVidarr Enhanced
    echo 4. Trigger: When I log on
    echo 5. Action: Start a program
    echo 6. Program: %MVIDARR_DIR%\start_mvidarr.bat
    echo 7. Finish
) else (
    call :print_success "Task Scheduler entry created successfully"
    call :print_success "MVidarr will start automatically when you log in"
    
    echo.
    set /p start_now="Do you want to start MVidarr now? (y/N): "
    if /i "!start_now!"=="y" (
        start "MVidarr Enhanced" "%MVIDARR_DIR%\start_mvidarr.bat"
        call :print_success "MVidarr started! Access it at: http://localhost:5000"
    )
fi

echo.
echo Task Management Commands:
echo   Start manually: "%MVIDARR_DIR%\start_mvidarr.bat"
echo   Disable auto-start: schtasks /delete /tn "MVidarr Enhanced" /f
echo   View task: schtasks /query /tn "MVidarr Enhanced"
goto :eof

:create_nssm_service
call :print_step "Windows Service setup with NSSM:"
echo.
echo NSSM (Non-Sucking Service Manager) allows running MVidarr as a Windows service.
echo.
echo Steps:
echo 1. Download NSSM from: https://nssm.cc/download
echo 2. Extract nssm.exe to a folder in your PATH
echo 3. Run as Administrator: nssm install MVidarr
echo 4. Set Application path: %PYTHON_CMD%
echo 5. Set Arguments: "%MVIDARR_DIR%\app.py"
echo 6. Set Startup directory: %MVIDARR_DIR%
echo 7. On Dependencies tab, add: Tcpip
echo 8. Click Install service
echo 9. Start service: nssm start MVidarr
echo.
echo Service Management:
echo   Start:   nssm start MVidarr
echo   Stop:    nssm stop MVidarr
echo   Remove:  nssm remove MVidarr
echo.
set /p download_nssm="Do you want to open the NSSM download page? (y/N): "
if /i "!download_nssm!"=="y" (
    start https://nssm.cc/download
)
goto :eof

:create_startup_script
call :print_step "Creating startup script..."

REM Create startup script
echo @echo off > "%MVIDARR_DIR%\start_mvidarr.bat"
echo title MVidarr Enhanced >> "%MVIDARR_DIR%\start_mvidarr.bat"
echo cd /d "%MVIDARR_DIR%" >> "%MVIDARR_DIR%\start_mvidarr.bat"
echo echo Starting MVidarr Enhanced... >> "%MVIDARR_DIR%\start_mvidarr.bat"
echo %PYTHON_CMD% app.py >> "%MVIDARR_DIR%\start_mvidarr.bat"
echo pause >> "%MVIDARR_DIR%\start_mvidarr.bat"

REM Create shortcut in startup folder
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
echo Set WshShell = WScript.CreateObject("WScript.Shell"^) > temp_shortcut.vbs
echo Set Shortcut = WshShell.CreateShortcut("%STARTUP_FOLDER%\MVidarr Enhanced.lnk"^) >> temp_shortcut.vbs
echo Shortcut.TargetPath = "%MVIDARR_DIR%\start_mvidarr.bat" >> temp_shortcut.vbs
echo Shortcut.WorkingDirectory = "%MVIDARR_DIR%" >> temp_shortcut.vbs
echo Shortcut.Description = "MVidarr Enhanced - Music Video Downloader" >> temp_shortcut.vbs
echo Shortcut.Save >> temp_shortcut.vbs

cscript temp_shortcut.vbs >nul 2>&1
del temp_shortcut.vbs >nul 2>&1

if exist "%STARTUP_FOLDER%\MVidarr Enhanced.lnk" (
    call :print_success "Startup script created successfully"
    call :print_success "MVidarr will start automatically when Windows starts"
) else (
    call :print_warning "Failed to create startup shortcut"
    call :print_step "Manual setup: Copy start_mvidarr.bat to your Startup folder"
)

echo.
echo Startup Management:
echo   Manual start: "%MVIDARR_DIR%\start_mvidarr.bat"
echo   Remove auto-start: Delete "%STARTUP_FOLDER%\MVidarr Enhanced.lnk"
goto :eof

REM Show final instructions
:show_final_instructions
call :print_header "🎉 Installation Complete!"
echo.
echo [92mMVidarr Enhanced v2.0 has been installed successfully![0m
echo.
echo [96m📋 Next Steps:[0m
echo.
echo [93m1. 🔧 Configuration:[0m
echo    - Edit .env file to customize settings
echo    - Update MariaDB password if needed
echo    - Configure YouTube API key for search functionality
echo.
echo [93m2. 🚀 Start the application:[0m
echo    %PYTHON_CMD% app.py
echo.
echo [93m3. 🌐 Access the application:[0m
echo    Open: http://localhost:5000
echo    Default login: Admin / Admin
echo    ⚠️  Change the default password immediately!
echo.
echo [93m4. 🔧 Auto-Start Management:[0m
echo    View scheduled task: schtasks /query /tn "MVidarr Enhanced"
echo    Disable auto-start: schtasks /delete /tn "MVidarr Enhanced" /f
echo    Manual start: "%MVIDARR_DIR%\start_mvidarr.bat"
echo.
echo [93m5. 📖 Documentation:[0m
echo    - MARIADB_SETUP.md - Database setup guide
echo    - FIXES_APPLIED.md - Recent changes and fixes
echo    - Configuration options in .env file
echo.
echo [95m🔗 Useful Commands:[0m
echo    Service control: scripts\manage_service.bat [start^|stop^|status^|logs]
echo    Test database: mysql -u mvidarr -pmvidarr123 mvidarr_db
echo    Manual start: "%MVIDARR_DIR%\start_mvidarr.bat"
echo    View logs: type logs\mvidarr.log
echo    Check status: curl http://localhost:5000/api/health
echo.
echo [92m✨ Enjoy using MVidarr Enhanced![0m
echo.
goto :eof

REM Error handling
:error_exit
echo.
call :print_error "Installation failed! Check the output above for details."
echo.
pause
exit /b 1

REM Main installation routine
:main
call :check_python
call :install_dependencies
call :create_environment
call :create_directories

echo.
set /p setup_db="Do you want to set up MariaDB? (y/N): "
if /i "!setup_db!"=="y" (
    call :setup_mariadb
)

call :test_installation

echo.
set /p setup_autostart="Do you want to set up auto-start? (y/N): "
if /i "!setup_autostart!"=="y" (
    call :create_windows_service
)

call :show_final_instructions

echo.
echo Press any key to exit...
pause >nul
exit /b 0

REM Run main installation
call :main
