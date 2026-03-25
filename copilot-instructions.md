<!-- GSD:project-start source:PROJECT.md -->
## Project

**Katalog – Agentenbasiertes Produktkatalog-System**

**Core Value:** Das System muss neue CSV-Strukturen ohne manuelle Konfiguration verstehen und alle verfügbaren Produktinformationen korrekt über die Artikelnummer zusammenführen können.

### Constraints

- **Tech Stack**: LLM-basierte Agenten (GPT-4/Claude) für CSV-Analyse und Sprachveredlung
- **Interface**: Web UI (nicht CLI-only)
- **Sprache**: Ausschließlich Deutsch für alle Ausgaben und Text-Veredlungen
- **Ordnerstruktur**: CSV-Dateien in `assets/`, Bilder in `bilder/`
- **Bildformat**: Mehrere Bilder pro Produkt möglich, Zuordnung über Artikelnummer
- **Ausgabeformat**: HTML first (PDF später), A4 Hochformat
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Executive Summary
## Recommended Stack
### 1. Core Backend Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.110+ | Web API & file upload handling | Modern async Python framework with automatic OpenAPI docs, excellent type hint support, high performance. Perfect for handling CSV/image uploads and serving generated catalogs. Much cleaner than Flask for async LLM calls. |
| Python | 3.11+ | Runtime | 3.11+ for performance improvements (10-60% faster than 3.10). Type hints are essential for this project. |
| **Uvicorn** | 0.27+ | ASGI server | Production-ready async server for FastAPI. Use with `--workers` for multi-process. |
| **Pydantic** | 2.6+ | Data validation & schemas | Built into FastAPI. Type-safe data models for CSV mappings, product data structures. V2 is 5-50x faster than v1. |
### 2. LLM Agent Orchestration
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Anthropic SDK** | 0.18+ | Claude API for CSV analysis & text enhancement | Direct SDK approach. Claude 3.5 Sonnet excels at structured data analysis and German language tasks. Simpler than LangChain for this use case—you don't need complex chains, just smart prompts for CSV schema detection and description enhancement. |
| **Instructor** | 1.0+ | Structured LLM outputs | Type-safe structured outputs from Claude. Ensures CSV mapping analysis returns predictable JSON schemas. Wraps Anthropic SDK with Pydantic validation. |
- LangChain: Over-engineered for this use case. Adds complexity without benefits. Direct SDK calls with good prompting are more maintainable.
- LlamaIndex: Designed for RAG (Retrieval-Augmented Generation). Overkill when you're processing CSVs directly, not searching document stores.
### 3. Data Processing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Polars** | 0.20+ | CSV parsing & data transformation | 10-100x faster than pandas for large datasets (500+ products). Lazy evaluation, excellent memory efficiency. Better type system. Modern DataFrame library built in Rust. |
| **DuckDB** (optional) | 0.10+ | SQL queries on CSV if needed | In-process SQL engine. Can query CSVs directly with SQL if complex joins are needed. Works alongside Polars. |
- Slower for 500+ product catalogs
- Polars has better null handling (important for "missing data" requirement)
- Polars API is cleaner and more consistent
- pandas is still fine, but Polars is the modern choice for new projects
### 4. HTML Generation & PDF Export
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Jinja2** | 3.1+ | HTML templating | De facto standard for Python HTML templates. Clean separation of logic and presentation. |
| **Playwright** | 1.42+ | HTML → PDF conversion | Headless Chromium for pixel-perfect PDF rendering. Handles CSS print media, complex layouts, web fonts. More reliable than wkhtmltopdf. Can screenshot for previews. |
| **WeasyPrint** (alternative) | 61+ | HTML → PDF (CSS Paged Media) | Pure Python alternative. Better for simple layouts. Supports CSS Paged Media spec. Use if you need full Python stack without Node.js dependency. |
- wkhtmltopdf — Unmaintained since 2020, known rendering bugs
- pdfkit — Python wrapper for wkhtmltopdf, same issues
- ReportLab — Low-level PDF generation, no HTML input
### 5. Image Processing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pillow** | 10.2+ | Image resizing, optimization, format conversion | Standard Python image library. Handles JPEG/PNG/WebP. Good for resizing product images for web/print. |
| **blake3** (optional) | 0.4+ | Fast image hashing for deduplication | If you need to detect duplicate images across 500+ products. 10x faster than MD5/SHA. |
- ImageMagick via subprocess — Pillow is sufficient and more Pythonic
- OpenCV — Overkill for simple image transformations
### 6. Frontend Stack
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **React** | 18.2+ | UI framework | Industry standard for complex UIs. Needed for table editing with 500+ rows. Mature ecosystem. |
| **TypeScript** | 5.3+ | Type safety | Essential for maintainable frontend code. Catches errors at compile time. |
| **Vite** | 5.1+ | Build tool | Faster than Webpack. Modern standard for React projects. Hot reload is excellent. |
| **TanStack Table** | 8.13+ | Table component for data editing | Best React table library. Handles sorting, filtering, editing for CSV mapping corrections. Much better than building from scratch. |
| **Tailwind CSS** | 3.4+ | Styling | Utility-first CSS. Faster development than custom CSS. Great for modern, clean catalog designs. |
| **React Hook Form** | 7.50+ | Form validation | For CSV upload forms, mapping corrections. Minimal re-renders, great DX. |
| **Axios** | 1.6+ | HTTP client | For API calls to FastAPI backend. Better API than fetch for this use case. |
### 7. Database (Optional)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **SQLite** | 3.45+ | Persist CSV mappings & corrections | Serverless, zero-config. Perfect for single-user system. Stores learned CSV schema mappings, user corrections. |
| **SQLModel** | 0.0.16+ | ORM & validation | SQLAlchemy ORM with Pydantic models. Type-safe database operations. Integrates perfectly with FastAPI. |
### 8. Deployment & Infrastructure
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Docker** | 24+ | Containerization | Single-user system can run as Docker Compose stack. Bundles Python backend + Node frontend + Playwright browser. |
| **Docker Compose** | 2.24+ | Multi-container orchestration | Simple deployment: `docker-compose up`. Handles FastAPI + React + Playwright dependencies. |
## Anti-Stack (What NOT to Use)
| Technology | Why Avoid |
|------------|-----------|
| **Django** | Too heavyweight. Admin panel not needed. ORM overkill for CSV processing. |
| **Flask** | Older sync model. FastAPI is the modern replacement. |
| **LangChain** | Over-engineered. Direct SDK calls are cleaner for this use case. Adds unnecessary abstraction layers. |
| **pandas** | Still fine, but Polars is faster and more modern. pandas if team already expert. |
| **wkhtmltopdf/pdfkit** | Unmaintained, rendering bugs, poor CSS support. Use Playwright or WeasyPrint instead. |
| **jQuery** | Outdated. React or htmx for modern UIs. |
| **Selenium** | Replaced by Playwright. Slower, more flaky. |
| **Celery** | Async task queue not needed for single-user system. FastAPI background tasks are sufficient. |
| **Redis** | Cache not needed for 500 products. SQLite is enough. |
## Installation Blueprint
### Backend (Python)
# Create virtual environment
# Install dependencies
# Install Playwright browsers
### Frontend (React)
# Create Vite + React + TypeScript project
# Install dependencies
# Initialize Tailwind
### Full Stack with Docker
# Dockerfile.backend
# Dockerfile.frontend
# docker-compose.yml
## Dependency Management
### Python: Use `uv` (Recommended for 2026)
# Install uv (Rust-based pip replacement, 10-100x faster)
# Create project
# Add dependencies
# Lock dependencies
# Install from lock
- 10-100x faster dependency resolution
- Compatible with pip/requirements.txt
- Rust-based, actively maintained by Astral (makers of Ruff)
- Industry momentum in 2025/2026
## Architecture Implications
### Agent Workflow Design
# Recommended structure with Anthropic SDK + Instructor
# Schema detection agent
# Text enhancement agent
- No framework overhead
- Type-safe responses (Pydantic)
- Easy to test and debug
- Scales to more agents without complexity
## Performance Considerations
| Concern | At 100 products | At 500 products (target) | At 5000+ products |
|---------|-----------------|-------------------------|-------------------|
| CSV parsing | Polars: <100ms | Polars: <500ms | Polars: 1-2s (still fine) |
| LLM calls (schema) | 1 call/CSV (2-5s) | 1 call/CSV (2-5s) | Same (not per-product) |
| LLM calls (text) | Batch 10: ~30s | Batch 50: ~2-3min | Batch in chunks, parallel |
| HTML generation | Jinja: <1s | Jinja: <5s | Jinja: <30s |
| PDF generation | Playwright: ~5-10s | Playwright: ~30-60s | Consider splitting catalogs |
| Image processing | Pillow: <5s | Pillow: <20s | Pillow: 2-3min |
| **Total pipeline** | ~1-2min | ~5-10min | ~30min+ (optimize async) |
## Versioning Strategy
# pyproject.toml (uv/poetry)
## Development vs Production
| Tool | Development | Production |
|------|-------------|------------|
| Python server | `uvicorn main:app --reload` | `uvicorn main:app --workers 4` |
| Frontend | `npm run dev` | `npm run build` + `npm run preview` |
| Database | SQLite file | SQLite file (same) |
| LLM model | Claude 3.5 Sonnet | Claude 3.5 Sonnet (same) |
| Logging | Console | Structured JSON + file |
| Error handling | Debug tracebacks | User-friendly messages |
## Cost Estimates (LLM API)
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens
- CSV schema analysis (2 CSVs): ~2K tokens input, 500 tokens output → $0.01
- Description enhancement (500 products): ~250K tokens input, 100K tokens output → $2.25
- **Total per run: ~$2.26**
## Migration & Alternatives
### If switching from X to this stack:
- Keep frontend, rewrite backend in FastAPI
- Anthropic SDK available in both (use TS if preferred)
- Playwright works identically in Node/Python
- Extract business logic to pure Python functions
- Wrap in FastAPI routes
- Reuse SQLAlchemy models with SQLModel
- Move Polars data processing into modules
- Wrap LLM calls into functions
- Add FastAPI wrapper for web access
## Tech Decision Rationale Summary
| Decision | Why | Confidence |
|----------|-----|-----------|
| **FastAPI over Django/Flask** | Modern async, performance, type safety | HIGH |
| **Anthropic SDK over LangChain** | Simpler, more maintainable, no abstraction overhead | HIGH |
| **Polars over pandas** | 10-100x faster, modern API, better for new projects | HIGH |
| **Playwright over wkhtmltopdf** | Maintained, reliable, CSS support, industry standard | HIGH |
| **React over htmx** | Better for complex table editing (500+ rows) | MEDIUM |
| **uv over pip/poetry** | 10-100x faster, modern tooling | MEDIUM |
| **SQLite over PostgreSQL** | No server needed, simpler deployment, sufficient for single-user | HIGH |
## Sources & Verification
- Anthropic API documentation (official)
- FastAPI documentation (official)
- Polars documentation (official)
- Playwright documentation (official)
- uv adoption trajectory (released 2024, rapid growth)
- React still dominant but htmx gaining for simpler stacks
- LangChain criticism in production use (common feedback)
- ✅ Anthropic SDK version (0.18+ confirmed for structured outputs with instructor)
- ✅ Polars version (0.20+ has stable API)
- ✅ FastAPI version (0.110+ is stable as of early 2026)
- ⚠️ Exact Claude API pricing (estimate based on announced rates)
## Next Steps for Roadmap
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
