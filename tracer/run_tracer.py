"""
Demo: run CodeTracer against sample_code.py / calculate_total.

Run from repo root:
    python -m tracer.run_tracer
or:
    python tracer/run_tracer.py
"""

import json
import sys
from pathlib import Path

# Allow running from repo root or from inside tracer/
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracer.code_tracer import CodeTracer

SAMPLE_FILE = Path(__file__).parent.parent / "parser" / "sample_code.py"

SAMPLE_INPUT = {
    "items": [
        {"price": 100},
        {"price": 150},
        {"price": 50},
    ],
    "discount": 0.1,
}

if __name__ == "__main__":
    result = CodeTracer().trace(SAMPLE_FILE, "calculate_total", SAMPLE_INPUT)
    print(json.dumps(result, indent=2))
