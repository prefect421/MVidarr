#!/usr/bin/env python3
"""
Improved restart script for MVidarr that works from web interface
"""

import os
import sys
import subprocess
import signal
import time
import psutil
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mvidarr_restart.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_mvidarr_processes():
    """Find all MVidarr-related processes"""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('app.py' in str(cmd) for cmd in cmdline):
                    # Check if it's our MVidarr app by looking at the working directory
                    cwd = proc.info['cwd']
                    if 'mvidarr' in cwd.lower():
                        processes.append(proc)
                        logger.info(f"Found MVidarr process: PID {proc.info['pid']}, CMD: {' '.join(cmdline)}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
    except Exception as e:
        logger.error(f"Error finding processes: {e}")
    
    return processes

def graceful_shutdown():
    """Gracefully shutdown existing MVidarr processes"""
    logger.info("Looking for existing MVidarr processes...")
    
    processes = find_mvidarr_processes()
    if not processes:
        logger.info("No existing MVidarr processes found")
        return True
    
    # Send SIGTERM for graceful shutdown
    for proc in processes:
        try:
            logger.info(f"Sending SIGTERM to process {proc.pid}")
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Wait for graceful shutdown
    logger.info("Waiting for graceful shutdown...")
    time.sleep(5)
    
    # Check if processes are still running and force kill if necessary
    remaining = []
    for proc in processes:
        try:
            if proc.is_running():
                remaining.append(proc)
        except psutil.NoSuchProcess:
            pass
    
    if remaining:
        logger.info("Force killing remaining processes...")
        for proc in remaining:
            try:
                proc.kill()
                logger.info(f"Force killed process {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(2)
    
    return True

def check_port_available(port=5000):
    """Check if the application port is available"""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return True
    except socket.error:
        return False

def start_application():
    """Start the MVidarr application"""
    logger.info("Starting MVidarr...")
    
    # Determine the application directory
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent
    app_file = app_dir / "app.py"
    
    if not app_file.exists():
        logger.error(f"Application file not found: {app_file}")
        return False
    
    # Create logs directory
    logs_dir = app_dir / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "mvidarr.log"
    
    # Determine Python executable
    # First check if system Python has required modules
    try:
        result = subprocess.run([
            "python3", "-c", "import flask, sqlalchemy, requests"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            python_cmd = "python3"
            logger.info("Using system Python (modules available)")
        else:
            # Try virtual environment
            venv_python = app_dir / "venv" / "bin" / "python3"
            if venv_python.exists():
                python_cmd = str(venv_python)
                logger.info("Using virtual environment Python")
            else:
                python_cmd = "python3"
                logger.info("Using system Python (fallback)")
    except Exception:
        python_cmd = "python3"
        logger.info("Using system Python (default)")
    
    try:
        # Change to application directory
        os.chdir(app_dir)
        
        # Start the application
        logger.info(f"Executing: {python_cmd} {app_file}")
        
        with open(log_file, "a") as log_f:
            # Try to start with preexec_fn first, fallback without it
            try:
                process = subprocess.Popen(
                    [python_cmd, str(app_file)],
                    cwd=str(app_dir),
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    preexec_fn=os.setsid
                )
            except Exception as e:
                logger.warning(f"Failed to start with preexec_fn, trying without: {e}")
                process = subprocess.Popen(
                    [python_cmd, str(app_file)],
                    cwd=str(app_dir),
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
        
        # Save PID
        pid_file = app_dir / "data" / "mvidarr.pid"
        with open(pid_file, "w") as f:
            f.write(str(process.pid))
        
        logger.info(f"Started MVidarr with PID: {process.pid}")
        
        # Wait a moment and check if it's still running
        time.sleep(3)
        
        if process.poll() is None:
            logger.info("MVidarr started successfully")
            
            # Check if port is now in use (indicating successful start)
            for i in range(10):
                if not check_port_available(5000):
                    logger.info("Port 5000 is now in use - application started successfully")
                    return True
                time.sleep(1)
            
            logger.warning("Application started but port 5000 is still available")
            return True
        else:
            logger.error("Application failed to start")
            # Read last few lines of log for debugging
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        logger.error("Last log entries:")
                        for line in lines[-10:]:
                            logger.error(line.strip())
            except Exception:
                pass
            return False
            
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return False

def main():
    """Main restart function"""
    logger.info("=== MVidarr Restart Script ===")
    
    try:
        # Step 1: Graceful shutdown
        if not graceful_shutdown():
            logger.error("Failed to shutdown existing processes")
            return False
        
        # Step 2: Wait for port to be available
        logger.info("Waiting for port 5000 to be available...")
        for i in range(15):  # Wait up to 15 seconds
            if check_port_available(5000):
                logger.info("Port 5000 is available")
                break
            logger.info(f"Port still in use, waiting... ({i+1}/15)")
            time.sleep(1)
        else:
            logger.warning("Port 5000 may still be in use, proceeding anyway")
        
        # Step 3: Start application
        if start_application():
            logger.info("=== Restart completed successfully ===")
            return True
        else:
            logger.error("=== Restart failed ===")
            return False
            
    except Exception as e:
        logger.error(f"Restart script failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)