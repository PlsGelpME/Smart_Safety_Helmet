import network
import time
import machine

class WiFiManager:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)
        
    def connect(self, max_retries=3, timeout=20):
        """Connect to WiFi with retry logic"""
        self.wlan.active(True)
        
        for attempt in range(max_retries):
            print(f"WiFi connection attempt {attempt + 1}/{max_retries}")
            
            if self.wlan.isconnected():
                print("Already connected to WiFi")
                return True
                
            # Disconnect first
            self.wlan.disconnect()
            time.sleep(2)
            
            # Connect
            self.wlan.connect(self.ssid, self.password)
            
            # Wait for connection
            start_time = time.time()
            while not self.wlan.isconnected():
                if time.time() - start_time > timeout:
                    break
                print(".", end='')
                time.sleep(1)
                
            if self.wlan.isconnected():
                print(f"\n✅ WiFi connected on attempt {attempt + 1}")
                print(f"IP: {self.wlan.ifconfig()[0]}")
                return True
            else:
                print(f"\n❌ Attempt {attempt + 1} failed")
                status = self.wlan.status()
                self.print_status_message(status)
                
                if attempt < max_retries - 1:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                    
        return False
    
    def print_status_message(self, status):
        """Print human-readable status messages"""
        status_messages = {
            network.STAT_IDLE: "Idle",
            network.STAT_CONNECTING: "Connecting",
            network.STAT_WRONG_PASSWORD: "Wrong password",
            network.STAT_NO_AP_FOUND: "Network not found", 
            network.STAT_CONNECT_FAIL: "Connection failed",
            network.STAT_GOT_IP: "Got IP address"
        }
        print(status_messages.get(status))
    
    def disconnect(self):
        """Disconnect from WiFi"""
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("WiFi disconnected")
    
    def getIP(self):
        """Get current IP address"""
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None

# Usage
if __name__ == "__main__":
    wifi = WiFiManager("OnePlus 9R", "kesav115")

    if wifi.connect():
        print("WiFi setup successful!")
        print(f"IP Address: {wifi.getIP()}")
    else:
        print("WiFi connection failed after all retries")
