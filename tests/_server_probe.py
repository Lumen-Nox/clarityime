"""One-off server startup probe for debugging e2e."""
import os
import sys
import threading
import time
import urllib.request

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo)
data = os.environ.get("CLARITYIME_DATA_DIR") or os.path.join(os.environ.get("TEMP", "."), "clarityime_probe")
os.environ["CLARITYIME_DATA_DIR"] = data
os.makedirs(data, exist_ok=True)

port = int(sys.argv[1]) if len(sys.argv) > 1 else 17899

from clarityime.server import run_server  # noqa: E402

print("starting server...", flush=True)
t = threading.Thread(target=run_server, args=("127.0.0.1", port), daemon=True)
t.start()

for i in range(50):
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=1)
        print("health:", r.read().decode(), flush=True)
        sys.exit(0)
    except Exception as e:
        if i == 0 or i % 10 == 9:
            print(f"wait {i}: {e}", flush=True)
        time.sleep(0.2)

print("FAILED: server never responded", flush=True)
sys.exit(1)
