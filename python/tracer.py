"""
Code Flow Explorer — Deterministic Runtime Tracer (sys.settrace).
Executes Python code and records variable state per line and loop iteration.
"""

import ast
import copy
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path


_MAX_STEPS = 500
_TIMEOUT_SECONDS = 5.0


def _safe_serialize(val, depth=0):
    """Serialize values safely: primitives as-is, collections up to 20 items / depth 2."""
    if depth > 2:
        return repr(val)[:80]

    if isinstance(val, (int, float, bool, str, type(None))):
        return val
    elif isinstance(val, (list, tuple)):
        items = list(val)[:20]
        res = [_safe_serialize(x, depth + 1) for x in items]
        if len(val) > 20:
            res.append(f"... (+{len(val) - 20} more)")
        return res
    elif isinstance(val, dict):
        res = {}
        for i, (k, v) in enumerate(val.items()):
            if i >= 20:
                res["..."] = f"(+{len(val) - 20} more keys)"
                break
            res[str(k)[:40]] = _safe_serialize(v, depth + 1)
        return res
    else:
        return repr(val)[:80]


def _safe_snapshot(locals_dict: dict) -> dict:
    """Capture snapshot of local variables."""
    snapshot = {}
    for k, v in locals_dict.items():
        if k.startswith("__") or k.startswith("_cfe_") or k.startswith("_tracer_"):
            continue
        try:
            snapshot[k] = _safe_serialize(v)
        except Exception:
            snapshot[k] = "<unserializable>"
    return snapshot


class LoopInfo:
    def __init__(self, header_line: int, start_line: int, end_line: int, depth: int):
        self.header_line = header_line
        self.start_line = start_line
        self.end_line = end_line
        self.depth = depth
        self.counter = 0


def _find_loops(source: str, function_name: str) -> list[LoopInfo]:
    """Inspect AST to find all loops inside function_name and their line bounds."""
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    target_func = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name or f"{getattr(node, 'parent_class', '')}.{node.name}" == function_name:
                target_func = node
                break

    if target_func is None:
        return []

    loops: list[LoopInfo] = []

    def walk_body(stmts, depth):
        for stmt in stmts:
            if isinstance(stmt, (ast.For, ast.While, ast.AsyncFor)):
                loops.append(LoopInfo(
                    header_line=stmt.lineno,
                    start_line=stmt.lineno,
                    end_line=stmt.end_lineno or stmt.lineno,
                    depth=depth
                ))
                walk_body(stmt.body, depth + 1)
                walk_body(stmt.orelse, depth + 1)
            elif hasattr(stmt, "body") and isinstance(stmt.body, list):
                walk_body(stmt.body, depth)
                if hasattr(stmt, "orelse") and isinstance(stmt.orelse, list):
                    walk_body(stmt.orelse, depth)

    walk_body(target_func.body, 1)
    return loops


