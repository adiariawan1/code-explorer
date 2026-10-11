"""
Unit tests for CodeParser and CodeTracer asserting on sample/sample.py.
Requirement from Section 26.1 and 26.4.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from python.parser import CodeParser
from python.tracer import CodeTracer


def test_parser():
    sample_path = REPO_ROOT / "sample" / "sample.py"
    assert sample_path.exists(), f"Sample file not found at {sample_path}"

    parser = CodeParser()
    res = parser.parse(sample_path)

    funcs = {f["name"]: f for f in res["functions"]}
    assert len(funcs) == 5, f"Expected 5 functions, got {len(funcs)}: {list(funcs.keys())}"

    assert "unused_helper" in funcs
    assert len(funcs["unused_helper"]["called_by"]) == 0, "unused_helper should have no callers"

    assert "main" in funcs
    assert len(funcs["main"]["called_by"]) == 0, "main should have no callers"

    # Verify calls edges
    edge_pairs = [(e["from"], e["to"], e["type"]) for e in res["edges"]]
    assert ("func_checkout", "func_calculate_total", "calls") in edge_pairs
    assert ("func_calculate_total", "func_validate_item", "calls") in edge_pairs
    assert ("func_main", "func_checkout", "calls") in edge_pairs

    # Verify called_by inverse mapping
    assert "func_calculate_total" in funcs["validate_item"]["called_by"]
    assert "func_checkout" in funcs["calculate_total"]["called_by"]
    assert "func_main" in funcs["checkout"]["called_by"]

    # Verify each function has source
    for f in res["functions"]:
        assert f["source"], f"Function {f['name']} is missing source segment"

    # Verify variables scope ids
    var_map = {v["name"]: v for v in res["variables"] if v["scope"] == "func_calculate_total"}
    assert "total" in var_map
    assert var_map["total"]["id"] == "var_total_calculate_total"
    assert "price" in var_map
    assert var_map["price"]["id"] == "var_price_calculate_total"

    print("[OK] Parser tests passed!")


def test_tracer_success():
    sample_path = REPO_ROOT / "sample" / "sample.py"
    tracer = CodeTracer()
    args = {"items": [10, 20, 30], "discount": 0.1}
    res = tracer.trace(sample_path, "calculate_total", args)

    assert res["error"] is None, f"Unexpected tracer error: {res['error']}"
    assert not res["truncated"], "Trace was unexpectedly truncated"

    # Filter loop body steps (line 11 is 'total += validate_item(price)')
    loop_body_steps = [s for s in res["steps"] if s["line"] == 11]
    assert len(loop_body_steps) == 3, f"Expected 3 loop body steps, got {len(loop_body_steps)}"
    iters = [s["loop_iteration"] for s in loop_body_steps]
    assert iters == [1, 2, 3], f"Expected loop iterations [1, 2, 3], got {iters}"

    # Verify step after loop has null loop_iteration
    post_loop_steps = [s for s in res["steps"] if s["line"] in (12, 13)]
    for s in post_loop_steps:
        assert s["loop_iteration"] is None, f"Expected None loop_iteration after loop, got {s['loop_iteration']}"

    # Verify final_state.total is ~54.0
    final_total = res["final_state"].get("total")
    assert final_total is not None, "final_state missing 'total'"
    assert abs(final_total - 54.0) < 1e-6, f"Expected total ~54.0, got {final_total}"

    print("[OK] Tracer success test passed!")


def test_tracer_error():
    sample_path = REPO_ROOT / "sample" / "sample.py"
    tracer = CodeTracer()
    args = {"items": [-1], "discount": 0}
    res = tracer.trace(sample_path, "calculate_total", args)

    assert res["error"] is not None, "Expected tracer to record error"
    assert "negative price" in res["error"], f"Expected 'negative price' in error, got {res['error']}"
    assert len(res["steps"]) > 0, "Expected steps to be preserved despite error"

    print("[OK] Tracer error test passed!")


def test_tracer_timeout():
    import tempfile, os
    code = """
def runaway():
    while True:
        pass
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp = f.name

    try:
        tracer = CodeTracer()
        res = tracer.trace(tmp, "runaway", {})
        assert res["truncated"] is True
        assert res["error"] is not None and "TimeoutError" in res["error"]
        print("[OK] Tracer timeout test passed!")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    test_parser()
    test_tracer_success()
    test_tracer_error()
    test_tracer_timeout()
    print("\nALL ANALYSIS TESTS PASSED!")
