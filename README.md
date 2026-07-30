# Contract Intelligence & Clause-Risk Platform

A backend platform for ingesting contracts (PDF/DOCX), building a searchable per-tenant knowledge base, and answering natural-language questions about contract clauses via a RAG pipeline — with an agentic risk reviewer, citation verification, and prompt-injection defense layered on top.

**Live demo:** https://contract-intel-platform.onrender.com/docs

> ⚠️ **Free-tier hosting note:** the API is deployed on Render's free tier, which spins down after 15 minutes of inactivity. The first request after idle time can take 30–60 seconds to respond while the instance wakes up — this is expected, not a bug.
>
> ⚠️ **Current deployment scope:** only the web API is deployed. Document processing (parsing, chunking, embedding) requires a background worker (Redis + RQ) and a vector store (Chroma), neither of which is deployed yet — uploads succeed and are stored, but `parse_status` will remain `pending` on the live demo until a worker is added. The RAG Q&A endpoint (`/ask`) is fully functional in local dev but requires processed documents and a `GROQ_API_KEY`, neither of which are configured in the current live deployment. This is a deliberate, documented scope boundary for the current phase, not an oversight (see [Known Limitations](#known-limitations)).

---

## Problem

Legal and procurement teams manually review contracts for risky clauses — unlimited liability, silent auto-renewal, unfavorable termination terms — a slow, error-prone process where missing one clause in a 40-page contract has real consequences.

## Solution

Documents are parsed, chunked, embedded, and indexed on upload. A RAG pipeline answers natural-language questions grounded in retrieved chunks with exact source citations. An agentic reviewer (ReAct-style loop) works through a risk checklist autonomously, producing a structured, citation-backed report — replacing hours of manual first-pass review with a defensible draft a human still signs off on.

*(Everything below reflects the current state: a fully functional traditional backend, plus the first two layers of the AI/RAG pipeline — local embedding generation with vector storage, and a working hybrid-retrieval grounded Q&A endpoint. Citation verification, the agentic reviewer, and prompt-injection hardening are the next phases.)*

---

## Architecture

![Architecture Diagram](docs/architecture-diagram.png)

**Ingestion flow (local dev):** Upload → save to disk → enqueue parse job (Redis/RQ) → worker parses (PyMuPDF/python-docx) → chunks (char-based, 1000/150 overlap) → stored in `chunks` table → on successful parse, a second job embeds each chunk (`BAAI/bge-small-en-v1.5`, local/CPU, no API cost) and writes the vectors to Chroma, tagged with tenant and version metadata for scoped retrieval.

**Grounded Q&A flow (`POST /documents/{id}/ask`):** Question in → BM25 full-text search (Postgres, `chunks.content_tsvector`) and vector similarity search (Chroma) run in parallel → results fused via Reciprocal Rank Fusion (no arbitrary score-weighting between incomparable scales) → top-5 fused chunk IDs resolved to real content through the tenant-scoped repository (Chroma is never trusted with content directly) → question + chunks sent to Groq (`openai/gpt-oss-120b`) with retrieved content explicitly delimited as untrusted data, forced into a schema-enforced structured JSON response → cited chunk_ids sanity-checked against the retrieved set before the answer is returned.

### Request Flow & Layering

![Request Flow Diagram](docs/request-flow-diagram.png)

`routers/` (HTTP, JWT validation, `org_id` resolution) → `services/` (business logic) → `repositories/` (tenant-scoped data access — every query filtered by `org_id`) → `models/` (SQLAlchemy ORM). See [decisions log](docs/project1-decisions-log.md) for why this structure was chosen over alternatives.

**Vector search follows the same tenant-isolation philosophy as Postgres, applied to a second data store:** Chroma's metadata filter narrows candidates for relevance and performance, but it is never trusted as the authorization boundary. Vector queries return chunk IDs only, never content — the actual content lookup still goes through the same tenant-scoped repository layer used everywhere else in the system, including in the B2 retrieval pipeline.

---

## Tech Stack

| Layer | Choice |
|---|---|
| API framework | FastAPI |
| Database | PostgreSQL 16 (Neon, hosted) |
| ORM / migrations | SQLAlchemy 2.0 + Alembic |
| Auth | JWT (access + refresh, bcrypt password hashing) |
| Async processing | Redis + RQ *(local dev only — not yet deployed)* |
| Document parsing | PyMuPDF (PDF), python-docx (DOCX) |
| Embeddings | `sentence-transformers` (`BAAI/bge-small-en-v1.5`, CPU, local — no API cost) |
| Vector store | Chroma (self-hosted, Docker) |
| Keyword search (RAG) | PostgreSQL full-text search (`ts_rank` / `tsvector`, GIN-indexed) |
| LLM (grounded Q&A) | Groq (`openai/gpt-oss-120b`), schema-enforced structured outputs |
| Retrieval fusion | Reciprocal Rank Fusion (RRF), combining vector + keyword search |
| Testing | pytest, real Postgres + real Chroma in integration tests |
| Containerization | Docker (multi-stage build) |
| Hosting | Render (API), Neon (database) |

---

## Key Engineering Decisions

Full reasoning, alternatives considered, and trade-offs for every decision below are in **[`docs/project1-decisions-log.md`](docs/project1-decisions-log.md)** — written specifically as interview-prep material, not just a changelog.

Highlights:
- **Tenant isolation** enforced at the repository layer — every query scoped by `org_id`, empirically verified with a cross-tenant access test (not just asserted). The same principle now extends to vector search: Chroma's metadata filter is treated as a performance optimization, not a security boundary — content lookups always resolve through the tenant-scoped repository, never directly from the vector store.
- **Idempotent ingestion** — re-uploading the same document doesn't duplicate chunks; verified by reprocessing an already-completed document and confirming deterministic, byte-identical output. Embedding generation carries the same guarantee.
- **Hybrid retrieval via Reciprocal Rank Fusion** — vector similarity and BM25 keyword search combined by fusing rank position rather than hand-weighting two incomparable score scales (cosine similarity vs. Postgres `ts_rank`), using the standard RRF constant rather than an invented, hard-to-defend weighting.
- **Structured, schema-enforced LLM citations** — the LLM's response is forced into a strict JSON schema (`answer` + `citations` with `chunk_id`/`quote`), not parsed out of free text, so citation verification can check facts programmatically instead of via regex. Every cited `chunk_id` is checked against the actual retrieved set before the response is ever returned — caught during manual testing that citation *quality* on negative answers (correctly saying "not found") is weaker than on positive ones, directly motivating the next phase's citation-verification work.
- **Org-wide content-hash deduplication** — catches the realistic failure mode (same file uploaded twice under different names) rather than narrower per-document dedup.
- **Soft-delete only** for documents — no hard-delete endpoint exists; a legal-tech audit trail should never silently lose evidence of a contract review. The same archived-document check gates the Q&A endpoint before any retrieval or LLM cost is spent.
- **Access + refresh JWT tokens, no rotation** — a deliberate scope call, not a shortcut: full rotation with reuse detection is the right answer for production systems with real attackers, but a complexity I chose not to build (and couldn't fully defend) for this project's actual threat model.
- **Local, open-source embeddings over a hosted API** — `bge-small-en-v1.5` runs entirely on CPU, no external API cost or network dependency for the embedding step. Paired with Groq (rather than a more generous free-tier provider) specifically because its tighter rate limits make the upcoming resilience work (backoff, circuit breaking, graceful degradation) a real necessity, not a theoretical exercise.

---

## Running Locally

**Prerequisites:** Python 3.12+, Docker Desktop (with WSL2 on Windows), Git, a free [Groq API key](https://console.groq.com) (required for the `/ask` endpoint).

```bash
# Clone and set up
git clone https://github.com/nithinknkr/contract-intel-platform.git
cd contract-intel-platform
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies (CPU-only torch first — avoids ~1.8GB of unused
# GPU/CUDA packages that sentence-transformers would otherwise pull in)
pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Start local Postgres, Redis, and Chroma (via docker-compose.yml)
docker compose up -d
# This starts three containers: contract-intel-postgres (port 5432),
# contract-intel-redis (port 6379), and contract-intel-chromadb (port 8001)

# Configure environment
cp .env.example .env
# edit .env with your local values, including GROQ_API_KEY

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a separate terminal, start the background worker
# (handles both document parsing/chunking and embedding generation)
python run_worker.py
```

API docs available at `http://localhost:8000/docs`.

**Run tests:**
```bash
pytest --cov=app --cov-report=term-missing
```

---

## Known Limitations

These are documented, deliberate scope boundaries — not undiscovered bugs. Each is logged in detail in the [decisions log](docs/project1-decisions-log.md).

- **No background worker or vector store deployed.** Uploads succeed and are stored on the live demo, but processing (parsing/chunking/embedding) requires a worker and Chroma instance that aren't deployed yet — `parse_status` stays `pending` on production. Fully functional in local dev.
- **`/ask` citation quality is weaker on negative answers.** When the correct answer is "this isn't covered in the document," the LLM's citations for that refusal are weaker (section-header fragments rather than genuine supporting text) than on positive, fact-grounded answers. The model does not fabricate content — this is a citation-quality gap, not a hallucination — and is the direct motivation for the next phase's citation-verification layer.
- **No OCR support.** Scanned/image-only PDFs fail cleanly with a documented reason rather than silently producing empty results.
- **No way to add a second user to an existing organization via the API** — signup always creates a new org. A known, named gap, not yet resolved (see decisions log).
- **No document re-versioning endpoint yet.** The schema and vector-store cleanup logic both support it, but the API path to upload a new version of an existing document doesn't exist yet — a named, deliberately deferred gap rather than a retrofit built just to exercise unused code.
- **CI/CD pipeline not yet set up.** Started, deliberately paused — tests are run and verified manually before each phase.

---

## Roadmap

- **Phase A** (traditional backend) — ✅ complete: ingestion, multi-tenant auth, search, testing, deployment
- **Phase B** (AI/RAG layer) — in progress
  - ✅ **B1** — Embeddings & vector store: local CPU embedding generation, Chroma integration, tenant-isolated vector search
  - ✅ **B2** — RAG retrieval & grounded Q&A endpoint: hybrid search (BM25 + vector, fused via RRF), Groq LLM with schema-enforced structured citations
  - B3 — Citation verification layer
  - B4 — Agentic clause-risk reviewer
  - B5 — Prompt injection defense
  - B6 — RAG/agent evaluation harness
  - B7 — Cost & rate-limit resilience
- Background worker deployment
- CI/CD pipeline (GitHub Actions)
- Frontend (deferred until Phase A + B are both complete)

---

## Project Structure

```
app/
├── core/          # config, security, dependencies
├── db/            # session, base
├── models/        # SQLAlchemy models
├── repositories/  # tenant-scoped data access layer
├── routers/       # HTTP endpoints
├── schemas/       # Pydantic request/response models
└── services/      # business logic (parsing, chunking, ingestion, embedding,
                    # vector store, hybrid retrieval, LLM integration, queue)
alembic/           # database migrations
tests/             # unit + integration tests
docs/              # decisions log
run_worker.py      # background worker entrypoint (parsing + embedding jobs)
```