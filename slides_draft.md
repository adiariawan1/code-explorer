# Draf Slide Presentasi: Code Flow Explorer
IBM Hackathon 2026 Submission Deck (Format Slide Tanpa Video)

---

### Slide 1: Judul & Tagline
**Code Flow Explorer**  
*Interactive Python Call-Graph & Runtime Variable Flow Analyzer with Deletion Risk AI*  
- Solusi pemahaman codebase instan bergaya Blender node editor.
- Parsing & tracing lokal deterministik, zero-server-storage privacy.

---

### Slide 2: Permasalahan (The Problem)
- **Codebase Onboarding Lambat:** Developer butuh berjam-jam membaca ribuan baris kode untuk memahami ketergantungan antar fungsi dan variabel.
- **Takut Melakukan Refactoring:** Developer ragu menghapus atau mengubah kode lama karena tidak mengetahui efek domino/side-effect ke modul lain.
- **Find Usages IDE Terlalu Tekstual:** Daftar pencarian teks di IDE mengharuskan developer mengecek satu per satu secara manual tanpa gambaran visual menyeluruh.

---

### Slide 3: Solusi Kami (The Solution)
- **Node Graph Interaktif:** Menampilkan fungsi dan variabel sebagai graph node bersih dengan layout otomatis (Dagre) ala Blender node editor.
- **Visual Diferensiasi Jelas:** Garis koneksi membedakan panggilan fungsi (`calls`) dan pemakaian variabel (`used_in`) secara intuitif.
- **Deteksi Otomatis:** Menyorot *dead code* (fungsi tak terpakai) dan *central functions* secara visual.
- **Simulasi Hapus (What-if Deletion):** Cukup pilih node dan klik "Simulasikan Hapus" untuk melihat cascade dampak ke modul hilir (*downstream*).

---

### Slide 4: Cara Kerja Sistem (Architecture)
1. **Lapisan Deterministik (Lokal & Cepat):**
   - **Parser AST:** Ekstraksi fungsi, parameter, variabel, dan relasi secara presisi tanpa AI (modul `ast` Python).
   - **Tracer `sys.settrace`:** Merekam eksekusi nyata nilai variabel per baris dan per iterasi loop.
2. **Lapisan Visualisasi (Client-Side Only):**
   - Hasil analisis di-kompresi menggunakan LZ-String dan disematkan langsung di URL browser.
3. **Lapisan Penalaran AI (On-Demand):**
   - AI hanya dipanggil saat tombol "Simulasikan Hapus" ditekan lewat Langflow + LLM.
   - Severity tinggi/sedang memicu MCP tool (Bob) untuk memberikan saran kode perbaikan instan.

---

### Slide 5: Privasi Melalui Arsitektur (Privacy by Design)
> "Server kami tidak menyimpan kode Anda."
- **Zero Server Code Storage:** Source code dan hasil analisis tidak pernah diunggah atau disimpan di database backend. Semua data hidup di URL browser developer.
- **AI On-Demand dengan Snippet Minimal:** AI hanya menerima potongan kode fungsi yang dipilih dan daftar relasi langsung, bukan keseluruhan repositori.
- **Firebase Minimalis:** Firestore hanya mencatat hitungan pemakaian kuota per perangkat (*device ID*), tanpa metadata kode apa pun.

---

### Slide 6: Model Bisnis & Freemium
- **Free Tier:** 5 analisis gratis per bulan per perangkat (soft limit via Firebase Firestore).
- **Bring Your Own Key (BYOK):** Pengguna dapat memasang API key LLM sendiri (Claude / Gemini / GPT) di browser untuk pemakaian *unlimited* tanpa biaya tambahan.
- **Enterprise Roadmap:** Opsi self-hosted / on-premise container untuk organisasi dengan kepatuhan keamanan data ketat.

---

### Slide 7: Roadmap Pengembangan
- **Multi-language Support:** Dukungan analisis untuk JavaScript / TypeScript dan bahasa C.
- **Sandbox Execution:** Simulasi hapus berbasis eksekusi virtual sandbox.
- **Team Workspace:** Berbagi visualisasi flow antar tim tanpa mengorbankan privasi kode.

---

### Slide 8: Demo & Akses
- **CLI Command:** `npx code-flow-explorer ./sample.py`
- **Demo Online:** `https://code-flow-explorer.vercel.app` (Buka dengan tombol *View sample demo*)
- **Status Integrasi:** CLI deterministik, UI Web Dagre, dan AI Simulation Route 100% berfungsi.
