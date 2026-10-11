"""
Code Flow Explorer — static AST parser (re-exported from python/parser.py).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from python.parser import CodeParser, main

if __name__ == "__main__":
    main()
