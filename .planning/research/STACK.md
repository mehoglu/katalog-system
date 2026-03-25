# Technology Stack

**Project:** Katalog — LLM-based Product Catalog System
**Researched:** 25. März 2026
**Overall Confidence:** HIGH (core stack), MEDIUM (some library choices)

## Executive Summary

Python-based stack with **FastAPI** backend, **Anthropic SDK (Claude)** for LLM agent orchestration, **Polars** for high-performance CSV processing (500+ products), and **Playwright** for production-quality HTML→PDF conversion. Frontend uses **React + Tailwind CSS** for modern UI with table editing. This stack prioritizes production readiness, maintainability, and performance for large-scale document generation.

---

## Recommended Stack

### 1. Core Backend Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.110+ | Web API & file upload handling | Modern async Python framework with automatic OpenAPI docs, excellent type hint support, high performance. Perfect for handling CSV/image uploads and serving generated catalogs. Much cleaner than Flask for async LLM calls. |
| Python | 3.11+ | Runtime | 3.11+ for performance improvements (10-60% faster than 3.10). Type hints are essential for this project. |
| **Uvicorn** | 0.27+ | ASGI server | Production-ready async server for FastAPI. Use with `--workers` for multi-process. |
| **Pydantic** | 2.6+ | Data validation & schemas | Built into FastAPI. Type-safe data models for CSV mappings, product data structures. V2 is 5-50x faster than v1. |

**Confidence:** HIGH — FastAPI is the standard for modern Python APIs in 2025/2026.

---

### 2. LLM Agent Orchestration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Anthropic SDK** | 0.18+ | Claude API for CSV analysis & text enhancement | Direct SDK approach. Claude 3.5 Sonnet excels at structured data analysis and German language tasks. Simpler than LangChain for this use case—you don't need complex chains, just smart prompts for CSV schema detection and description enhancement. |
| **Instructor** | 1.0+ | Structured LLM outputs | Type-safe structured outputs from Claude. Ensures CSV mapping analysis returns predictable JSON schemas. Wraps Anthropic SDK with Pydantic validation. |

**Why NOT LangChain/LlamaIndex:**
- LangChain: Over-engineered for this use case. Adds complexity without benefits. Direct SDK calls with good prompting are more maintainable.
- LlamaIndex: Designed for RAG (Retrieval-Augmented Generation). Overkill when you're processing CSVs directly, not searching document stores.

**Alternative consideration:** OpenAI SDK (GPT-4) if cost is critical, but Claude 3.5 Sonnet has better reasoning for schema analysis and German language quality.

**Confidence:** HIGH — Direct SDK approach is production best practice for 2025/2026.

---

### 3. Data Processing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Polars** | 0.20+ | CSV parsing & data transformation | 10-100x faster than pandas for large datasets (500+ products). Lazy evaluation, excellent memory efficiency. Better type system. Modern DataFrame library built in Rust. |
| **DuckDB** (optional) | 0.10+ | SQL queries on CSV if needed | In-process SQL engine. Can query CSVs directly with SQL if complex joins are needed. Works alongside Polars. |

**Why NOT pandas:**
- Slower for 500+ product catalogs
- Polars has better null handling (important for "missing data" requirement)
- Polars API is cleaner and more consistent
- pandas is still fine, but Polars is the modern choice for new projects

**Migration note:** If team is highly experienced with pandas, using pandas is acceptable—the performance difference won't be critical at 500 products. Switch to Polars at 5000+.

**Confidence:** HIGH — Polars is the recommended choice for new Python data projects in 2026.

---

### 4. HTML Generation & PDF Export

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Jinja2** | 3.1+ | HTML templating | De facto standard for Python HTML templates. Clean separation of logic and presentation. |
| **Playwright** | 1.42+ | HTML → PDF conversion | Headless Chromium for pixel-perfect PDF rendering. Handles CSS print media, complex layouts, web fonts. More reliable than wkhtmltopdf. Can screenshot for previews. |
| **WeasyPrint** (alternative) | 61+ | HTML → PDF (CSS Paged Media) | Pure Python alternative. Better for simple layouts. Supports CSS Paged Media spec. Use if you need full Python stack without Node.js dependency. |

**Recommendation:** Start with **Playwright** for production-quality PDFs. It's the industry standard for HTML→PDF in 2026.

**Why NOT:**
- wkhtmltopdf — Unmaintained since 2020, known rendering bugs
- pdfkit — Python wrapper for wkhtmltopdf, same issues
- ReportLab — Low-level PDF generation, no HTML input

**Confidence:** HIGH — Playwright is production standard for HTML→PDF.

---