class CodeTracer:
    """Traces execution of a specific function in a target Python file."""

    def trace(self, file_path: str | Path, function_name: str, args: dict | None = None) -> dict:
        if args is None:
            args = {}

        target_path = Path(file_path).resolve()
        if not target_path.exists():
            return {
                "function_traced": function_name,
                "input_used": args,
                "steps": [],
                "final_state": {},
                "error": f"File not found: {target_path}",
                "truncated": False,
            }

        try:
            source = target_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "function_traced": function_name,
                "input_used": args,
                "steps": [],
                "final_state": {},
                "error": f"Failed to read file: {e}",
                "truncated": False,
            }

        loops = _find_loops(source, function_name)

        # Load the module under an isolated name so __main__ blocks do not run
        mod_name = f"_cfe_traced_{target_path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, str(target_path))
        if spec is None or spec.loader is None:
            return {
                "function_traced": function_name,
                "input_used": args,
                "steps": [],
                "final_state": {},
                "error": f"Cannot load module spec for {target_path}",
                "truncated": False,
            }

        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            return {
                "function_traced": function_name,
                "input_used": args,
                "steps": [],
                "final_state": {},
                "error": f"Error loading module: {type(e).__name__}: {e}",
                "truncated": False,
            }

        # Resolve function (support Class.method or top-level function)
        if "." in function_name:
            cls_name, m_name = function_name.split(".", 1)
            cls_obj = getattr(module, cls_name, None)
            func = getattr(cls_obj, m_name, None) if cls_obj else None
        else:
            func = getattr(module, function_name, None)

        if func is None or not callable(func):
            return {
                "function_traced": function_name,
                "input_used": args,
                "steps": [],
                "final_state": {},
                "error": f"Function '{function_name}' not found or not callable",
                "truncated": False,
            }

        target_code = getattr(func, "__code__", None)

        steps: list[dict] = []
        truncated = False
        error_msg: str | None = None
        final_state: dict = {}
        start_time = time.monotonic()
        stop_tracing = False

        def local_tracer(frame, event, arg):
            nonlocal truncated, error_msg, final_state, stop_tracing
            if stop_tracing:
                return None

            # Check timeout
            if time.monotonic() - start_time > _TIMEOUT_SECONDS:
                truncated = True
                error_msg = f"TimeoutError: Execution exceeded {_TIMEOUT_SECONDS}s"
                stop_tracing = True
                return None

            if event == "return":
                final_state = _safe_snapshot(frame.f_locals)
                return local_tracer

            if event == "exception":
                # Exception occurred, captured in runner try-except
                return local_tracer

            if event == "line":
                if len(steps) >= _MAX_STEPS:
                    truncated = True
                    stop_tracing = True
                    return None

                lineno = frame.f_lineno

                # Update loop iteration counters
                # Check if current line is the header of any loop
                for l in loops:
                    if lineno == l.header_line:
                        l.counter += 1
                        # Reset inner loops
                        for inner in loops:
                            if inner.depth > l.depth and inner.start_line >= l.start_line and inner.end_line <= l.end_line:
                                inner.counter = 0

                # Determine active loop iteration for current line:
                # Find deepest enclosing loop
                active_loop = None
                max_depth = -1
                for l in loops:
                    if l.start_line <= lineno <= l.end_line and l.counter > 0:
                        if l.depth > max_depth:
                            max_depth = l.depth
                            active_loop = l

                loop_iter = active_loop.counter if active_loop is not None else None

                step_record = {
                    "step": len(steps) + 1,
                    "line": lineno,
                    "event": "line",
                    "variables": _safe_snapshot(frame.f_locals),
                    "loop_iteration": loop_iter,
                }
                steps.append(step_record)
                return local_tracer

            return local_tracer

        def global_tracer(frame, event, arg):
            if stop_tracing:
                return None
            if event == "call":
                # Only trace the target function frame
                if target_code and frame.f_code is target_code:
                    return local_tracer
                elif frame.f_code.co_name == function_name.split(".")[-1]:
                    return local_tracer
            return None

        # Execute inside thread with timeout
        exec_exception: list[Exception] = []

        def worker():
            old_tracer = sys.gettrace()
            sys.settrace(global_tracer)
            try:
                if "." in function_name and inspect.isfunction(func):
                    # Class method without instance: instantiate if possible
                    cls_name = function_name.split(".", 1)[0]
                    cls_obj = getattr(module, cls_name)
                    instance = cls_obj()
                    instance_method = getattr(instance, function_name.split(".", 1)[1])
                    instance_method(**args)
                else:
                    func(**args)
            except Exception as e:
                exec_exception.append(e)
            finally:
                sys.settrace(old_tracer)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(timeout=_TIMEOUT_SECONDS + 1.0)

        if t.is_alive():
            truncated = True
            error_msg = f"TimeoutError: Execution exceeded {_TIMEOUT_SECONDS}s (infinite loop)"
        elif exec_exception:
            exc = exec_exception[0]
            error_msg = f"{type(exc).__name__}: {exc}"

        # Clean up imported temp module
        sys.modules.pop(mod_name, None)

        return {
            "function_traced": function_name,
            "input_used": args,
            "steps": steps,
            "final_state": final_state,
            "error": error_msg,
            "truncated": truncated,
        }


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python tracer.py <file.py> <function_name> [args_json]"}), file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    func_name = sys.argv[2]
    args = {}
    if len(sys.argv) >= 4:
        try:
            args = json.loads(sys.argv[3])
        except Exception as e:
            print(json.dumps({"error": f"Invalid args JSON: {e}"}), file=sys.stderr)
            sys.exit(1)

    tracer = CodeTracer()
    result = tracer.trace(file_path, func_name, args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
