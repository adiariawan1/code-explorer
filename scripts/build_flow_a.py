import json
import copy
import os

STUDY_PATH = r"C:\Users\adi ariawan\Downloads\Study Planner - Complete.json"
TARGET_FILES = [
    "langflow/code-flow-risk-api.flow.json",
    "langflow/flow-a-api-mode.json"
]

def build_flow():
    with open(STUDY_PATH, "r", encoding="utf-8") as f:
        study = json.load(f)

    study_nodes = {n["id"]: n for n in study["data"]["nodes"]}

    # 1. ChatInput-01
    chat_input_src = study_nodes["ChatInput-9iO3O"]
    chat_input = copy.deepcopy(chat_input_src)
    chat_input["id"] = "ChatInput-01"
    chat_input["position"] = {"x": 100, "y": 300}
    chat_input["data"]["id"] = "ChatInput-01"
    # Default sample test payload
    sample_payload = json.dumps({
        "deleted_node": {"name": "calculate_total", "type": "function"},
        "code_snippet": "def calculate_total(items, discount):\n    total = 0\n    for price in items:\n        total += validate_item(price)\n    return total * (1 - discount)",
        "affected_nodes": [
            {"name": "checkout", "relation": "calls calculate_total"},
            {"name": "main", "relation": "calls checkout (indirect)"}
        ]
    })
    chat_input["data"]["node"]["template"]["input_value"]["value"] = sample_payload

    # 2. PromptTemplate-01
    prompt_src = study_nodes["Prompt Template-hH8lu"]
    prompt_node = copy.deepcopy(prompt_src)
    prompt_node["id"] = "PromptTemplate-01"
    prompt_node["position"] = {"x": 460, "y": 260}
    prompt_node["data"]["id"] = "PromptTemplate-01"
    
    # Custom fields and variable
    prompt_node["data"]["node"]["custom_fields"] = {"template": ["payload"]}
    
    # Replace old 'input' field with 'payload'
    template_dict = prompt_node["data"]["node"]["template"]
    if "input" in template_dict:
        del template_dict["input"]

    template_dict["payload"] = {
        "advanced": False,
        "api_editable": False,
        "display_name": "payload",
        "dynamic": False,
        "field_type": "str",
        "fileTypes": [],
        "file_path": "",
        "info": "",
        "input_types": ["Message"],
        "list": False,
        "load_from_db": False,
        "multiline": True,
        "name": "payload",
        "placeholder": "",
        "required": False,
        "show": True,
        "title_case": False,
        "type": "str",
        "value": ""
    }

    prompt_text = """You are a code risk analyst. Analyze the consequences if a function or variable is deleted from the codebase, based on the provided dependencies.

RULES:
1. Distinguish between direct and indirect dependencies (marked with '(indirect)'). The narrative must NEVER refer to indirect nodes as direct dependencies.
2. Local variables belonging to a deleted function are NOT broken components—they are simply deleted alongside their parent function, not broken callers.
3. Suggested fixes MUST NOT hide errors (PROHIBITED: 'return None', assigning 'None', or empty try-except/pass blocks). Fixes must preserve correct functional behavior or explicitly explain that callers must be adapted.
4. Return 'suggested_fix' ONLY if severity is 'high' or 'medium'. If severity is 'low', omit 'suggested_fix'.

OUTPUT FORMAT (must be followed exactly):
{{
  "narrative": "2-3 sentence explanation distinguishing direct callers/users from indirect downstream cascade",
  "severity": "high | medium | low",
  "reason": "short reason why this severity was chosen",
  "suggested_fix": {{
    "description": "explanation of the correct fix or caller adaptation",
    "code": "working Python code preserving valid data/behavior"
  }}
}}

---
EXAMPLE 1:
Input:
{{"deleted_node": {{"name": "calculateDiscount", "type": "function"}}, "code_snippet": "def calculateDiscount(price):\\n    return price * 0.9", "affected_nodes": [{{"name": "checkoutFlow", "relation": "calls calculateDiscount"}}]}}

Output:
{{"narrative": "Deleting calculateDiscount will cause checkoutFlow to fail, since this function is called directly to calculate the discounted price. Checkout will error out unless a replacement is provided.", "severity": "high", "reason": "Called directly within the checkout flow, a critical part of the transaction", "suggested_fix": {{"description": "Provide a replacement discount calculation or update checkoutFlow callers", "code": "def calculate_discount(price, rate=0.1):\\n    return price * (1 - rate)"}}}}

---
EXAMPLE 2:
Input:
{{"deleted_node": {{"name": "logDebugInfo", "type": "function"}}, "code_snippet": "def logDebugInfo(msg):\\n    print(msg)", "affected_nodes": [{{"name": "testHelper", "relation": "calls logDebugInfo in a test file"}}]}}

Output:
{{"narrative": "logDebugInfo is only used for debug logging in a test file, not part of the core business logic. Removing it is likely safe, just clean up the call in the test file afterward.", "severity": "low", "reason": "Only used in testing/debugging, not connected to core logic"}}

---
EXAMPLE 3:
Input:
{{"deleted_node": {{"name": "userSession", "type": "variable"}}, "code_snippet": "userSession = {{'id': user.id, 'role': user.role}}", "affected_nodes": [{{"name": "authMiddleware", "relation": "reads userSession.role"}}, {{"name": "dashboardView", "relation": "reads userSession.id (indirect)"}}]}}

Output:
{{"narrative": "userSession is directly read by authMiddleware for access control, while dashboardView indirectly depends on it for user data. Deleting this variable will break authentication directly and cause cascading failures in the dashboard.", "severity": "high", "reason": "Directly required by authentication middleware and indirectly impacts dashboard display", "suggested_fix": {{"description": "Keep userSession object or pass authenticated user context directly to middleware", "code": "class UserSession:\\n    def __init__(self, user_id, role):\\n        self.id = user_id\\n        self.role = role"}}}}

---
NOW ANALYZE THIS PAYLOAD:
{payload}

Respond ONLY with valid JSON in the format specified above.
OUTPUT MUST START DIRECTLY WITH A CURLY BRACE. NO PREAMBLE, NO CODE FENCES, NO EXPLANATION."""

    template_dict["template"]["value"] = prompt_text
    prompt_node["data"]["node"]["field_order"] = ["template", "payload", "use_double_brackets", "tool_placeholder"]

    # 3. LanguageModelComponent-01
    lang_src = study_nodes["LanguageModelComponent-obtNV"]
    lang_node = copy.deepcopy(lang_src)
    lang_node["id"] = "LanguageModelComponent-01"
    lang_node["position"] = {"x": 860, "y": 260}
    lang_node["data"]["id"] = "LanguageModelComponent-01"
    
    # Configure parameters per requirements
    lang_node["data"]["node"]["template"]["temperature"]["value"] = 0.2
    lang_node["data"]["node"]["template"]["max_tokens"]["value"] = 600
    lang_node["data"]["node"]["template"]["api_key"]["value"] = ""

    # 4. JSONCleaner-01
    cleaner_code = '''import json
import re
from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import BoolInput, HandleInput
from lfx.io import Output
from lfx.schema.message import Message


class JSONCleaner(Component):
    display_name = "JSON Cleaner"
    description = "Cleans code fences and validates JSON format."
    icon = "file-json"

    inputs = [
        HandleInput(
            name="json_string",
            display_name="JSON String",
            input_types=["Message", "str"],
            required=True,
            info="The raw JSON response from the language model",
        ),
        BoolInput(
            name="validate_json",
            display_name="Validate JSON",
            value=True,
            info="Validate and enforce clean JSON schema",
        ),
    ]

    outputs = [
        Output(
            display_name="Cleaned JSON String",
            name="clean_json",
            method="clean_and_validate",
        ),
    ]

    def clean_and_validate(self) -> Message:
        text = self.json_string.text if isinstance(self.json_string, Message) else str(self.json_string or "")
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\\s*```$", "", text)
            text = text.strip()

        idx = text.find("{")
        if idx != -1:
            text = text[idx:]
        last_idx = text.rfind("}")
        if last_idx != -1:
            text = text[:last_idx + 1]

        if getattr(self, "validate_json", True):
            try:
                data = json.loads(text)
            except Exception:
                data = {
                    "narrative": text,
                    "severity": "medium",
                    "reason": "Parsed from LLM output",
                }
            sev = str(data.get("severity", "medium")).lower()
            if sev not in ["high", "medium", "low"]:
                sev = "medium"
            data["severity"] = sev
            if sev == "low" and "suggested_fix" in data:
                del data["suggested_fix"]
            text = json.dumps(data, ensure_ascii=False)

        self.status = text
        return Message(text=text)
'''

    cleaner_node = {
        "id": "JSONCleaner-01",
        "type": "genericNode",
        "position": {"x": 1240, "y": 260},
        "selected": False,
        "data": {
            "id": "JSONCleaner-01",
            "type": "JSONCleaner",
            "node": {
                "base_classes": ["Component"],
                "beta": False,
                "conditional_paths": [],
                "custom_fields": {},
                "description": "Cleans code fences and validates JSON format.",
                "display_name": "JSON Cleaner",
                "documentation": "",
                "edited": False,
                "field_order": ["json_string", "validate_json"],
                "frozen": False,
                "icon": "file-json",
                "legacy": False,
                "minimized": False,
                "output_types": ["Message"],
                "outputs": [
                    {
                        "allows_loop": False,
                        "cache": True,
                        "display_name": "Cleaned JSON String",
                        "group_outputs": False,
                        "method": "clean_and_validate",
                        "name": "clean_json",
                        "selected": "Message",
                        "tool_mode": True,
                        "types": ["Message"],
                        "value": "__UNDEFINED__"
                    }
                ],
                "pinned": False,
                "template": {
                    "_type": "Component",
                    "code": {
                        "type": "code",
                        "value": cleaner_code
                    },
                    "json_string": {
                        "_input_type": "HandleInput",
                        "advanced": False,
                        "api_editable": False,
                        "display_name": "JSON String",
                        "dynamic": False,
                        "info": "The raw JSON response from the language model",
                        "input_types": ["Message", "str"],
                        "list": False,
                        "load_from_db": False,
                        "name": "json_string",
                        "override_skip": False,
                        "placeholder": "",
                        "required": True,
                        "show": True,
                        "title_case": False,
                        "trace_as_input": True,
                        "trace_as_metadata": True,
                        "track_in_telemetry": False,
                        "type": "other",
                        "value": ""
                    },
                    "validate_json": {
                        "_input_type": "BoolInput",
                        "advanced": False,
                        "api_editable": False,
                        "display_name": "Validate JSON",
                        "dynamic": False,
                        "info": "Validate and enforce clean JSON schema",
                        "list": False,
                        "list_add_label": "Add More",
                        "name": "validate_json",
                        "override_skip": False,
                        "placeholder": "",
                        "required": False,
                        "show": True,
                        "title_case": False,
                        "tool_mode": False,
                        "trace_as_metadata": True,
                        "track_in_telemetry": True,
                        "type": "bool",
                        "value": True
                    }
                }
            }
        }
    }

    # 5. ChatOutput-01
    chat_output_src = study_nodes["ChatOutput-ObU8w"]
    chat_output = copy.deepcopy(chat_output_src)
    chat_output["id"] = "ChatOutput-01"
    chat_output["position"] = {"x": 1600, "y": 300}
    chat_output["data"]["id"] = "ChatOutput-01"

    # Edges definition using Langflow character encoding œ for handles
    def lf_handle(d):
        return json.dumps(d, separators=(",", ":")).replace('"', '\u0153')

    # Edge 1: Chat Input (Message) -> Prompt Template (payload)
    src_h_1 = {"dataType": "ChatInput", "id": "ChatInput-01", "name": "message", "output_types": ["Message"]}
    tgt_h_1 = {"fieldName": "payload", "id": "PromptTemplate-01", "inputTypes": ["Message"], "type": "str"}
    edge_1 = {
        "id": f"xy-edge__ChatInput-01{lf_handle(src_h_1)}-PromptTemplate-01{lf_handle(tgt_h_1)}",
        "source": "ChatInput-01",
        "target": "PromptTemplate-01",
        "sourceHandle": lf_handle(src_h_1),
        "targetHandle": lf_handle(tgt_h_1),
        "data": {
            "sourceHandle": src_h_1,
            "targetHandle": tgt_h_1
        }
    }

    # Edge 2: Prompt Template (Prompt) -> Language Model (Input)
    src_h_2 = {"dataType": "Prompt Template", "id": "PromptTemplate-01", "name": "prompt", "output_types": ["Message"]}
    tgt_h_2 = {"fieldName": "input_value", "id": "LanguageModelComponent-01", "inputTypes": ["Message"], "type": "str"}
    edge_2 = {
        "id": f"xy-edge__PromptTemplate-01{lf_handle(src_h_2)}-LanguageModelComponent-01{lf_handle(tgt_h_2)}",
        "source": "PromptTemplate-01",
        "target": "LanguageModelComponent-01",
        "sourceHandle": lf_handle(src_h_2),
        "targetHandle": lf_handle(tgt_h_2),
        "data": {
            "sourceHandle": src_h_2,
            "targetHandle": tgt_h_2
        }
    }

    # Edge 3: Language Model (Model Response) -> JSON Cleaner (JSON String)
    src_h_3 = {"dataType": "LanguageModelComponent", "id": "LanguageModelComponent-01", "name": "text_output", "output_types": ["Message"]}
    tgt_h_3 = {"fieldName": "json_string", "id": "JSONCleaner-01", "inputTypes": ["Message", "str"], "type": "other"}
    edge_3 = {
        "id": f"xy-edge__LanguageModelComponent-01{lf_handle(src_h_3)}-JSONCleaner-01{lf_handle(tgt_h_3)}",
        "source": "LanguageModelComponent-01",
        "target": "JSONCleaner-01",
        "sourceHandle": lf_handle(src_h_3),
        "targetHandle": lf_handle(tgt_h_3),
        "data": {
            "sourceHandle": src_h_3,
            "targetHandle": tgt_h_3
        }
    }

    # Edge 4: JSON Cleaner (Cleaned JSON String) -> Chat Output (Inputs)
    src_h_4 = {"dataType": "JSONCleaner", "id": "JSONCleaner-01", "name": "clean_json", "output_types": ["Message"]}
    tgt_h_4 = {"fieldName": "input_value", "id": "ChatOutput-01", "inputTypes": ["Data", "JSON", "DataFrame", "Table", "Message"], "type": "other"}
    edge_4 = {
        "id": f"xy-edge__JSONCleaner-01{lf_handle(src_h_4)}-ChatOutput-01{lf_handle(tgt_h_4)}",
        "source": "JSONCleaner-01",
        "target": "ChatOutput-01",
        "sourceHandle": lf_handle(src_h_4),
        "targetHandle": lf_handle(tgt_h_4),
        "data": {
            "sourceHandle": src_h_4,
            "targetHandle": tgt_h_4
        }
    }

    flow_data = {
        "name": "Code Flow Explorer — Flow A (API Mode)",
        "description": "Flow A untuk Code Flow Explorer: Chat Input -> Prompt Template -> Language Model -> JSON Cleaner -> Chat Output. Menganalisis risiko penghapusan node.",
        "id": "code-flow-risk-api",
        "is_component": False,
        "last_tested_version": "1.11.5",
        "locked": False,
        "data": {
            "viewport": {"x": 0, "y": 0, "zoom": 1},
            "nodes": [
                chat_input,
                prompt_node,
                lang_node,
                cleaner_node,
                chat_output
            ],
            "edges": [
                edge_1,
                edge_2,
                edge_3,
                edge_4
            ]
        }
    }

    for target in TARGET_FILES:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(flow_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully generated {target}")

if __name__ == "__main__":
    build_flow()
