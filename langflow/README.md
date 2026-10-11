# Panduan Impor & Tes Flow A (Langflow)

1. Buka Langflow -> klik **New Flow** -> **Import** -> pilih `code-flow-risk-api.flow.json`.
2. Masukkan API Key di node **Language Model** (kolom API Key) atau via **Settings > Global Variables**.
3. Di node **Language Model**, pastikan provider dan model telah dipilih (mis. Google Generative AI / `gemini-2.0-flash`).
4. Klik **Playground**, lalu tempel contoh JSON berikut ke **Input Text**:
```json
{"deleted_node":{"name":"calculate_total","type":"function"},"code_snippet":"def calculate_total(items, discount):\n    total = 0\n    for price in items:\n        total += validate_item(price)\n    return total * (1 - discount)","affected_nodes":[{"name":"checkout","relation":"calls calculate_total"},{"name":"main","relation":"calls checkout (indirect)"}]}
```
5. Klik **Send**. Respons akan mengembalikan JSON valid (`narrative`, `severity`, `reason`, `suggested_fix`).

*Catatan: Status flow ditandai belum teruji secara live sampai dikonfirmasi melalui pengujian langsung di Playground oleh Anda.*
