from __future__ import annotations

import sys
import time
from datetime import datetime, UTC


def ts() -> str:
    return datetime.now(tz=UTC).isoformat()


print(f"[{ts()}] interactive_echo.py started", flush=True)
print("Type text and press Enter. Type 'exit' to stop.", flush=True)

while True:
    line = sys.stdin.readline()
    if not line:
        print(f"[{ts()}] stdin closed", flush=True)
        break
    value = line.strip()
    if value.lower() == "exit":
        print(f"[{ts()}] exit requested", flush=True)
        break
    print(f"[{ts()}] echo: {value}", flush=True)
    time.sleep(0.1)

print(f"[{ts()}] interactive_echo.py stopped", flush=True)
