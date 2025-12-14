import requests
import sys
import time

def check_health(url="http://localhost:8000/health", retries=5, delay=2):
    print(f"Checking health at {url}...")
    for i in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 200 and response.json().get("status") == "ok":
                print("✅ Service is HEALTHY")
                return True
            else:
                print(f"⚠️ Service returned status {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"⏳ Waiting for service... ({i+1}/{retries})")
        
        time.sleep(delay)
    
    print("❌ Service health check FAILED")
    return False

if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)
