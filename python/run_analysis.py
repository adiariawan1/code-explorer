"""
run_analysis.py — Bridge script combining CodeParser and CodeTracer.
Outputs the complete Analysis JSON to stdout.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from python.parser import CodeParser
from python.tracer import CodeTracer, _find_loops


def find_trace_args_comment(source_lines: list[str], line_start: int) -> dict | None:
    """Check lines immediately preceding function definition for # trace-args: <json>."""
    idx = line_start - 2  # 0-indexed line before def (line_start is 1-indexed)
    while idx >= 0:
        line = source_lines[idx].strip()
        if not line:
            idx -= 1
            continue
        if line.startswith("#"):
            match = re.search(r"#\s*trace-args\s*:\s*(\{.*\})", line)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    return None
            idx -= 1
        else:
            break
    return None


def run(file_path: str, function_name: str | None = None, args_json: str | None = None) -> dict:
    target_path = Path(file_path).resolve()
    if not target_path.exists():
        sys.stderr.write(f"Error: file not found: {target_path}\n")
        sys.exit(2)

    source = target_path.read_text(encoding="utf-8")
    source_lines = source.splitlines()

    parser = CodeParser()
    try:
        parse_result = parser.parse(target_path)
    except SyntaxError as e:
        sys.stderr.write(f"Syntax error at line {e.lineno}: {e.msg}\n")
        print(json.dumps({"error": f"Syntax error at line {e.lineno}: {e.msg}"}))
        sys.exit(2)
    except Exception as e:
        sys.stderr.write(f"Parser error: {e}\n")
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    functions = parse_result.get("functions", [])

    # Function selection:
    # 1. explicit --function
    # 2. first function with loop
    # 3. fallback: first function
    chosen_func = None
    if function_name:
        chosen_func = next((f for f in functions if f["name"] == function_name or f["name"].endswith(f".{function_name}")), None)
        if not chosen_func:
            chosen_func = {"name": function_name, "params": [], "line_start": 1}
    else:
        for f in functions:
            loops = _find_loops(source, f["name"])
            if loops:
                chosen_func = f
                break
        if not chosen_func and functions:
            chosen_func = functions[0]

    trace_result = None
    if chosen_func:
        func_name = chosen_func["name"]
        # Args determination:
        args = None
        if args_json:
            try:
                args = json.loads(args_json)
            except Exception as e:
                sys.stderr.write(f"Warning: could not parse --args JSON ({e}), skipping trace\n")
        if args is None and "line_start" in chosen_func:
            args = find_trace_args_comment(source_lines, chosen_func["line_start"])
        if args is None and len(chosen_func.get("params", [])) == 0:
            args = {}

        if args is not None:
            try:
                tracer = CodeTracer()
                trace_result = tracer.trace(target_path, func_name, args)
            except Exception as e:
                sys.stderr.write(f"Tracer warning: {e}\n")
                trace_result = {
                    "function_traced": func_name,
                    "input_used": args,
                    "steps": [],
                    "final_state": {},
                    "error": str(e),
                    "truncated": False,
                }
        else:
            sys.stderr.write(f"Note: no trace input arguments found for '{func_name}', trace skipped.\n")

    combined = {
        "file": target_path.name,
        "functions": parse_result["functions"],
        "variables": parse_result["variables"],
        "edges": parse_result["edges"],
        "trace": trace_result,
    }
    return combined


def main():
    parser = argparse.ArgumentParser(description="Run static AST parser and dynamic tracer on Python source.")
    parser.add_argument("file", help="Path to Python source file")
    parser.add_argument("--function", "-f", help="Name of function to trace")
    parser.add_argument("--args", "-a", help="JSON string of arguments for traced function")

    args = parser.parse_args()
    combined = run(args.file, args.function, args.args)
    print(json.dumps(combined, indent=2))


if __name__ == "__main__":
    main()