### 5. Image Processing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pillow** | 10.2+ | Image resizing, optimization, format conversion | Standard Python image library. Handles JPEG/PNG/WebP. Good for resizing product images for web/print. |
| **blake3** (optional) | 0.4+ | Fast image hashing for deduplication | If you need to detect duplicate images across 500+ products. 10x faster than MD5/SHA. |

**Why NOT:**
- ImageMagick via subprocess — Pillow is sufficient and more Pythonic
- OpenCV — Overkill for simple image transformations

**Confidence:** HIGH — Pillow is the standard choice.

---

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

**Alternative:** **htmx + Alpine.js** if you want to avoid complex React state management. Renders HTML server-side, sprinkles JavaScript for interactivity. Simpler architecture, but less dynamic table editing.

**Confidence:** HIGH — React + TypeScript is standard for 2026 web UIs.

---

### 7. Database (Optional)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **SQLite** | 3.45+ | Persist CSV mappings & corrections | Serverless, zero-config. Perfect for single-user system. Stores learned CSV schema mappings, user corrections. |
| **SQLModel** | 0.0.16+ | ORM & validation | SQLAlchemy ORM with Pydantic models. Type-safe database operations. Integrates perfectly with FastAPI. |

**Alternative:** File-based JSON storage if database feels like overkill. But SQLite is recommended for queryability.

**Confidence:** HIGH — SQLite is perfect for this use case.

---

### 8. Deployment & Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Docker** | 24+ | Containerization | Single-user system can run as Docker Compose stack. Bundles Python backend + Node frontend + Playwright browser. |
| **Docker Compose** | 2.24+ | Multi-container orchestration | Simple deployment: `docker-compose up`. Handles FastAPI + React + Playwright dependencies. |

**Alternative:** No Docker if running locally only. Use `uv` or `poetry` for Python deps, `npm` for frontend.

**Confidence:** MEDIUM — Docker is optional but recommended for reproducibility.

---

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

---

## Installation Blueprint

### Backend (Python)

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install \
  fastapi[all]==0.110.0 \
  anthropic==0.18.1 \
  instructor==1.0.0 \
  polars==0.20.10 \
  jinja2==3.1.3 \
  playwright==1.42.0 \
  pillow==10.2.0 \
  sqlmodel==0.0.16 \
  python-multipart \
  uvicorn[standard]

# Install Playwright browsers
playwright install chromium
```

### Frontend (React)

```bash
# Create Vite + React + TypeScript project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install \
  @tanstack/react-table \
  react-hook-form \
  axios \
  tailwindcss \
  @tailwindcss/typography \
  postcss \
  autoprefixer

# Initialize Tailwind
npx tailwindcss init -p
```

### Full Stack with Docker

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./assets:/app/assets
      - ./bilder:/app/bilder
      - ./output:/app/output
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

## Dependency Management

### Python: Use `uv` (Recommended for 2026)

```bash
# Install uv (Rust-based pip replacement, 10-100x faster)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init
uv venv
source .venv/bin/activate

# Add dependencies
uv add fastapi anthropic instructor polars playwright pillow sqlmodel
uv add --dev pytest ruff mypy

# Lock dependencies
uv lock

# Install from lock
uv sync
```

**Why uv over pip/poetry/pipenv:** 
- 10-100x faster dependency resolution
- Compatible with pip/requirements.txt
- Rust-based, actively maintained by Astral (makers of Ruff)
- Industry momentum in 2025/2026

**Alternative:** `poetry` if you prefer more mature tooling. Avoid `pipenv` (slower, less maintained).

**Confidence:** HIGH — uv is gaining rapid adoption in 2026.

---

## Architecture Implications

### Agent Workflow Design

```python
# Recommended structure with Anthropic SDK + Instructor

from anthropic import Anthropic
from instructor import from_anthropic
from pydantic import BaseModel

client = from_anthropic(Anthropic())

class CSVSchema(BaseModel):
    """Type-safe CSV schema detection"""
    article_number_column: str
    price_columns: list[str]
    description_columns: list[str]
    
class EnhancedDescription(BaseModel):
    """Type-safe product description enhancement"""
    original: str
    enhanced: str
    confidence: float

# Schema detection agent
def detect_csv_schema(csv_content: str) -> CSVSchema:
    return client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        response_model=CSVSchema,
        messages=[{
            "role": "user",
            "content": f"Analyze this CSV and identify columns:\n{csv_content[:1000]}"
        }]
    )

# Text enhancement agent
def enhance_description(text: str) -> EnhancedDescription:
    return client.chat.completions.create(
        model="claude-3-5-sonnet-20240620",
        response_model=EnhancedDescription,
        messages=[{
            "role": "user",
            "content": f"Verbessere diese Produktbeschreibung für einen professionellen Katalog:\n{text}"
        }]
    )
