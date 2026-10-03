import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.probe import probe_status

def test_probe():
    status = probe_status()
    assert status == "HEALTHY", f"Probe expected HEALTHY but got {status}"
    print("[PASS] Probe status is HEALTHY.")

if __name__ == "__main__":
    test_probe()
