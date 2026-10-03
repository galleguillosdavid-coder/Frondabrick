import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.token_counter import count_tokens, count_chars

def test_token_counter():
    text = "Frondabrick Pair Programming Autonomous Session 2026"
    assert count_tokens(text) == 6
    assert count_chars("abc") == 3
    print("[PASS] Token counter verified successfully.")

if __name__ == "__main__":
    test_token_counter()
