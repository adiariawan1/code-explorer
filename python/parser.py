"""
Code Flow Explorer — Deterministic AST Parser (no AI, pure Python ast).
Extracts functions, variables, usages, calls, and relationships.
"""

import ast
import json
import sys
from pathlib import Path


def _func_id(name: str) -> str:
    # replace dots for methods, e.g. Class.method -> Class_method
    sanitized = name.replace(".", "_")
    return f"func_{sanitized}"


def _var_id(name: str, scope: str) -> str:
    sanitized_scope = scope.replace(".", "_")
    if sanitized_scope.startswith("func_"):
        sanitized_scope = sanitized_scope[5:]
    return f"var_{name}_{sanitized_scope}"


class CodeParser:
    """Parse Python source code using built-in ast module into graph data."""

    def parse(self, file_path: str | Path) -> dict:
        path = Path(file_path).resolve()
        try:
            source = path.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as e:
            raise e

        source_lines = source.splitlines()

        # Pass 1: Discover all functions and class methods
        functions_map: dict[str, dict] = {}
        # Map simple function/method name to func_id
        name_to_func_id: dict[str, str] = {}

        class FunctionCollector(ast.NodeVisitor):
            def __init__(self):
                self.current_class: str | None = None

            def visit_ClassDef(self, node: ast.ClassDef):
                prev_class = self.current_class
                self.current_class = node.name
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.register_function(item, f"{node.name}.{item.name}")
                    else:
                        self.visit(item)
                self.current_class = prev_class

            def visit_FunctionDef(self, node: ast.FunctionDef):
                if self.current_class is None:
                    self.register_function(node, node.name)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                if self.current_class is None:
                    self.register_function(node, node.name)
                self.generic_visit(node)

            def register_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, full_name: str):
                fid = _func_id(full_name)
                name_to_func_id[node.name] = fid
                name_to_func_id[full_name] = fid

                # Extract source
                src = ""
                try:
                    src = ast.get_source_segment(source, node) or ""
                except Exception:
                    pass
                if not src and node.end_lineno is not None:
                    src = "\n".join(source_lines[node.lineno - 1 : node.end_lineno])

                params = [arg.arg for arg in node.args.args if arg.arg != "self" and arg.arg != "cls"]

                functions_map[fid] = {
                    "id": fid,
                    "name": full_name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "params": params,
                    "calls": [],
                    "called_by": [],
                    "source": src,
                    "ast_node": node,
                }

        collector = FunctionCollector()
        collector.visit(tree)

        # Pass 2: Extract calls, variables, and usages
        variables_map: dict[str, dict] = {}
        calls_list: list[tuple[str, str]] = []  # (caller_id, callee_id)

        # Helper to get line context string
        def get_line_context(lineno: int) -> str:
            if 1 <= lineno <= len(source_lines):
                return source_lines[lineno - 1].strip()
            return ""

        class BodyVisitor(ast.NodeVisitor):
            def __init__(self):
                # stack of (scope_id, scope_name)
                self.scope_stack: list[tuple[str, str]] = []

            @property
            def current_scope_id(self) -> str:
                return self.scope_stack[-1][0] if self.scope_stack else "global"

            @property
            def current_scope_name(self) -> str:
                return self.scope_stack[-1][1] if self.scope_stack else "global"

            def visit_ClassDef(self, node: ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        full_name = f"{node.name}.{item.name}"
                        fid = _func_id(full_name)
                        self.scope_stack.append((fid, full_name))
                        self.visit_function_body(item)
                        self.scope_stack.pop()
                    else:
                        self.visit(item)

            def visit_FunctionDef(self, node: ast.FunctionDef):
                fid = _func_id(node.name)
                self.scope_stack.append((fid, node.name))
                self.visit_function_body(node)
                self.scope_stack.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                fid = _func_id(node.name)
                self.scope_stack.append((fid, node.name))
                self.visit_function_body(node)
                self.scope_stack.pop()

            def visit_function_body(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
                for stmt in node.body:
                    self.visit(stmt)

            def visit_Call(self, node: ast.Call):
                # Detect direct calls to user functions (ast.Name only)
                if isinstance(node.func, ast.Name):
                    target_name = node.func.id
                    if target_name in name_to_func_id:
                        callee_id = name_to_func_id[target_name]
                        caller_id = self.current_scope_id
                        if caller_id != "global":
                            calls_list.append((caller_id, callee_id))
                self.generic_visit(node)

            def declare_variable(self, name: str, lineno: int, action: str = "declared"):
                scope_id = self.current_scope_id
                scope_name = self.current_scope_name
                vid = _var_id(name, scope_name)
                if vid not in variables_map:
                    variables_map[vid] = {
                        "id": vid,
                        "name": name,
                        "scope": scope_id,
                        "line_declared": lineno,
                        "usages": [],
                    }
                # Check if declaration/modified action already recorded on this line
                usages = variables_map[vid]["usages"]
                if not any(u["line"] == lineno and u["action"] in ("declared", "modified") for u in usages):
                    usages.append({
                        "line": lineno,
                        "action": action,
                        "context": get_line_context(lineno),
                    })

            def record_usage(self, name: str, lineno: int, action: str):
                scope_name = self.current_scope_name
                vid = _var_id(name, scope_name)
                # If variable not declared in local scope, check if it's declared globally
                if vid not in variables_map:
                    global_vid = _var_id(name, "global")
                    if global_vid in variables_map:
                        vid = global_vid

                if vid in variables_map:
                    usages = variables_map[vid]["usages"]
                    # If on the same line we already recorded 'returned', don't add duplicate 'used'
                    if action == "used" and any(u["line"] == lineno and u["action"] == "returned" for u in usages):
                        return
                    # Avoid duplicate identical actions on same line
                    if not any(u["line"] == lineno and u["action"] == action for u in usages):
                        usages.append({
                            "line": lineno,
                            "action": action,
                            "context": get_line_context(lineno),
                        })

            def visit_Assign(self, node: ast.Assign):
                lineno = node.lineno
                for target in node.targets:
                    for name in self.extract_names(target):
                        self.declare_variable(name, lineno, action="declared" if _var_id(name, self.current_scope_name) not in variables_map else "modified")
                # Visit the value (RHS) for usages
                self.visit(node.value)

            def visit_AugAssign(self, node: ast.AugAssign):
                lineno = node.lineno
                for name in self.extract_names(node.target):
                    self.declare_variable(name, lineno, action="modified")
                self.visit(node.value)

            def visit_AnnAssign(self, node: ast.AnnAssign):
                lineno = node.lineno
                for name in self.extract_names(node.target):
                    self.declare_variable(name, lineno, action="declared")
                if node.value:
                    self.visit(node.value)

            def visit_For(self, node: ast.For):
                lineno = node.lineno
                for name in self.extract_names(node.target):
                    self.declare_variable(name, lineno, action="declared" if _var_id(name, self.current_scope_name) not in variables_map else "modified")
                self.visit(node.iter)
                for stmt in node.body:
                    self.visit(stmt)
                for stmt in node.orelse:
                    self.visit(stmt)

            def visit_Return(self, node: ast.Return):
                if node.value is not None:
                    for name in self.extract_load_names(node.value):
                        self.record_usage(name, node.lineno, action="returned")
                    self.visit(node.value)

            def visit_Name(self, node: ast.Name):
                if isinstance(node.ctx, ast.Load):
                    # Check that this name is not a called function name
                    if node.id not in name_to_func_id:
                        self.record_usage(node.id, node.lineno, action="used")
                self.generic_visit(node)

            def extract_names(self, node: ast.AST):
                if isinstance(node, ast.Name):
                    yield node.id
                elif isinstance(node, (ast.Tuple, ast.List)):
                    for elt in node.elts:
                        yield from self.extract_names(elt)

            def extract_load_names(self, node: ast.AST):
                for n in ast.walk(node):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                        if n.id not in name_to_func_id:
                            yield n.id

        body_visitor = BodyVisitor()
        body_visitor.visit(tree)

        # Wire up calls and called_by in functions
        for caller_id, callee_id in calls_list:
            if caller_id in functions_map and callee_id in functions_map:
                caller = functions_map[caller_id]
                callee = functions_map[callee_id]
                if callee_id not in caller["calls"]:
                    caller["calls"].append(callee_id)
                if caller_id not in callee["called_by"]:
                    callee["called_by"].append(caller_id)

        # Build clean functions list
        functions: list[dict] = []
        for f in functions_map.values():
            functions.append({
                "id": f["id"],
                "name": f["name"],
                "line_start": f["line_start"],
                "line_end": f["line_end"],
                "params": f["params"],
                "calls": f["calls"],
                "called_by": f["called_by"],
                "source": f["source"],
            })

        # Build clean variables list
        variables: list[dict] = []
        for v in variables_map.values():
            variables.append({
                "id": v["id"],
                "name": v["name"],
                "scope": v["scope"],
                "line_declared": v["line_declared"],
                "usages": v["usages"],
            })

        # Build edges:
        # 1. 'calls' edges
        edges: list[dict] = []
        seen_edges: set[tuple[str, str, str]] = set()

        for f in functions:
            for callee_id in f["calls"]:
                edge_key = (f["id"], callee_id, "calls")
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "from": f["id"],
                        "to": callee_id,
                        "type": "calls",
                    })

        # 2. 'used_in' edges: from variable to functions that use it
        for v in variables:
            # If variable has a function scope, connect it to that function
            if v["scope"] != "global" and v["scope"] in functions_map:
                edge_key = (v["id"], v["scope"], "used_in")
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "from": v["id"],
                        "to": v["scope"],
                        "type": "used_in",
                    })
            elif v["scope"] == "global":
                # Connect global variable to every function where it is used
                for f in functions:
                    # Check if usages fall within function line ranges
                    has_usage_in_func = any(
                        f["line_start"] <= u["line"] <= f["line_end"]
                        for u in v["usages"]
                    )
                    if has_usage_in_func:
                        edge_key = (v["id"], f["id"], "used_in")
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            edges.append({
                                "from": v["id"],
                                "to": f["id"],
                                "type": "used_in",
                            })

        return {
            "file": path.name,
            "functions": functions,
            "variables": variables,
            "edges": edges,
        }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python parser.py <file.py>"}), file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    parser = CodeParser()
    try:
        result = parser.parse(file_path)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except SyntaxError as e:
        print(json.dumps({"error": f"Syntax error at line {e.lineno}: {e.msg}"}))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
