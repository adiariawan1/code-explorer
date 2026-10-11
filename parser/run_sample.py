"""Run the CodeParser against sample_code.py and print the JSON result."""
import json
import sys
from pathlib import Path

# allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.code_parser import CodeParser

result = CodeParser().parse(Path(__file__).parent / "sample_code.py")
print(json.dumps(result, indent=2))
