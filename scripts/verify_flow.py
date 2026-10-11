import json
import re
import sys

def verify_flow(flow_path):
    print(f"=== Verifying Flow: {flow_path} ===")
    errors = []
    warnings = []

    with open(flow_path, "r", encoding="utf-8") as f:
        flow = json.load(f)

    data = flow.get("data", {})
    nodes = {n["id"]: n for n in data.get("nodes", [])}
    edges = data.get("edges", [])

    print(f"[OK] Flow contains {len(nodes)} nodes and {len(edges)} edges.")

    # 1. Verify Edge references to existing nodes
    print("\n1. Checking edge references to existing nodes...")
    for idx, edge in enumerate(edges):
        src = edge.get("source")
        tgt = edge.get("target")
        if src not in nodes:
            errors.append(f"Edge {idx} ({edge.get('id')}): Source node '{src}' does not exist.")
        if tgt not in nodes:
            errors.append(f"Edge {idx} ({edge.get('id')}): Target node '{tgt}' does not exist.")
        print(f"  - Edge {idx+1}: {src} -> {tgt} [VALID]")

    # 2. Check handle existence on source and target nodes
    print("\n2. Checking handle existence on source and target nodes...")
    for idx, edge in enumerate(edges):
        src_id = edge.get("source")
        tgt_id = edge.get("target")
        src_node = nodes.get(src_id, {})
        tgt_node = nodes.get(tgt_id, {})

        # Parse source handle info
        src_h_data = edge.get("data", {}).get("sourceHandle", {})
        tgt_h_data = edge.get("data", {}).get("targetHandle", {})

        src_output_name = src_h_data.get("name")
        tgt_field_name = tgt_h_data.get("fieldName")

        # Verify source node output exists
        src_outputs = src_node.get("data", {}).get("node", {}).get("outputs", [])
        src_output_match = next((o for o in src_outputs if o.get("name") == src_output_name), None)
        if not src_output_match:
            errors.append(f"Edge {idx+1}: Source node '{src_id}' does not have output '{src_output_name}'.")
        else:
            print(f"  - Source Handle: '{src_id}'.output['{src_output_name}'] exists (display: '{src_output_match.get('display_name')}').")

        # Verify target node input field exists
        tgt_template = tgt_node.get("data", {}).get("node", {}).get("template", {})
        if tgt_field_name not in tgt_template:
            errors.append(f"Edge {idx+1}: Target node '{tgt_id}' does not have template input field '{tgt_field_name}'.")
        else:
            tgt_field = tgt_template.get(tgt_field_name, {})
            display_name = tgt_field.get("display_name", tgt_field_name) if isinstance(tgt_field, dict) else tgt_field_name
            print(f"  - Target Handle: '{tgt_id}'.input['{tgt_field_name}'] exists (display: '{display_name}').")

    # 3. Check type compatibility
    print("\n3. Checking type compatibility between connected handles...")
    for idx, edge in enumerate(edges):
        src_id = edge.get("source")
        tgt_id = edge.get("target")
        src_node = nodes.get(src_id, {})
        tgt_node = nodes.get(tgt_id, {})

        src_h_data = edge.get("data", {}).get("sourceHandle", {})
        tgt_h_data = edge.get("data", {}).get("targetHandle", {})

        src_types = set(src_h_data.get("output_types", []))
        tgt_types = set(tgt_h_data.get("inputTypes", []))

        # Check intersection or wildcard 'other'
        common = src_types.intersection(tgt_types)
        if not common and "other" not in tgt_types and "other" not in src_types:
            errors.append(f"Edge {idx+1} ({src_id} -> {tgt_id}): Type mismatch! Source types {src_types} incompatible with target types {tgt_types}.")
        else:
            overlap = list(common) if common else ['compatible generic/other']
            print(f"  - Edge {idx+1} ({src_id} -> {tgt_id}): Type match on {overlap} [PASS]")

    # 4. Check Prompt Template variable configuration
    print("\n4. Checking Prompt Template payload variable...")
    prompt_node = None
    for n in nodes.values():
        if "Prompt" in n.get("data", {}).get("type", "") or "Prompt" in n.get("id", ""):
            prompt_node = n
            break

    if not prompt_node:
        errors.append("Prompt Template node not found.")
    else:
        p_node_data = prompt_node.get("data", {}).get("node", {})
        custom_fields = p_node_data.get("custom_fields", {})
        template_vars = custom_fields.get("template", [])
        p_template = p_node_data.get("template", {})

        if "payload" not in template_vars:
            errors.append(f"Prompt Template custom_fields does not contain 'payload'. Found: {template_vars}")
        else:
            print("  - 'payload' is declared in custom_fields['template'] [PASS]")

        if "payload" not in p_template:
            errors.append("Prompt Template node template dictionary does not define 'payload' input.")
        else:
            payload_field = p_template["payload"]
            print(f"  - 'payload' field is defined with input_types={payload_field.get('input_types')} [PASS]")

        # Check prompt text variables
        template_text = p_template.get("template", {}).get("value", "")
        extracted_vars = re.findall(r"(?<!\{)\{([a-zA-Z0-9_]+)\}(?!\})", template_text)
        print(f"  - Single-brace variables in prompt text: {extracted_vars}")
        if extracted_vars != ["payload"]:
            errors.append(f"Prompt text must ONLY contain {{payload}} as a single variable. Found: {extracted_vars}")
        else:
            print("  - Prompt text has exactly one variable: {payload} [PASS]")

        # Test execution of Python string formatter to prevent ValueError: Single '}'
        try:
            test_formatted = template_text.format(payload='{"deleted_node": "test"}')
            print("  - Prompt text passes Python str.format() validation without ValueError or unescaped braces [PASS]")
        except Exception as fmt_err:
            errors.append(f"Prompt text format syntax error: {type(fmt_err).__name__}: {fmt_err}")

    # 5. Check for accidental API key or secrets in JSON
    print("\n5. Checking for hardcoded API keys or secrets...")
    with open(flow_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # Regex patterns for typical keys
    key_patterns = [
        (r"AIza[0-9A-Za-z-_]{35}", "Google Gemini API key pattern"),
        (r"sk-[a-zA-Z0-9-_]{20,}", "OpenAI API key pattern"),
        (r"Bearer\s+[a-zA-Z0-9-_\.]+", "Bearer token pattern")
    ]
    for pattern, name in key_patterns:
        match = re.search(pattern, raw_content)
        if match:
            errors.append(f"Found hardcoded secret matching {name}: {match.group()[:8]}...")

    # Check api_key field in LanguageModelComponent specifically
    for n in nodes.values():
        template = n.get("data", {}).get("node", {}).get("template", {})
        if "api_key" in template:
            key_val = template["api_key"].get("value", "")
            if key_val and str(key_val).strip() != "":
                errors.append(f"Node '{n['id']}' has non-empty api_key value: '{key_val[:4]}...'")
            else:
                print(f"  - Node '{n['id']}': api_key field is empty (uses Langflow Global Variable) [PASS]")

    # Final Summary
    print("\n=== VERIFICATION SUMMARY ===")
    if errors:
        print(f"[FAIL] Found {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("[SUCCESS] All checks passed successfully! Flow is formally verified.")
        return True

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "langflow/code-flow-risk-api.flow.json"
    success = verify_flow(path)
    sys.exit(0 if success else 1)
