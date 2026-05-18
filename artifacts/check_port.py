import socket
import sys

def check_port(host, port):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"Successfully connected to {host}:{port}")
            return True
    except (socket.timeout, ConnectionRefusedError):
        print(f"Could not connect to {host}:{port}")
        return False
    except Exception as e:
        print(f"Error connecting to {host}:{port}: {e}")
        return False

if __name__ == "__main__":
    check_port("127.0.0.1", 8000)
