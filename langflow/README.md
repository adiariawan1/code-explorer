# Langflow Setup for Code Flow Explorer

1. **Import Flow**: Buka UI Langflow, pilih **My Projects** -> **Import**, lalu pilih file `code-flow-explorer.flow.json`.
2. **Global Variables**: Di menu Settings -> Global Variables, tambahkan `GEMINI_API_KEY` (atau `ANTHROPIC_API_KEY`).
3. **MCP Tool (Bob)**: Pastikan MCP server Bob terdaftar jika menggunakan fix generator; jika belum tersedia, Bob MCP berperan sebagai placeholder.
4. **Environment App**: Salin URL dan Flow ID ke `.env.local`:
   ```
   LANGFLOW_URL=http://localhost:7860
   LANGFLOW_FLOW_ID=<your-flow-id>
   ```
5. **Testing Endpoint via cURL**:
   ```bash
   curl -X POST "$LANGFLOW_URL/api/v1/run/$LANGFLOW_FLOW_ID" \
     -H "Content-Type: application/json" \
     -d '{"input_value": "{\"deleted_node\":\"validate_item\",\"code_snippet\":\"def validate_item(p): ...\",\"affected_nodes\":\"calculate_total\"}"}'
   ```
   Flow akan merespons dengan JSON `{"narrative": "...", "severity": "...", "reason": "..."}`.