```

**Why this approach:**
- No framework overhead
- Type-safe responses (Pydantic)
- Easy to test and debug
- Scales to more agents without complexity

---

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

**Optimization strategies for 500+ products:**
1. **Parallel LLM calls:** Use `asyncio.gather()` for description enhancements (rate limit: 10-20 concurrent)
2. **Lazy CSV loading:** Polars lazy API (`pl.scan_csv()`)
3. **Image caching:** Pre-process images once, reuse for re-generations
4. **PDF streaming:** Generate PDFs on-demand rather than all upfront

---

## Versioning Strategy

**Lock all dependencies** to avoid breaking changes:

```toml
# pyproject.toml (uv/poetry)
[project]
dependencies = [
  "fastapi==0.110.0",  # Pin major versions
  "anthropic~=0.18.0",  # Allow patch updates
  "polars~=0.20.0",
  # ...
]
```

**Rationale:** LLM SDKs change rapidly. Claude SDK breaking changes between 0.17 → 0.18. Pin to avoid surprises.

---

## Development vs Production

| Tool | Development | Production |
|------|-------------|------------|
| Python server | `uvicorn main:app --reload` | `uvicorn main:app --workers 4` |
| Frontend | `npm run dev` | `npm run build` + `npm run preview` |
| Database | SQLite file | SQLite file (same) |
| LLM model | Claude 3.5 Sonnet | Claude 3.5 Sonnet (same) |
| Logging | Console | Structured JSON + file |
| Error handling | Debug tracebacks | User-friendly messages |

**No separate staging needed:** Single-user system. Test locally before deploying.

---

## Cost Estimates (LLM API)

**Claude 3.5 Sonnet (Anthropic) pricing as of 2026:**
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens

**Per 500-product catalog run:**
- CSV schema analysis (2 CSVs): ~2K tokens input, 500 tokens output → $0.01
- Description enhancement (500 products): ~250K tokens input, 100K tokens output → $2.25
- **Total per run: ~$2.26**

**For smaller catalogs or less enhancement:** Could use Claude 3 Haiku ($0.25/$1.25 per 1M tokens) for descriptions → ~$0.15 per run.

**Confidence:** MEDIUM — Pricing estimates, actual may vary.

---

## Migration & Alternatives

### If switching from X to this stack:

**From Node.js/TypeScript backend:**
- Keep frontend, rewrite backend in FastAPI
- Anthropic SDK available in both (use TS if preferred)
- Playwright works identically in Node/Python

**From Django:**
- Extract business logic to pure Python functions
- Wrap in FastAPI routes
- Reuse SQLAlchemy models with SQLModel

**From Jupyter notebooks:**
- Move Polars data processing into modules
- Wrap LLM calls into functions
- Add FastAPI wrapper for web access

---

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

---

## Sources & Verification

**HIGH confidence sources:**
- Anthropic API documentation (official)
- FastAPI documentation (official)
- Polars documentation (official)
- Playwright documentation (official)

**MEDIUM confidence (training data, 2025/2026 ecosystem trends):**
- uv adoption trajectory (released 2024, rapid growth)
- React still dominant but htmx gaining for simpler stacks
- LangChain criticism in production use (common feedback)

**Verification needed:**
- ✅ Anthropic SDK version (0.18+ confirmed for structured outputs with instructor)
- ✅ Polars version (0.20+ has stable API)
- ✅ FastAPI version (0.110+ is stable as of early 2026)
- ⚠️ Exact Claude API pricing (estimate based on announced rates)

---

## Next Steps for Roadmap

**Recommended phase structure based on stack:**

1. **Phase 1: Core Backend Setup** — FastAPI skeleton, CSV upload, Polars parsing
2. **Phase 2: LLM Integration** — Anthropic SDK, CSV schema detection agent
3. **Phase 3: Data Merging** — Article number joins, conflict resolution
4. **Phase 4: Text Enhancement** — German description improvement agent
5. **Phase 5: HTML Generation** — Jinja templates, A4 layout
6. **Phase 6: PDF Export** — Playwright integration
7. **Phase 7: Frontend UI** — React + table editing for mappings
8. **Phase 8: Image Integration** — Pillow processing, catalog assembly
9. **Phase 9: Persistence** — SQLite for mappings, correction history

**Stack enables fast iteration:** FastAPI hot reload + Vite HMR = instant feedback loop.

---

*Last updated: 25. März 2026*
*Researcher: GSD Project Researcher Agent*
