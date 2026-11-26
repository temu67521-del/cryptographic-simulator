"""Keep-alive pinger for the Render cron job."""
import urllib.request
import json

url = "https://cryptographic-simulator.onrender.com/api/health"
req = urllib.request.Request(url, headers={"User-Agent": "RenderKeepAlive/1.0"})
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
        print(f"OK {resp.status} {data}")
except Exception as exc:
    print(f"ERROR: {exc}")
    raise
