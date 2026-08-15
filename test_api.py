import requests
import json

base_url = "http://127.0.0.1:5000"

print("Testing API endpoints...")

# Test /api/iptv/stats
try:
    response = requests.get(f"{base_url}/api/iptv/stats")
    print(f"GET /api/iptv/stats: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"GET /api/iptv/stats: ERROR - {e}")

# Test /api/iptv/sources
try:
    response = requests.get(f"{base_url}/api/iptv/sources")
    print(f"GET /api/iptv/sources: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"GET /api/iptv/sources: ERROR - {e}")

# Test /api/process/status
try:
    response = requests.get(f"{base_url}/api/process/status")
    print(f"GET /api/process/status: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"GET /api/process/status: ERROR - {e}")

print("\nAPI endpoints test completed.")
