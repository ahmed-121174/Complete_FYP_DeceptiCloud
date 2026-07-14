#!/usr/bin/env python3
"""
SSH Honeypot - Lightweight SSH trap
Logs all SSH connection attempts and commands
"""

import socket
import threading
import sys
import json
from pathlib import Path
from datetime import datetime
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_service import get_db_service

# Configuration
SSH_PORT = 2222  # Non-standard port to avoid conflicts
SSH_BANNER = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
MAX_CONNECTIONS = 100

db = get_db_service()


class SSHHoneypot:
    """Lightweight SSH honeypot"""
    
    def __init__(self, port: int = SSH_PORT):
        self.port = port
        self.running = False
        self.connections = []
    
    def start(self):
        """Start the SSH honeypot"""
        self.running = True
        
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(MAX_CONNECTIONS)
            
            print(f"SSH Honeypot listening on port {self.port}")
            
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    thread = threading.Thread(
                        target=self.handle_connection,
                        args=(client_socket, address),
                        daemon=True
                    )
                    thread.start()
                    self.connections.append(thread)
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}")
        
        except Exception as e:
            print(f"Error starting SSH honeypot: {e}")
        finally:
            server_socket.close()
    
    def handle_connection(self, client_socket: socket.socket, address: tuple):
        """Handle an SSH connection attempt"""
        ip, port = address
        session_id = hashlib.sha256(f"{ip}:{port}:{datetime.now()}".encode()).hexdigest()[:16]
        
        print(f"SSH connection from {ip}:{port}")
        
        try:
            # Send SSH banner
            client_socket.send(f"{SSH_BANNER}\r\n".encode())
            
            # Log connection attempt
            self.log_connection(ip, session_id)
            
            # Receive client banner
            data = client_socket.recv(1024)
            if data:
                client_banner = data.decode('utf-8', errors='ignore').strip()
                self.log_client_banner(ip, client_banner, session_id)
            
            # Simulate authentication
            attempts = 0
            max_attempts = 3
            
            while attempts < max_attempts:
                # Wait for authentication data
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Try to extract username/password (simplified)
                # In a real implementation, you'd parse SSH protocol properly
                auth_data = data.decode('utf-8', errors='ignore')
                
                # Log authentication attempt
                self.log_auth_attempt(ip, auth_data, session_id)
                
                attempts += 1
                
                # Always reject authentication
                client_socket.send(b"Authentication failed\r\n")
            
            # Close connection
            client_socket.send(b"Too many authentication failures\r\n")
        
        except Exception as e:
            print(f"Error handling SSH connection from {ip}: {e}")
        finally:
            client_socket.close()
            self.log_disconnect(ip, session_id)
    
    def log_connection(self, ip: str, session_id: str):
        """Log SSH connection attempt"""
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO honeypot_events (
                        timestamp, honeypot_name, honeypot_port, event_type,
                        ip, session_id, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    'ssh',
                    self.port,
                    'ssh_connection',
                    ip,
                    session_id,
                    json.dumps({'action': 'connect'})
                ))
                conn.commit()
        except Exception as e:
            print(f"Error logging SSH connection: {e}")
    
    def log_client_banner(self, ip: str, banner: str, session_id: str):
        """Log SSH client banner"""
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO honeypot_events (
                        timestamp, honeypot_name, honeypot_port, event_type,
                        ip, session_id, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    'ssh',
                    self.port,
                    'ssh_banner',
                    ip,
                    session_id,
                    json.dumps({'banner': banner})
                ))
                conn.commit()
        except Exception as e:
            print(f"Error logging SSH banner: {e}")
    
    def log_auth_attempt(self, ip: str, auth_data: str, session_id: str):
        """Log SSH authentication attempt"""
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO honeypot_events (
                        timestamp, honeypot_name, honeypot_port, event_type,
                        ip, session_id, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    'ssh',
                    self.port,
                    'ssh_auth_attempt',
                    ip,
                    session_id,
                    json.dumps({'auth_data_hash': hashlib.sha256(auth_data.encode()).hexdigest()[:16]})
                ))
                conn.commit()
        except Exception as e:
            print(f"Error logging SSH auth attempt: {e}")
    
    def log_disconnect(self, ip: str, session_id: str):
        """Log SSH disconnection"""
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO honeypot_events (
                        timestamp, honeypot_name, honeypot_port, event_type,
                        ip, session_id, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    'ssh',
                    self.port,
                    'ssh_disconnect',
                    ip,
                    session_id,
                    json.dumps({'action': 'disconnect'})
                ))
                conn.commit()
        except Exception as e:
            print(f"Error logging SSH disconnect: {e}")
    
    def stop(self):
        """Stop the SSH honeypot"""
        self.running = False
        print("SSH Honeypot stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSH Honeypot')
    parser.add_argument('--port', type=int, default=SSH_PORT,
                       help=f'Port to listen on (default: {SSH_PORT})')
    args = parser.parse_args()
    
    honeypot = SSHHoneypot(port=args.port)
    
    try:
        honeypot.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        honeypot.stop()


if __name__ == '__main__':
    main()
