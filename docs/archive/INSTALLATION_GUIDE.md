# MVidarr Installation Guide

## Overview

MVidarr v2.0 now includes automatic handling of pip installation and modern Python environment management, including support for externally-managed Python environments found on newer Linux distributions.

## What's New

### Automatic Pip Installation
- Scripts now automatically install pip if it's missing
- Multiple fallback methods ensure high success rate
- Cross-platform support (Windows, Linux, macOS)

### Externally-Managed Environment Support
- Detects externally-managed Python environments (Ubuntu 22.04+, Debian 12+, etc.)
- Offers multiple installation methods when detected
- Virtual environment support for isolated installations

## Installation Methods

### Quick Start
```bash
# Linux/macOS
cd /path/to/mvidarr
chmod +x scripts/install.sh
./scripts/install.sh

# Windows
cd C:\path\to\mvidarr\scripts
install.bat
```

### Installation Options for Externally-Managed Environments

When the installer detects an externally-managed environment, you'll be presented with these options:

#### 1. Virtual Environment (Recommended)
- Creates an isolated Python environment
- No conflicts with system packages
- Safe and clean installation
- Automatically creates startup scripts
- **Note**: May require sudo to install `python3-venv` if not available

#### 2. User Installation (No Sudo Required) ✨
- Installs packages to `~/.local/` directory
- No system conflicts, no sudo required
- Automatically configures PATH
- Creates `start_mvidarr.sh` startup script
- Perfect for shared systems or when you don't have admin access

#### 3. System-wide with --break-system-packages
- Installs packages system-wide
- May conflict with system packages
- Not recommended for production systems

#### 4. System Package Manager
- Uses apt/dnf/yum to install packages
- Limited package availability
- Some features may be missing

## Files Modified

### Main Installation Scripts
- `scripts/install.sh` - Enhanced Linux/macOS installer
- `scripts/install.bat` - Enhanced Windows installer

### New Features Added
- Automatic pip installation
- Virtual environment support
- Externally-managed environment detection
- Multiple installation methods
- Improved error handling

## Virtual Environment Usage

### If You Chose Virtual Environment Installation

The installer creates several convenience files:

#### Startup Script
```bash
# Use the generated startup script
./start_with_venv.sh
```

#### Manual Activation
```bash
# Activate virtual environment
source mvidarr_venv/bin/activate

# Run the application
python app.py

# Deactivate when done
deactivate
```

#### Service Configuration
- systemd services automatically use the virtual environment
- macOS LaunchAgents are configured for virtual environment
- No manual configuration needed

## User Installation Usage

### If You Chose User Installation (--user)

The installer creates convenience files and configures your environment:

#### Startup Script
```bash
# Use the generated startup script (handles PATH automatically)
./start_mvidarr.sh
```

#### Manual Startup
```bash
# Ensure ~/.local/bin is in your PATH
export PATH="$HOME/.local/bin:$PATH"

# Run the application
python3 app.py
```

#### PATH Configuration
- The installer automatically adds `~/.local/bin` to your shell profile
- Restart your terminal or run `source ~/.bashrc` (or `~/.zshrc`) to apply
- The startup script handles PATH configuration automatically

#### Service Configuration
- systemd services are configured with the correct PATH
- No manual configuration needed

## Troubleshooting

### Common Issues

#### 1. "externally-managed-environment" Error
**Solution**: Run the installer again and choose option 1 (Virtual Environment)

#### 2. "python3-venv not found" or "sudo required"
**Solutions** (in order of preference):
1. Choose **User Installation** (option 3) - no sudo required
2. Try alternative virtual environment methods (option 2)
3. Install python3-venv manually:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-venv
   
   # CentOS/RHEL/Fedora
   sudo dnf install python3-venv  # or yum
   ```
4. Use the installer's automatic detection and choose the best available method

#### 3. pip Installation Failed
**Solutions** (in order of preference):
1. Use the installer's automatic pip installation
2. Manual installation:
   ```bash
   # Method 1: get-pip.py
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   python3 get-pip.py
   
   # Method 2: ensurepip
   python3 -m ensurepip --upgrade
   
   # Method 3: Package manager
   sudo apt install python3-pip  # Ubuntu/Debian
   sudo dnf install python3-pip  # Fedora
   ```

### Testing Your Environment

Use the provided test script to check your environment:
```bash
chmod +x scripts/test_externally_managed.sh
./scripts/test_externally_managed.sh
```

## System Service Management

### Linux (systemd)
```bash
# Start service
sudo systemctl start mvidarr

# Stop service  
sudo systemctl stop mvidarr

# Check status
sudo systemctl status mvidarr

# View logs
sudo journalctl -u mvidarr -f
```

### macOS (LaunchAgent)
```bash
# Start service
launchctl start com.mvidarr.enhanced

# Stop service
launchctl stop com.mvidarr.enhanced

# Remove auto-start
launchctl unload ~/Library/LaunchAgents/com.mvidarr.enhanced.plist
```

## Manual Installation (Fallback)

If the automatic installer fails, you can install manually:

### 1. Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv mvidarr_venv
source mvidarr_venv/bin/activate

# Install dependencies
pip install flask==2.3.3 requests==2.31.0
pip install mysql-connector-python==8.1.0 bcrypt==4.0.1 flask-cors==4.0.0 python-dotenv==1.0.0
pip install schedule==1.2.0 yt-dlp==2023.7.6
```

### 2. Create Environment File
```bash
cp .env.template .env
# Edit .env file as needed
```

### 3. Create Directories
```bash
mkdir -p logs downloads/{music_videos,audio,thumbnails} data/backups
```

### 4. Start Application
```bash
source mvidarr_venv/bin/activate
python app.py
```

## Environment Variables

Key configuration options in `.env`:

```bash
# Database Configuration
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=mvidarr
MARIADB_PASSWORD=mvidarr123
MARIADB_DATABASE=mvidarr_db

# Application Settings
APP_SECRET_KEY=your-secret-key-here
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mvidarr.log
```

## Support

If you encounter issues:

1. Check the installation logs for specific error messages
2. Run the test script to diagnose environment issues
3. Try the virtual environment installation method
4. Check system requirements and dependencies
5. Review the troubleshooting section above

For additional help, check the project documentation or create an issue with:
- Your operating system and version
- Python version (`python3 --version`)
- Complete error messages
- Output from the test script
