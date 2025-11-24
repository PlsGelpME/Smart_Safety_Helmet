import socket
import threading
import time

class SimpleBroker:
    def __init__(self, host='0.0.0.0', port=1883):
        self.host = host
        self.port = port
        self.clients = []
        
    def handle_client(self, client_socket, address):
        print(f"ESP32 Connected: {address}")
        self.clients.append((client_socket, address))
        
        try:
            # Send welcome message
            client_socket.send(b"Connected to Python MQTT broker\n")
            
            while True:
                data = client_socket.recv(1024)
                if data:
                    message = data.decode().strip()
                    print(f"From {address}: {message}")
                    
                    # Echo back to client
                    response = f"Echo: {message}\n"
                    client_socket.send(response.encode())
                else:
                    break
                    
        except Exception as e:
            print(f"Client {address} error: {e}")
        finally:
            self.clients.remove((client_socket, address))
            client_socket.close()
            print(f"ESP32 Disconnected: {address}")
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        print(f"Python MQTT Broker running on {self.host}:{self.port}")
        print("Waiting for ESP32 connections...")
        
        try:
            while True:
                client_socket, address = server.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("Broker stopped")
        finally:
            server.close()

if __name__ == "__main__":
    broker = SimpleBroker('0.0.0.0', 1883)
    broker.start()