#!/usr/bin/env python3
"""
MVidarr Service Manager
Handles proper service startup, port management, and process cleanup
"""

import os
import sys
import time
import socket
import signal
import subprocess
from pathlib import Path

class MVidarrServiceManager:
    def __init__(self, port=5000):
        self.port = port
        self.app_path = Path(__file__).parent / "app.py"
        self.venv_path = Path(__file__).parent / "venv"
        self.python_path = self.venv_path / "bin" / "python3"
        
    def check_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return True
            
    def find_process_on_port(self, port):
        """Find process ID using a specific port"""
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTEN' in line:
                    # Extract PID from netstat output
                    parts = line.split()
                    if len(parts) > 6:
                        pid_info = parts[-1]
                        if '/' in pid_info:
                            pid = pid_info.split('/')[0]
                            try:
                                return int(pid)
                            except ValueError:
                                pass
        except Exception as e:
            print(f"Error finding process on port {port}: {e}")
        return None
        
    def kill_process_on_port(self, port):
        """Kill process using a specific port"""
        pid = self.find_process_on_port(port)
        if pid:
            try:
                print(f"Killing process {pid} on port {port}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                # If still running, force kill
                try:
                    os.kill(pid, signal.SIGKILL)
                    print(f"Force killed process {pid}")
                except ProcessLookupError:
                    print(f"Process {pid} terminated successfully")
                return True
            except Exception as e:
                print(f"Error killing process {pid}: {e}")
        return False
        
    def cleanup_previous_instances(self):
        """Clean up any previous MVidarr instances"""
        print("Cleaning up previous instances...")
        
        # Kill any processes on our target port
        if not self.check_port_available(self.port):
            print(f"Port {self.port} is in use, attempting cleanup...")
            self.kill_process_on_port(self.port)
            
        # Kill any python processes running app.py
        try:
            result = subprocess.run(['pkill', '-f', 'python.*app.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Killed MVidarr processes")
                time.sleep(2)
        except Exception as e:
            print(f"Error cleaning up processes: {e}")
            
        # Final check
        if self.check_port_available(self.port):
            print(f"Port {self.port} is now available")
            return True
        else:
            print(f"Warning: Port {self.port} still appears to be in use")
            return False
            
    def start_service(self):
        """Start the MVidarr service"""
        print("Starting MVidarr service...")
        
        # Cleanup any previous instances
        self.cleanup_previous_instances()
        
        # Verify paths exist
        if not self.app_path.exists():
            print(f"Error: app.py not found at {self.app_path}")
            return False
            
        if not self.python_path.exists():
            print(f"Error: Python virtualenv not found at {self.python_path}")
            return False
            
        try:
            # Start the service
            cmd = [str(self.python_path), str(self.app_path)]
            process = subprocess.Popen(
                cmd, 
                cwd=str(self.app_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"Started MVidarr service with PID {process.pid}")
            
            # Wait for service to start and check if port is bound
            max_wait = 30
            wait_time = 0
            
            while wait_time < max_wait:
                if not self.check_port_available(self.port):
                    print(f"✅ Service is listening on port {self.port}")
                    print(f"🌐 MVidarr is available at http://localhost:{self.port}")
                    return True
                    
                # Check if process is still running
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    print("❌ Service failed to start:")
                    print("STDOUT:", stdout)
                    print("STDERR:", stderr)
                    return False
                    
                time.sleep(1)
                wait_time += 1
                print(f"Waiting for service to start... ({wait_time}/{max_wait})")
                
            print(f"❌ Service did not bind to port {self.port} within {max_wait} seconds")
            return False
            
        except Exception as e:
            print(f"❌ Error starting service: {e}")
            return False
            
    def stop_service(self):
        """Stop the MVidarr service"""
        print("Stopping MVidarr service...")
        return self.cleanup_previous_instances()
        
    def restart_service(self):
        """Restart the MVidarr service"""
        print("Restarting MVidarr service...")
        self.stop_service()
        time.sleep(2)
        return self.start_service()
        
    def service_status(self):
        """Check service status"""
        if self.check_port_available(self.port):
            print(f"❌ MVidarr service is NOT running on port {self.port}")
            return False
        else:
            print(f"✅ MVidarr service is running on port {self.port}")
            return True

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MVidarr Service Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], 
                       help='Action to perform')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Port number (default: 5000)')
    
    args = parser.parse_args()
    
    manager = MVidarrServiceManager(args.port)
    
    if args.action == 'start':
        success = manager.start_service()
        sys.exit(0 if success else 1)
    elif args.action == 'stop':
        success = manager.stop_service()
        sys.exit(0 if success else 1)
    elif args.action == 'restart':
        success = manager.restart_service()
        sys.exit(0 if success else 1)
    elif args.action == 'status':
        success = manager.service_status()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()