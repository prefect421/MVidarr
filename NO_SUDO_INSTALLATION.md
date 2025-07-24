# MVidarr - No Sudo Required Installation 🚀

## Quick Solution for \"sudo required\" or \"externally-managed-environment\" Errors

If you encountered the `externally-managed-environment` error or don't have sudo access, here's the **easiest solution**:

### 1. Run the Enhanced Installer
```bash
cd /path/to/mvidarr
chmod +x scripts/install.sh
./scripts/install.sh
```

### 2. When Prompted, Choose Option 3: User Installation
```
Choose installation method:
  1. Install python3-venv with sudo (requires admin access)
  2. Try alternative virtual environment method (python -m venv)
  3. Use --user installation (install to user directory)     ← Choose this!
  4. Switch to --break-system-packages method
Enter choice (1-4) [3]: 3
```

### 3. Start the Application
```bash
# Use the auto-generated startup script
./start_mvidarr.sh

# Or manually (if PATH issues)
export PATH="$HOME/.local/bin:$PATH"
python3 app.py
```

## What User Installation Does

✅ **No Sudo Required** - Installs to `~/.local/` directory  
✅ **No System Conflicts** - Doesn't interfere with system packages  
✅ **Automatic PATH Setup** - Configures your shell automatically  
✅ **Service Integration** - Works with systemd/LaunchAgent  
✅ **Clean and Safe** - Isolated from system Python  

## Files Created

- `start_mvidarr.sh` - Startup script with proper PATH
- `~/.local/bin/` - Python packages installed here
- Updated shell profile (`.bashrc`/`.zshrc`) with PATH configuration

## Troubleshooting

### If you get "command not found" errors:
```bash
# Add to your current session
export PATH="$HOME/.local/bin:$PATH"

# Or restart your terminal to load the updated profile
```

### If the installer still asks for sudo:
Choose option 3 (User Installation) when prompted, or run:
```bash
# Manual user installation
pip3 install --user flask requests mysql-connector-python bcrypt flask-cors python-dotenv schedule yt-dlp
```

## Why This Works

Modern Linux distributions (Ubuntu 22.04+, Debian 12+) use "externally-managed environments" to prevent pip conflicts. The user installation method:

1. **Bypasses the restriction** by installing to user space
2. **Maintains isolation** like virtual environments  
3. **Requires no admin privileges**
4. **Works on all systems** including shared hosting/containers

## Alternative: Manual User Installation

If the installer fails completely:

```bash
# Install dependencies to user directory
pip3 install --user flask==2.3.3 requests==2.31.0
pip3 install --user mysql-connector-python==8.1.0 bcrypt==4.0.1 
pip3 install --user flask-cors==4.0.0 python-dotenv==1.0.0
pip3 install --user schedule==1.2.0 yt-dlp==2023.7.6

# Ensure PATH includes ~/.local/bin
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Create environment file
cp .env.template .env

# Create directories
mkdir -p logs downloads/{music_videos,audio,thumbnails} data/backups

# Start the application
python3 app.py
```

**That's it! No sudo required, no system conflicts, and MVidarr runs perfectly.** 🎉
