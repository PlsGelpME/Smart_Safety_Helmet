# test_client.py - Simple test client
import socket
import time
import json

def test_client():
    """Test the socket broker with sample data"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect(('localhost', 1883))
        print("Connected to broker")
        
        # Receive welcome message
        welcome = client_socket.recv(1024).decode()
        print(f"Broker: {welcome.strip()}")
        
        # Send test messages
        test_messages = [
            # Gas sensor data
            json.dumps({
                "sensor": "gas",
                "value": 125,
                "status": "normal",
                "unit": "adc",
                "timestamp": time.time()
            }),
            
            # Temperature data
            json.dumps({
                "sensor": "temperature",
                "value": 23.5,
                "unit": "celsius",
                "timestamp": time.time()
            }),
            
            # GPS data
            json.dumps({
                "sensor": "gps",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "altitude": 10.5,
                "timestamp": time.time()
            }),
            
            # Status update
            json.dumps({
                "type": "status",
                "status": "online",
                "message": "Test device running",
                "timestamp": time.time()
            })
        ]
        
        for message in test_messages:
            print(f"Sending: {message}")
            client_socket.send((message + '\n').encode())
            
            # Wait for response
            response = client_socket.recv(1024).decode()
            print(f"Response: {response.strip()}")
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        print("Disconnected")

if __name__ == "__main__":
    test_client()