# Code Flow Explorer

Visualizes Python code as an interactive Blender-style node graph with dependency tracing and AI risk simulation.

## Requirements
- Node.js 20+ & npm
- Python 3.10+ (standard library only)

## Quick Start
1. Install dependencies:
   ```bash
   cd web && npm install
   ```
2. Start the web viewer:
   ```bash
   cd web && npm run dev
   ```
3. Analyze any Python file from your terminal:
   ```bash
   node bin/cli.js sample/sample.py
   # or from web/: node bin/cli.js ../sample/sample.py
   ```
4. Run tests:
   ```bash
   python python/test_analysis.py
   cd web && npm run build && npm run lint
   ```

No external server or database is required for local development. The app runs completely offline with client-side URL encoding and mock AI simulation fallbacks.
