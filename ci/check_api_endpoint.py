"""Test that the root API endpoint is available."""

import json

import requests

# We expect the server to be running on the local host
url = "http://localhost:8000/api/"

print("Testing InvenTree API endpoint")

response = requests.get(url)

assert(response.status_code == 200)

print("- Response 200 OK")

data = json.loads(response.text)

required_keys = [
    'server',
    'version',
    'apiVersion',
    'worker_running',
]

for key in required_keys:
    assert(key in data)
    print(f"- Found key '{key}'")

# Check that the worker is running
assert(data['worker_running'])

print("- Background worker is operational")

print("API Endpoint Tests Passed OK")
