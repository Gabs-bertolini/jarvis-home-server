import requests
import json
import subprocess

GLANCES_URL = "http://192.168.0.211:61208/api/4/all"

def server_status():
    response = requests.get(GLANCES_URL)

    data = response.json()

    summary = {
        "cpu_percent": data["cpu"]["total"],
        "memory_percent": data["mem"]["percent"],
        "uptime": data["uptime"],
        "disk": data["fs"]
    }

    return json.dumps(summary, indent=2)

def docker_status():
    dockerps = subprocess.run(
        ["docker", "ps"],
        capture_output=True,
        text=True
    ).stdout

    return f"""=== DOCKER PS ===
{dockerps}
"""

