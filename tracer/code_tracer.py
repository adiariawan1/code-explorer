"""
Code Flow Explorer — runtime tracer (re-exported from python/tracer.py).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from python.tracer import CodeTracer, main

if __name__ == "__main__":
    main()
