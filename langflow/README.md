# Panduan Impor Flow Langflow (Code Flow Explorer)

### 1. Impor Flow A (Mode API Key)
1. Buka dashboard Langflow -> klik **New Flow** -> **Import** -> pilih `flow-a-api-mode.json`.
2. Buka **Settings > Global Variables**, tambahkan `GEMINI_API_KEY` (atau pasang key di node `Language Model`).
3. Buka **Playground** untuk menguji payload JSON.
4. Salin URL dan Flow ID ke `.env.local`:
   ```env
   LANGFLOW_URL=http://localhost:7860
   LANGFLOW_FLOW_ID=<id-flow-a>
   LANGFLOW_MODEL_NODE_ID=LanguageModelComponent-01
   ```

### 2. Impor Flow B (Mode Bob MCP)
1. Di Langflow, klik **New Flow** -> **Import** -> pilih `flow-b-bob-mode.json`.
2. Flow ini mengekspos tool MCP `get_delete_impact` tanpa model bahasa.
3. Buka menu **Endpoint / MCP Server** pada flow tersebut, salin konfigurasi tool `get_delete_impact`.
4. Tempel konfigurasi MCP ke Bob IDE (atau simpan di `.env.local` sebagai `NEXT_PUBLIC_BOB_MCP_CONFIG`).

### 3. Pengujian Playground
Uji Flow A di Playground dengan mengirimkan payload JSON:
- **Test 1 (`calculate_total`)**: Menghasilkan severity `high`/`medium` dan saran fix valid tanpa `return None`.
- **Test 2 (`unused_helper`)**: Menghasilkan severity `low` tanpa saran fix.
