# Decisions Log — Contract Intelligence & Clause-Risk Platform

This log records the key architectural and technical decisions made during the project. Each entry captures the alternatives considered, the rationale behind the chosen approach, and the trade-offs accepted. The goal is to document not just *what* was done, but *why* it was done.

---

## WSL2 Development Environment
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Native Windows development vs WSL2 (Ubuntu)

**Chosen:** WSL2 (Ubuntu)

**Why:** Linux closely matches production environments and integrates seamlessly with Docker and Python tooling.

**Trade-off accepted:** Slightly longer initial setup compared to native Windows.

**Interview angle:** *"I chose WSL2 because it provides a Linux environment similar to production while still allowing me to work comfortably on Windows."*

---

## Docker Backend
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Hyper-V backend vs WSL2 backend

**Chosen:** Docker Desktop with WSL2 backend

**Why:** WSL2 offers better performance, lower resource usage, and tighter integration with Ubuntu.

**Trade-off accepted:** Requires WSL2 to be configured before Docker.

**Interview angle:** *"I used Docker's WSL2 backend because it's the recommended setup for modern Windows-based development."*

---

## Project Architecture
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Microservices vs Modular Monolith

**Chosen:** Modular Monolith

**Why:** It keeps the application simple while maintaining separation of concerns through a layered architecture.

**Trade-off accepted:** Individual modules cannot be deployed independently.

**Interview angle:** *"Since this is a single-developer project, a modular monolith gives me clean separation without the operational overhead of microservices."*

---

## Folder Structure
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Flat project structure vs Layered architecture

**Chosen:** Layered architecture (`routers`, `services`, `models`, `schemas`, `db`, `core`)

**Why:** Separating HTTP handling, business logic, and database code improves maintainability and scalability.

**Trade-off accepted:** More folders and boilerplate during the initial setup.

**Interview angle:** *"I separated responsibilities into layers so each part of the application has a single responsibility and is easier to maintain."*

---

## Python Dependency Management
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Global Python packages vs Virtual Environment (`venv`)

**Chosen:** Python Virtual Environment (`venv`)

**Why:** Keeps project dependencies isolated from the system Python installation.

**Trade-off accepted:** The virtual environment must be activated for each development session.

**Interview angle:** *"Using a virtual environment prevents dependency conflicts between different Python projects."*

---

## Database Selection
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** SQLite vs MySQL vs PostgreSQL

**Chosen:** PostgreSQL 16

**Why:** PostgreSQL is production-ready, highly reliable, and integrates well with FastAPI and SQLAlchemy.

**Trade-off accepted:** More setup effort compared to SQLite.

**Interview angle:** *"I chose PostgreSQL because it's the database I would realistically use in a production backend."*

---

## Database Deployment
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Local PostgreSQL installation vs Docker container

**Chosen:** Dockerized PostgreSQL

**Why:** Docker provides a consistent, reproducible database environment across machines.

**Trade-off accepted:** Docker Desktop must be running before using the database.

**Interview angle:** *"Running PostgreSQL in Docker ensures the same environment can be recreated easily on any machine."*

---

## Configuration Management
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Hardcoded configuration vs Environment variables (`.env`)

**Chosen:** Environment variables

**Why:** Keeps secrets out of source control while making configuration easy to change between environments.

**Trade-off accepted:** Requires managing additional configuration files.

**Interview angle:** *"I externalized configuration so secrets remain secure and deployments can be configured without modifying the code."*

---

## Git Authentication
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** HTTPS with Personal Access Token vs SSH

**Chosen:** SSH Authentication

**Why:** SSH provides secure, password-free authentication after a one-time setup.

**Trade-off accepted:** Initial SSH key generation and GitHub configuration.

**Interview angle:** *"I chose SSH because it's the standard workflow for developers and avoids repeatedly managing access tokens."*

---

## Version Control Strategy
**Phase:** A1  
**Date:** 20-07-2026

**Options considered:** Push after development vs Push from project initialization

**Chosen:** Version control from the beginning

**Why:** Establishes a clean commit history and provides immediate backup on GitHub.

**Trade-off accepted:** Early commits mainly contain project scaffolding.

**Interview angle:** *"I initialized Git from the start so every meaningful change is tracked and backed up from day one."*


# Phase A2 Decisions

---

## Tenant Isolation Strategy
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** PostgreSQL Row-Level Security (RLS) vs Strict application-layer tenant filtering

**Chosen:** Strict application-layer tenant filtering using the Repository Pattern

**Why:** Simpler to implement with FastAPI, SQLAlchemy, async sessions, and connection pooling while still providing strong tenant isolation when every database query is routed through tenant-aware repositories.

**Trade-off accepted:** Security enforcement depends on application code discipline rather than the database itself. Every repository method must explicitly filter by `organization_id`, and direct database queries outside the repository layer are prohibited.

**Interview angle:** *"I chose strict application-layer tenant isolation because it integrates well with FastAPI and SQLAlchemy, avoids the operational complexity of RLS with async connection pooling, and still provides strong isolation through a centralized repository layer."*

---

## Primary Key Strategy
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** BIGINT auto-increment IDs vs UUID v4 for all tables vs Mixed strategy (UUID for public entities and BIGINT for internal tables)

**Chosen:** UUID v4 for all tables

**Why:** UUIDs provide globally unique, non-sequential identifiers that are difficult to guess, improving security in a multi-tenant application while maintaining a single, consistent identifier strategy across the entire system.

**Trade-off accepted:** UUIDs consume more storage and produce slightly larger indexes than BIGINTs, but the overhead is negligible for this project's scale.

**Interview angle:** *"I standardized on UUIDs across all entities because they prevent predictable ID enumeration, strengthen the multi-tenant security model, and keep the data model consistent."*

---

## User-to-Organization Relationship
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** Single organization per user vs Multi-organization membership through a junction table

**Chosen:** Single organization per user

**Why:** It satisfies the current project requirements while keeping authentication, authorization, and tenant resolution simple. The schema remains extensible if multi-organization membership is required in the future.

**Trade-off accepted:** Users cannot belong to multiple organizations without introducing an additional membership table in a future version.

**Interview angle:** *"I intentionally started with a single-organization user model because it covers the current requirements with minimal complexity while leaving a clear migration path to multi-organization memberships later."*

---

## User Roles & Authorization Model
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** Two-role model (`admin`, `member`) vs finer-grained roles (`admin`, `reviewer`, `viewer`)

**Chosen:** Finer-grained roles via Postgres enum (`user_role`: `admin`, `reviewer`, `viewer`), stored on `users.role`, defaulting to `viewer`

**Why:** Legal-tech context makes coarse permissions inadequate — not everyone who can view a contract should be able to approve a risk review or delete a document. A least-privilege default (`viewer`) means a new user row is safe by default; elevated access is an explicit choice in application logic, not a default.

**Trade-off accepted:** The roles are modeled now but not yet enforced anywhere — actual authorization checks (e.g. only `admin`/`reviewer` can delete a document) are deferred to A4. Also accepted more schema complexity up front for a distinction that only matters once real endpoints exist.

**Interview angle:** *"I modeled least-privilege roles at the schema level from the start, so authorization checks in the API layer have real role data to check against instead of retrofitting permissions later."*

---

## SQLAlchemy Enum Value Mapping
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** Default SQLAlchemy `Enum` behavior (stores Python enum *member name*) vs explicit `values_callable` (stores enum *value*)

**Chosen:** Explicit `values_callable=lambda x: [e.value for e in x]` on the `role` column

**Why:** `UserRole` is a `str` subclass with lowercase values (`"admin"`, `"reviewer"`, `"viewer"`). Without `values_callable`, SQLAlchemy's default behavior stores the uppercase member *name* (`ADMIN`) in Postgres, silently mismatching what the Python/Pydantic layer expects to serialize and compare against.

**Trade-off accepted:** One more non-obvious SQLAlchemy detail to remember on every future enum column in this project — not a one-time fix, a pattern to repeat.

**Interview angle:** *"I caught a mismatch between how SQLAlchemy stores Python enums by default and how my API layer would actually serialize them, before it became a runtime bug — the DB would have silently stored 'ADMIN' while my Pydantic schemas expected 'admin'."*

---

## Foreign Key Delete Behavior
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** Leave FK `ondelete` unset (Postgres default `NO ACTION`) vs explicit `ondelete='RESTRICT'` vs `CASCADE`

**Chosen:** Explicit `ondelete='RESTRICT'` on `users.org_id → organizations.id`

**Why:** Deleting an organization must never silently cascade-delete its users. Making the behavior explicit (even though it matches Postgres's default) turns an accidental omission into a documented decision — organization deactivation should go through an application-level soft-delete flag, not a hard `DELETE`.

**Trade-off accepted:** None functionally (matches default behavior) — the cost here was purely reviewing autogenerated migrations carefully instead of trusting them blindly.

**Interview angle:** *"I made delete behavior explicit rather than relying on the database default, because 'it happens to match the default today' isn't the same as 'this is guaranteed and documented.'"*

## Document Status: Document-Level vs Version-Level
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** Single status field on `documents` only vs split status across `documents` (lifecycle) and `document_versions` (per-upload processing)

**Chosen:** Split — `documents.status` (uploaded/processing/ready/failed) answers "can a user interact with this document," `document_versions.parse_status` answers "did this specific upload process correctly." `documents.is_archived` is a separate boolean, independent of processing state.

**Why:** A failed re-upload (e.g. amended contract v2 fails OCR) shouldn't make a document with a working v1 disappear from the user's view. Version history absorbs processing failures; document identity reflects whether there's at least one usable version.

**Trade-off accepted:** Two status fields to keep in sync conceptually (not literally — they track different things), and application logic needs a rule for how a version's `parse_status` rolls up into the document's `status` on first upload.

**Interview angle:** *"I separated document identity from upload processing state so a failed re-upload doesn't take down access to a document that already has a working prior version."*  

## Current-Version Tracking via Partial Unique Index
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** (A) No flag — "current" = MAX(version_number) per document, computed on every query. (B) Explicit `is_current` boolean, enforced only by application logic. (C) Explicit `is_current` boolean, enforced by a Postgres partial unique index (`UNIQUE(document_id) WHERE is_current`).

**Chosen:** C — partial unique index

**Why:** Retrieving "the current version" is the most frequent query in the whole system (every RAG query in Phase B needs it) — a flag makes that an indexed O(1) lookup instead of a subquery/order-by every time. But a bare boolean flag (option B) can drift out of sync if application logic ever fails to atomically unset the old current version before setting the new one — a partial unique index makes that structurally impossible at the database level, not just a convention the code has to get right.

**Trade-off accepted:** Slightly more complex migration/index syntax, and every version-creation flow must explicitly flip `is_current` in a transaction (insert new version with `is_current=True`, update old one to `False`) — if that transaction isn't atomic, the insert will simply fail against the constraint rather than silently corrupting state, which is the point.

**Interview angle:** *"I used a Postgres partial unique index instead of just trusting application code to maintain the 'current version' invariant — so even a bug in my upload logic can't produce two current versions of the same document, it'll just fail the constraint loudly instead of corrupting data silently."*

## Manual Tenant Isolation Verification
**Phase:** A2  
**Date:** 20-07-2026

**What was done:** Wrote a standalone script creating two organizations, one user per org, and a document belonging to org B. Verified `DocumentRepository.get_by_id(org_id=org_a.id, record_id=doc_b.id)` returns `None` (not an error, not the document — a clean "not found," indistinguishable from the document simply not existing), while the same lookup scoped to org_b.id correctly returns the document. All test data rolled back, never committed.

**Why this matters:** This is the first empirical proof — not just schema design — that the tenant isolation mechanism actually works. The repository's `get_by_id` filters by `org_id` AND `id` in a single SQL WHERE clause, so a cross-tenant lookup fails at the query level, not via an application-level ownership check after the fact (which would leak existence via timing/logic even if it blocked the data itself).

**Trade-off accepted:** This is a manual, one-off script — not part of an automated suite yet. A5 needs to formalize this exact scenario (two tenants, cross-access attempt) as a real pytest case that runs on every CI push, so a future regression can't silently reintroduce a leak.

**Interview angle:** *"Before building anything on top of my isolation layer, I wrote a script that creates two tenants and proves, empirically, that one tenant's repository calls cannot return another tenant's data — not by checking ownership after fetching, but by scoping the SQL query itself. That's the specific test I'd walk through in an interview to demonstrate the isolation is real, not just asserted."*


## Audit Log Design: Free-Text Action, Nullable Actor, Narrow Repository
**Phase:** A2  
**Date:** 20-07-2026

**Options considered:** Enum `action` field (matching the pattern used for `document_status`/`parse_status`) vs free-text indexed string. Also: standard `TenantScopedRepository` (full CRUD) vs a narrower purpose-built repository.

**Chosen:** Free-text `action` string (indexed, app-level `resource.verb` naming convention, e.g. `document.uploaded`), `user_id` FK with `ON DELETE SET NULL` (the only non-RESTRICT/CASCADE FK in the schema), and a standalone `AuditLogRepository` with only `create`/`list_for_org`/`list_for_resource` — no `get_by_id`, no `delete`, no `update`.

**Why:** `action` is an open-ended, growing set (more values arrive in Phase B — risk review completions, citation verification failures) — an enum would require a migration for every new event type, real friction for something meant to be cheap to extend, unlike `document_status`, which is a genuinely closed state machine. `user_id` uses `SET NULL` because an audit trail must outlive the actor: deleting a user account should neither be blocked by their audit history (`RESTRICT`) nor silently erase that history (`CASCADE`) — the log entry persists with a null actor, which is itself a meaningful fact. The repository excludes mutation methods because audit rows are append-only by design; exposing `delete`/update-via-get-by-id on this table would be a schema-level guarantee (append-only) undermined by an API-level capability that shouldn't exist.

**Trade-off accepted:** No DB-level guarantee that `action` values follow the naming convention — that discipline is enforced by code review / a constants file, not the schema. A determined bug could still write a malformed action string; that's accepted as reasonable given the extensibility win.

**Interview angle:** *"I broke my own enum pattern deliberately for the audit log's action field — enums are right for closed state machines like document status, wrong for an open-ended, growing event vocabulary. And the audit log is the one table where I used SET NULL instead of RESTRICT, because an audit trail's job is to outlive the thing it's auditing."*


Phase A3 Decisions
PDF/DOCX Parsing Library & OCR Deferral

Phase: A3
Date: 21-07-2026

Options considered: PyMuPDF vs pdfplumber for PDF parsing; implement real OCR now vs. defer

Chosen: PyMuPDF (fitz) + python-docx; OCR deferred — scanned/empty-text pages fail cleanly with a documented reason instead of silently degrading

Why: PyMuPDF has no external system dependency (unlike Tesseract, which requires an apt package baked into the Docker image) and reliably detects zero-text pages, which is exactly the signal needed to decide "this document needs OCR." Real OCR tuning (DPI, page segmentation modes, output quality) is a distraction from A3's actual goal — proving the pipeline mechanics work, not text-extraction quality.

Trade-off accepted: Scanned/image-only contracts are currently unsupported and fail the whole version rather than being processed via OCR — explicitly documented as future work, not silently ignored.

Interview angle: "I chose PyMuPDF because it has no system-level dependency and gives me a reliable signal for detecting scanned pages — I deliberately deferred OCR itself, since baking Tesseract into the Docker image and tuning its output quality is a separate, self-contained unit of work I didn't want blocking the core ingestion pipeline."

Chunking Strategy: Char-Based Splitting, 1000/150 Parameters

Phase: A3
Date: 21-07-2026

Options considered: Char-based splitting now vs. token-based splitting tied to an embedding model not yet chosen (B1)

Chosen: Char-based splitting (paragraph → sentence → hard-cut fallback), 1000-character chunks with 150-character overlap

Why: Token-based chunking is premature without a locked embedding model — different models tokenize differently, so "optimizing" chunk size in tokens now would measure against a ruler that doesn't exist yet. Char-based chunking is model-agnostic and sufficient to unblock A3.

Trade-off accepted: 1000/150 is an unvalidated starting point, explicitly flagged to be revisited against real retrieval quality once B1 (embeddings) and B6 (eval harness) exist.

Interview angle: "I used character-based chunking instead of token-based because I hadn't locked in an embedding model yet — tokenizing against a model I haven't chosen would be premature optimization. The 1000/150 parameters are a documented starting point, not a final answer."

chunks Table Stores Full Text (Resolving Spec Ambiguity)

Phase: A3
Date: 21-07-2026

Options considered: chunks as metadata-only per the original spec wording vs. storing full chunk text directly

Chosen: chunks.content stores full chunk text now; the future vector store (B1) will hold only embeddings keyed to chunk.id, never duplicating text

Why: B2's hybrid retrieval needs BM25 over actual chunk text, and no vector store exists yet in A3 — chunk text has to live somewhere queryable regardless of what the eventual vector store holds.

Trade-off accepted: None material — this resolves an ambiguity in the original spec rather than introducing a new one.

Interview angle: "My original spec said chunks should be metadata-only, but that only applies to the embedding vector — the chunk text itself has to live in Postgres so hybrid search can run BM25 against it later, independent of whatever vector store I add in B1."

Idempotency Mechanism: Org-Wide Hash-Based Dedup (Not True Resumability)

Phase: A3
Date: 21-07-2026

Options considered: (a) Content-hash dedup at upload time vs. (b) true crash-resumability (skip already-processed chunks on retry); dedup scope — org-wide vs. scoped to a single document

Chosen: Content-hash dedup (8a) only — a retry redoes the full parse+chunk work, it does not skip anything already processed. Dedup scope is org-wide: file_hash is checked against all documents in the organization, not just the one being uploaded to.

Why: Org-wide dedup catches the realistic failure mode — a user uploading the same NDA twice under two different filenames — which document-scoped dedup would miss entirely. True resumability (skipping already-processed chunks mid-crash) was judged disproportionate effort for A3's actual goal.

Trade-off accepted: Two genuinely different contracts that happen to be byte-identical (e.g., a shared template used across two different clients) would incorrectly collide under org-wide dedup — accepted as a rare, low-stakes edge case, worth relaxing to per-document scope if it ever mattered in practice.

Interview angle: "I chose org-wide dedup over per-document dedup because the actual mistake I wanted to prevent was someone uploading the same file twice under different names — not just re-submitting to one specific document's upload flow. I explicitly did not build true crash-resumability; a retry just redoes the work safely, it doesn't try to pick up mid-chunk."

CASCADE Delete on chunks.document_version_id

Phase: A3
Date: 21-07-2026

Options considered: RESTRICT (the A2 default pattern used elsewhere in the schema) vs. CASCADE

Chosen: CASCADE

Why: Chunks have no independent existence apart from their parent document version — deleting a version should always take its chunks with it. This is a deliberate, justified deviation from the RESTRICT-by-default convention set in A2, not an oversight.

Trade-off accepted: None material — CASCADE here doesn't risk unexpected data loss, since chunks are purely derived data.

Interview angle: "Most of my foreign keys default to RESTRICT to prevent silent data loss, but I made an explicit exception for chunks — they're derived data with no meaning outside their parent version, so cascading delete is the correct behavior, not a gap."

document_versions.file_hash + chunks.char_start/char_end Addition

Phase: A3
Date: 21-07-2026

Options considered: Add these columns now vs. defer until B1 (embeddings) / B3 (citation verification) actually need them

Chosen: Add now; file_hash indexed but not unique at the DB level

Why: char_start/char_end require re-parsing every existing document to backfill if added later — cheap now, expensive retroactively. file_hash was deliberately not made a unique DB constraint, because the same contract template can legitimately be uploaded across different documents/tenants; dedup correctness belongs in the service layer, where a clean 409 can be returned, not as a blind constraint that would throw an ugly IntegrityError on a legitimate case.

Trade-off accepted: Dedup correctness now depends on application code checking the hash before insert, not the database enforcing it.

Interview angle: "I added citation-grounding offsets before I needed them in B3, because retrofitting them would mean re-parsing every document already ingested. I deliberately kept the file-hash column non-unique at the DB level, since uniqueness there would incorrectly block a legitimate case — the same template uploaded for two different clients."

chunks.org_id Denormalization

Phase: A3 (originated in A2's chunks migration, formally logged during A3)
Date: 21-07-2026

Options considered: Denormalized org_id directly on chunks vs. always joining through document_versions → documents for tenant scoping

Chosen: Denormalized, with its own RESTRICT FK to organizations

Why: Matches TenantScopedRepository's assumption that every model has a direct org_id column — keeps chunk queries a single-table WHERE org_id = ... instead of a join, which matters once B2's retrieval queries are running per-request at volume.

Trade-off accepted: org_id is now redundant data that must stay consistent with document_versions.org_id/documents.org_id — nothing in the schema currently enforces that the three agree. Accepted as a low-risk integrity concern since it's set once at insert and never updated afterward.

Interview angle: "I denormalized org_id onto the chunks table itself rather than requiring a join every time, since tenant-scoped chunk queries are going to be the hottest path once RAG retrieval is live in Phase B. I accepted the redundant-data risk because it's write-once, never-updated data — low actual drift risk for a real performance win."

Save-File-Then-Commit-DB Ordering (No Compensating Cleanup)

Phase: A3
Date: 21-07-2026

Options considered: Commit DB then save file vs. save file then commit DB; add compensating cleanup on failure vs. accept the residual risk

Chosen: Save file to disk first, then commit the DB row; no automated cleanup on commit failure

Why: This ordering avoids the worse failure mode — a DB row pointing at a file that was never actually written, which would break parsing with a confusing error. The remaining failure mode (DB commit fails after a successful disk write) leaves an orphaned file with no DB row — inert, harmless, and cleanable later with a simple reconciliation script.

Trade-off accepted: A rare DB-commit failure after a successful disk write leaves a harmless orphaned file; no automated cleanup exists yet.

Interview angle: "I deliberately ordered the file save before the DB commit, because the alternative failure mode — a database row pointing at a file that doesn't exist — actively breaks the parsing step downstream. The failure mode I accepted instead is just a harmless orphaned file, which costs disk space but nothing else."

Partial-Empty-Pages Parsing Policy

Phase: A3
Date: 21-07-2026

Options considered: Silently accept partial text (ship what parsed, ignore what didn't) vs. fail the entire version if any page fails to extract, not just if all pages fail

Chosen: Fail the whole version on any single empty page, not only the all-empty case

Why: In a legal-tech product, "page 12 wasn't reviewed" is a worse failure mode than "this document needs reprocessing" — silent partial coverage is the more dangerous default for this specific domain, where a missed clause has real consequences.

Trade-off accepted: A document with one bad scanned page (e.g., a signature page) fails entirely, even though the other 39 pages parsed fine — accepted until OCR is implemented.

Interview angle: "I made a deliberate domain-specific call here: for most products, shipping partial results is fine, but for a contract-review tool, silently skipping one unreadable page is a worse failure than refusing the whole document. I'd rather force a clear reprocessing signal than risk a user trusting an incomplete review."

Bug: Corrupt/Invalid PDF Uploads Caused Unhandled 500s

Phase: A3
Date: 21-07-2026

What was found: Uploading a malformed/non-PDF file caused pymupdf.FileDataError to propagate as an unhandled exception → HTTP 500, even though the underlying DB-level failure handling had already correctly recorded parse_status=failed — the symptom (500 response) didn't match the actual state (a properly recorded, expected failure).

Fix: Wrapped fitz.open() (and docx.Document() for DOCX) in a try/except, converting the library-level exception into the existing ParseError type (corrupt_or_invalid_pdf / corrupt_or_invalid_docx) — treating "can't even open this file" as an expected outcome, the same category as scanned_pdf_no_text_layer, rather than an unhandled crash.

Why this matters: A user uploading a corrupted or wrong-type file is completely ordinary behavior, not an edge case — the system should respond with a clean, recorded failure state, not a 500.

Interview angle: "During testing I found that a corrupt PDF crashed the request with a 500, even though my failure-handling logic had already correctly written 'failed' to the database underneath — the exception just wasn't being caught at the right layer. I fixed it by converting the library's own exception into my existing ParseError type, so a bad upload is treated as an expected outcome instead of an unhandled crash."

Bug: Model Registration / NoReferencedTableError (Two Attempts)

Phase: A3
Date: 21-07-2026

What was found: NoReferencedTableError on any code path involving cross-model foreign keys (e.g., documents.uploaded_by → users.id) — SQLAlchemy only registers a model's table in Base.metadata once that model class has actually been imported somewhere. This worked in Alembic (whose env.py explicitly imports every model) and in the manual isolation script, but broke the first time a new entrypoint (the upload endpoint, later a standalone test script) touched multiple related tables without importing all of them first.

First attempted fix (rejected): Centralizing model imports inside app/db/base.py itself — this created a circular import, since every model file imports Base from that same file.

Final fix: Created app/models/__init__.py importing every model; any entrypoint (FastAPI, Alembic, standalone scripts, the RQ worker) now gets full registration via a single import app.models line, rather than each entrypoint needing to independently remember its own full import list.

Why this matters: The first fix was locally correct but not general enough — a genuine two-attempt debugging story, not a first-try success, and a real, transferable SQLAlchemy pattern (a single source of truth for "all models" import).

Interview angle: "I hit the same SQLAlchemy foreign-key resolution bug twice from two different entrypoints, and my first fix actually introduced a circular import. The correct fix was centralizing all model imports in one place — app/models/init.py — that every part of the system, including a future background worker, can rely on without needing to know about each other's import requirements."

Step 6 Retry-Safety — Empirically Verified

Phase: A3
Date: 21-07-2026

What was done: Ran process_document_version a second time on an already-processed document version via a standalone script. Verified: chunk count unchanged (4 → 4), all chunk IDs were entirely new (proving the delete-then-recreate transaction actually ran, not a silent no-op), chunk content and offsets were byte-identical to the first pass (proving determinism), and parse_status remained correctly parsed after the second pass.

Why this matters: This is the literal mechanism A3's stated idempotency goal ("re-uploading/reprocessing doesn't duplicate chunks") was built around — worth being able to say "I tested this specific scenario" rather than "the logic should handle it."

Trade-off accepted: This tests retry-safety (a retry is always safe to re-run), not true resumability (a retry does not skip already-completed work) — consistent with the idempotency-mechanism decision above.

Interview angle: "I didn't just implement the delete-then-recreate logic and assume it worked — I wrote a script that reprocesses an already-completed document version and checks three things: the chunk count doesn't change, the old chunk IDs are gone and replaced with new ones (proving the delete actually happened), and the content is byte-for-byte identical, proving the whole operation is deterministic."

RQ/Redis Async Processing — No Retry Policy Configured

Phase: A3
Date: 21-07-2026

Options considered: Configure automatic RQ retries (e.g., Retry(max=3)) for job failures vs. no retries

Chosen: No retries for now

Why: Every failure observed during testing has been deterministic (bad file content) — retrying a deterministic failure just fails the same way repeatedly, wasting worker time without fixing anything. Retries would matter for genuinely transient failures (e.g., a momentary DB connection blip), none of which have been observed yet.

Trade-off accepted: A named queue (document_processing) was used instead of RQ's default queue, anticipating future job types (e.g., embeddings in B1) that may want dedicated workers or prioritization — a cheap decision to make now, annoying to retrofit later. Also newly verified and worth logging as an operational fact: a document uploaded while no worker is running sits at pending indefinitely — confirmed by explicitly stopping the worker, uploading, confirming the job sat queued in Redis, then restarting the worker and confirming it was picked up and processed correctly.

Interview angle: "I deliberately left RQ retries off for now, because every failure I've hit so far has been deterministic — retrying a bad file three times just wastes worker time. I did verify the queue's actual value, though: I stopped the worker, uploaded a document, confirmed it sat safely in Redis at 'pending' status, then restarted the worker and watched it pick the job up and complete it — proving uploads and processing are genuinely decoupled now."

Status Endpoint — No org_id Scoping Yet (Deferred to A4)

Phase: A3
Date: 21-07-2026

What was done: GET /documents/{document_id}/versions/{version_id} filters by both document_id and version_id together (so a mismatched pair correctly 404s, rather than returning the wrong document's version) — but does not filter by org_id.

Why deferred: Same reason as the upload endpoint's existing auth TODOs — there's no way to know "the authenticated caller's org" until real auth exists in A4.

Trade-off accepted: Right now, any caller who knows or guesses a version UUID can poll any organization's document status — a real, explicitly named tenant-isolation gap, not silently shipped. Flagged with a code comment (# TODO: also filter by org_id once auth exists) directly at the query site.

Interview angle: "This endpoint has a known, deliberately deferred tenant-isolation gap — it doesn't yet check that the caller's org matches the version's org, because there's no authenticated caller identity to check against until A4. I named this explicitly rather than let it sit as an invisible gap, and left a TODO directly at the query site so it can't be missed when auth lands."


# Phase A4 Decisions

---

## Password Hashing Library
**Phase:** A4
**Date:** 22-07-2026

**Options considered:** passlib[bcrypt] (the conventional FastAPI-tutorial default) vs the `bcrypt` package directly

**Chosen:** `bcrypt` directly, no passlib

**Why:** passlib's bcrypt backend reads a `bcrypt.__about__.__version__` attribute that bcrypt removed in 4.1+, breaking passlib's version detection; passlib itself hasn't shipped a fix since 2020 and is effectively unmaintained. Calling `bcrypt.hashpw`/`bcrypt.checkpw` directly removes a fragile, unnecessary abstraction layer for a two-function need.

**Trade-off accepted:** Lose passlib's multi-algorithm abstraction (easy migration between hash schemes) — not a real cost here, since there's no plan to support multiple password hash algorithms simultaneously.

**Interview angle:** *"I skipped passlib and called bcrypt directly, because passlib's bcrypt backend is actually broken against bcrypt 4.1 and later — it reads a version attribute bcrypt removed, and passlib hasn't been updated to fix it. That's one less unmaintained dependency for two functions I can call directly."*

---

## Token Strategy: Access + Refresh, No Rotation
**Phase:** A4
**Date:** 22-07-2026

**Options considered:** (a) Access token only, short-lived, re-login on expiry. (b) Access + refresh pair, refresh token rotated on every use with reuse detection. (c) Access + refresh pair, refresh token NOT rotated — same token valid until natural expiry or explicit logout.

**Chosen:** (c) — 30-minute access token (stateless JWT), 14-day refresh token (opaque, DB-backed, revocable via `revoked_at`)

**Why:** Access-only forces re-login every 30 minutes, a real usability cost with no corresponding security benefit for this project's threat model. Full rotation + reuse detection (b) is a genuine defense-in-depth technique for production systems with real attackers, but disproportionate complexity for a solo portfolio project — the added code (tracking token families, detecting reuse, revoking on detected reuse) isn't something I could defend in depth if asked "walk me through why you needed this," versus the simpler revocable-refresh-token design, which I can.

**Trade-off accepted:** A stolen refresh token remains valid for up to 14 days if not proactively revoked (no reuse detection to catch an attacker using it alongside the legitimate user). Accepted given the threat model of a portfolio project versus a production system with real user data at stake.

**Interview angle:** *"I built access+refresh, not rotation. Rotation with reuse detection is the right answer for production, but I made a deliberate scope call not to build it here, because I couldn't defend the complexity for this project's actual threat model — I'd rather show a simpler design I fully understand than a fancier one I copied without being able to explain the trade-off."*

---

## Refresh Token Hashing: SHA-256, Not Bcrypt
**Phase:** A4
**Date:** 22-07-2026

**Options considered:** Bcrypt (same as password hashing, for consistency) vs SHA-256

**Chosen:** SHA-256

**Why:** These are two different problems. Passwords are low-entropy, human-chosen secrets that need a deliberately slow, salted hash to resist brute-force — that's bcrypt's job. A refresh token is 512 bits of `secrets.token_urlsafe`-backed entropy — there's nothing to brute-force. More importantly, bcrypt's per-hash salt makes it *unsuitable* here: `/auth/refresh` needs an exact-match lookup by hash in a single indexed query, and a salted hash can't be looked up that way (you'd have to pull every stored token and `checkpw` each one). SHA-256 is fast, deterministic, and indexable — the correct tool for this specific job.

**Trade-off accepted:** None material — using the "stronger" bcrypt here would actually be the wrong choice, not a safer one, since it breaks the required lookup pattern.

**Interview angle:** *"I used two different hash functions for two different reasons: bcrypt for passwords because it needs to be slow, SHA-256 for refresh tokens because they need to be looked up by exact match, and a salted hash can't do that efficiently. Using bcrypt everywhere 'for consistency' would have been the less correct choice, not the safer one."*

---

## Current User Resolution: Re-query DB Every Request
**Phase:** A4
**Date:** 22-07-2026

**Options considered:** Trust the JWT's embedded `org_id`/`role` claims directly (fully stateless, no DB hit) vs re-query the `users` table by `sub` on every authenticated request

**Chosen:** Re-query the DB every request

**Why:** A stateless JWT is only as current as the moment it was issued — if a user's role changes or their account is deactivated, a pure-claims approach means that change doesn't take effect until the access token naturally expires (up to 30 minutes later). Re-querying costs one extra indexed query per request in exchange for immediate consistency.

**Trade-off accepted:** One additional DB round-trip per authenticated request — a real latency/throughput cost at scale, accepted here because correctness (a revoked admin losing access immediately, not in up-to-30-minutes) matters more than shaving one query for this project's actual load.

**Interview angle:** *"I chose consistency over pure statelessness for `get_current_user` — the JWT still carries org_id and role, but I don't trust them blindly, I use the token only to identify who's asking, then re-check their current role from the database. That's a deliberate latency-for-correctness trade-off, not an oversight — a fully stateless version would be faster but means a role change or deactivation doesn't take effect until the token expires."*

---

## Document Deletion: Soft Delete (Archive) Only
**Phase:** A4
**Date:** 22-07-2026

**Options considered:** Hard `DELETE FROM documents` vs soft delete via `is_archived=True` (the column already existed since A2)

**Chosen:** Soft delete only — `DELETE /documents/{id}` sets `is_archived=True`, no hard-delete endpoint exists

**Why:** This is a legal-tech product with an audit trail (A2's `audit_log` table) — an irrecoverable hard delete is a worse default than an archive a user can be shown/restored later. "We accidentally deleted evidence of a contract review" is a materially worse failure mode than "the document is hidden by default but still there."

**Trade-off accepted:** No way to actually free storage/reduce row count via the API yet. If a genuine hard-delete need arises (e.g., a GDPR-style erasure request), it should be a separate, explicitly admin-only endpoint — not this verb's default behavior.

**Interview angle:** *"Delete on this system doesn't delete — it archives. In a domain where losing evidence of what a contract review actually said is a real liability, I'd rather the default action be reversible, with a genuine hard-delete as a separate, more deliberate path if it's ever needed."*

---

## Bug: Full-Text Search Silently Matched Nothing on Real Filenames
**Phase:** A4
**Date:** 22-07-2026

**What was found:** `GET /documents/search?q=original` returned `[]` against a document literally named `original.pdf`. Root cause, confirmed empirically against a real Postgres instance: `to_tsvector('english', 'original.pdf')` produces a single fused lexeme `'original.pdf'`, not separate `original`/`pdf` tokens — Postgres's default text search parser treats a `word.extension` pattern as one "file" token. The same issue affects underscores: `to_tsvector('english', 'Vendor_NDA_Agreement.pdf')` also produces one fused token, not three words. Since every realistic uploaded filename has an extension, and many will use underscores, the search feature as originally built would have matched almost nothing on real data — a demo would look broken with virtually any real contract filename.

**Fix:** Changed the generated `search_vector` column's expression from `to_tsvector('english', filename)` to `to_tsvector('english', regexp_replace(regexp_replace(filename, '\.[^.]+$', ''), '[_-]', ' ', 'g'))` — strips the file extension and normalizes underscores/hyphens to spaces before tokenizing. Verified against multiple realistic cases (`Vendor_NDA_Agreement.pdf`, `Q3 Lease Agreement.pdf`, `original.pdf`) that each now indexes as separate, correctly stemmed lexemes, and that `plainto_tsquery('english', 'vendor')` now actually matches.

**Why this matters:** This wasn't caught by design review — it was caught by actually testing the endpoint end-to-end with a real filename, exactly the "test both, briefly, so it isn't a hypothetical claim" discipline this project is meant to build. Also required a real Alembic mechanic worth knowing cold: a `GENERATED ALWAYS AS ... STORED` column's expression can't be `ALTER`ed in place — Postgres requires drop-and-recreate, and Alembic's autogenerate doesn't reliably detect an expression-only change to a computed column (it produced an empty migration on the first attempt), so the fix migration had to be hand-written.

**Interview angle:** *"My full-text search worked perfectly against test data like 'the auto-renewal clause' but returned nothing against a document literally named original.pdf — because Postgres's tokenizer treats 'word.extension' as one fused token, not two words. I caught it by actually testing with a realistic filename instead of trusting the design, root-caused it against a real Postgres instance rather than guessing, and the fix — stripping the extension and normalizing separators before indexing — also taught me that generated columns can't be altered in place, which Alembic's autogenerate didn't handle correctly on its own."*

---

## Search: Archived Documents Excluded By Default
**Phase:** A4
**Date:** 22-07-2026

**Options considered:** `GET /documents/search` always includes archived documents (findability over consistency) vs excludes them by default with an `include_archived` opt-in, matching `GET /documents`'s existing behavior

**Chosen:** Excluded by default, `include_archived=true` param to opt in

**Why:** Both are legitimate "browse my documents" surfaces (list and search) — having them default to different visibility rules would be an inconsistency I'd have to explain away rather than defend. Least-surprise principle: searching almost always means "help me find what I'm currently working with," not "show me everything including things I deliberately archived." Consistent with the soft-delete decision above — nothing is actually hidden forever, just not shown unless asked for.

**Trade-off accepted:** A user who knows they archived something and wants to find it again must remember to pass `include_archived=true` — a minor discoverability cost, mitigated by it being an explicit, documented parameter rather than a hidden behavior difference between endpoints.

**Interview angle:** *"I made list and search behave identically with respect to archived documents on purpose — same default, same opt-in parameter name. Two 'browse' endpoints on the same resource silently disagreeing about what 'show me my documents' means is exactly the kind of inconsistency that looks like a bug even when each individual behavior is defensible on its own."*

---

## Known Gap (Deferred, Not Yet Decided): No Way to Add a User to an Existing Organization
**Phase:** A4
**Date:** 22-07-2026

**What was found:** Testing role-gating (viewer vs admin) required manually `INSERT`-ing a second user directly into Postgres via `psql`, because no API path exists to add a user to an org that already has one — `POST /auth/signup` always creates a brand-new organization with the caller as its sole admin. This means, as the system stands, an organization can never legitimately grow past its founding user through the API.

**Status:** Explicitly flagged as a real, named product gap — not silently shipped, not yet resolved. Not fixed in A4; needs a deliberate decision (invite-by-email flow? admin-creates-user-directly endpoint? something else?) before being built, rather than being bolted on reactively.

**Interview angle:** *"While testing role-based access control, I hit a real gap empirically, not hypothetically: there's currently no way for a second person to join an existing organization through the API at all — I had to insert a user directly into Postgres to test it. I've deliberately left this open rather than rushing a fix, because the right shape for that flow (invite links vs admin-created accounts vs something else) deserves an actual decision, not a bolt-on."*

## Audit Log Wiring: Auth + Document Events
**Phase:** A4
**Date:** 22-07-2026

**What was done:** Wired `AuditLogRepository.create()` into six real events, following the `resource.verb` naming convention established in A2: `user.signed_up`, `user.logged_in`, `user.login_failed`, `user.logged_out`, `document.uploaded`, `document.upload_deduplicated`, `document.archived`. Each write happens in the same DB transaction as the action it's logging (added before the existing `db.commit()`, not a separate commit) — an audit entry and the event it describes succeed or fail together, not as two independent writes that could disagree.

**Why this matters:** This is the first real consumer of the append-only `AuditLogRepository` built in A2 — it sat unused for two phases. Choosing to log the *dedup* case (`document.upload_deduplicated`) separately from a real upload was a deliberate call: they're different events worth distinguishing in a real audit trail (a user re-uploading the same file isn't the same story as a genuinely new document), not just noise to collapse into one action.

**Trade-off accepted:** `/auth/refresh` is deliberately NOT logged — at a ~30-minute access token lifetime, it would fire roughly as often as normal usage, adding volume without adding signal. Login/logout are the meaningful session boundaries; a routine refresh isn't.

**Interview angle:** *"The audit_log table and its repository existed since A2, but had zero real callers until A4 — I built the shape without a concrete consumer, which is a normal sequencing call for schema work, but it meant nothing was actually proven correct until I wired six real events in and empirically confirmed rows landing correctly, including making sure each write shares a transaction with the action it describes."*

---

## Known Gap: Unknown-Email Failed Logins Aren't Audit-Logged
**Phase:** A4
**Date:** 22-07-2026

**What was found:** `audit_log.org_id` is `NOT NULL` (by design, from A2 — every audit row belongs to a tenant). A failed login against an email that doesn't exist at all has no `org_id` to attribute the attempt to, so it can't be written to this table. Only failed attempts against a *known* email (wrong password, correct email) get logged, since only that case has a resolvable `org_id`.

**Status:** Named and accepted, not fixed. A real limitation for security monitoring — this table alone can't detect someone probing random/guessed emails, only someone repeatedly failing against one they got right. A genuine fix would mean either a separate, org-independent security-events table, or relaxing `org_id` to nullable specifically for this one row type — neither was judged worth doing for this project's actual scope.

**Interview angle:** *"My audit log can't see every failed login attempt — only ones against emails that actually exist, because the schema deliberately requires every row to belong to an organization, and an unknown email has none. I could've relaxed that constraint to catch the blind case too, but chose not to, since it would weaken a guarantee (every audit row is tenant-attributable) for a monitoring capability outside this project's actual scope. Worth naming as a real trade-off rather than pretending the audit trail is more complete than it is."*

# Phase A5 Decisions

---

## Test Database Strategy: Separate Postgres DB via Alembic, Not `create_all()`
**Phase:** A5
**Date:** 23-07-2026

**Options considered:** `Base.metadata.create_all()` against a test DB vs. running the real Alembic migration chain (`alembic upgrade head`) against a separate test database

**Chosen:** Separate `contract_intel_test` database in the existing Postgres container, schema built exclusively via `alembic upgrade head`

**Why:** `documents.search_vector` is a hand-migrated `GENERATED ALWAYS AS (...) STORED` column (A4) that exists only as raw migration SQL, not as an ORM-expressible `Column`/`Computed()` construct — `create_all()` would silently produce a schema missing that column and its GIN index, and full-text search tests would fail or, worse, pass against a schema that doesn't match production. Running the real migration chain is also itself a valuable end-to-end check: the first time all 8 migrations replayed cleanly against a genuinely fresh database.

**Trade-off accepted:** Slower test-suite bootstrap than `create_all()`, and the test DB must be manually created once (`CREATE DATABASE`) before migrations can run — not automated as part of the test run itself.

**Interview angle:** *"I deliberately didn't use SQLAlchemy's create_all() for the test database, because one of my columns — a generated tsvector column for full-text search — only exists as hand-written migration SQL, not as an ORM construct. create_all() would have silently built a test schema that didn't match production. Running the real Alembic chain against a fresh database also doubled as the first real proof that my full migration history replays cleanly end-to-end."*

---

## Settings/Engine Import-Time Binding: `.env.test` Must Load Before Any `app.*` Import
**Phase:** A5
**Date:** 23-07-2026

**Options considered:** Override `DATABASE_URL` via a pytest fixture/monkeypatch after imports vs. loading a separate `.env.test` file before any application import happens

**Chosen:** `load_dotenv(".env.test", override=True)` as the literal first executable lines in `conftest.py`, before any `from app...` import anywhere in the import chain

**Why:** Both `Settings()` (config.py) and the SQLAlchemy `engine` (session.py) are constructed once at module import time, not lazily per-request. A fixture-level override (e.g. monkeypatching `settings.database_url` inside a test) would not affect the already-constructed `engine` object, which is bound to whatever DB was live at import time — silently running tests against the dev database instead of the test database. The only correct fix is controlling environment state before the first import, not after.

**Trade-off accepted:** A fragile ordering constraint that isn't enforced by any tooling — a future contributor (or future me) adding an `import app.something` above the `load_dotenv` call in `conftest.py` would silently break test isolation with no error message, just tests quietly running against the dev DB. Documented with a loud comment at the top of `conftest.py`, not otherwise guarded against.

**Interview angle:** *"I found a real gotcha with module-level singletons: my Settings object and DB engine are both constructed once, at import time. That means you can't swap the test database with a normal fixture override — by the time a fixture runs, the engine's already bound to the wrong DB. The fix has to happen before the first app import in the whole test session, which is a real ordering constraint I had to get right, not just a convenience."*

---

## Test Isolation: Outer Transaction + Auto-Restarting SAVEPOINT per Test
**Phase:** A5
**Date:** 23-07-2026

**Options considered:** Truncate all tables between tests vs. recreate schema per test vs. wrap each test in an outer transaction with a nested SAVEPOINT that auto-restarts after every `session.commit()`

**Chosen:** Outer transaction + auto-restarting SAVEPOINT (the standard SQLAlchemy "join a savepoint" pattern)

**Why:** Route handlers call `db.commit()` throughout the real code (`documents.py`, `auth.py`) — a naive single-transaction-per-test approach would break the moment any route under test committed, since that would end the transaction the test's rollback depends on. The SAVEPOINT pattern lets route-level commits behave normally during the test while the true rollback boundary (the outer transaction) is untouched, discarding all test data on teardown regardless of how many commits happened inside.

**Trade-off accepted:** More complex fixture code than truncation, and genuinely subtle if something goes wrong (a `session.expire_all()` at the wrong point, or an event listener misfiring, produces confusing test pollution rather than a clean error). Verified empirically (not just assumed correct) by confirming `SELECT count(*) FROM users` returned 0 against the real test DB after a signup test ran.

**Interview angle:** *"Because my routes commit mid-request, a simple 'wrap the test in a transaction and roll back' approach doesn't work on its own — the route's own commit would end that transaction early. I used the SAVEPOINT pattern instead, and I didn't just trust it — I directly queried the test database after a signup test ran and confirmed the row count was zero, proving the rollback boundary actually holds."*

---

## RQ Enqueue Mocked in Tests, Not Exercised via Real Redis/Worker
**Phase:** A5
**Date:** 23-07-2026

**Options considered:** Run a real RQ worker against real Redis during integration tests vs. mock `document_queue.enqueue` and assert on call arguments only

**Chosen:** Mocked, autouse fixture (`mock_enqueue`) replacing `enqueue` with a call-recording stub

**Why:** A3 already empirically proved queue mechanics work correctly (stopped/restarted worker, confirmed jobs sit pending in Redis and get picked up) — re-proving that in A5 would be redundant effort. A5's actual job is proving the upload endpoint hands off the *correct* work (right function, right version ID), not re-verifying Redis/RQ delivery.

**Trade-off accepted:** A5's test suite would not catch a regression in actual RQ/Redis wiring (e.g., a broken Redis connection string) — that class of failure is outside this phase's scope and would need a separate, deliberately-live integration test to catch, not currently built.

**Interview angle:** *"I mocked the queue call rather than running a real worker in tests, because I'd already proven the queue mechanics manually in an earlier phase — re-testing Redis delivery here would be duplicated effort. What I actually wanted A5 to prove was narrower: that uploading a document hands off the right job with the right arguments, which a mock lets me assert directly and quickly."*

---

## Sync `TestClient` Used Instead of `httpx.AsyncClient`
**Phase:** A5
**Date:** 23-07-2026

**Options considered:** `pytest-asyncio` + `httpx.AsyncClient` (as originally specified in the execution plan) vs. FastAPI's synchronous `TestClient`

**Chosen:** Synchronous `TestClient`

**Why:** Every route in the application is defined as a regular `def`, not `async def` — there is no async code path anywhere in the request-handling flow for an async client to meaningfully exercise differently from a sync one. Introducing `pytest-asyncio` and async fixtures would have added real complexity (event loop management, async fixture chaining) with no corresponding coverage benefit.

**Trade-off accepted:** A direct deviation from the execution plan's stated tooling ("pytest + httpx.AsyncClient"). If future phases introduce genuinely async routes (e.g., a streaming RAG response in Phase B), this decision should be revisited rather than carried forward by default.

**Interview angle:** *"My execution plan called for httpx.AsyncClient, but every route in my app is synchronous — there was no async behavior for an async client to actually test differently. I made a deliberate call to use the simpler sync TestClient instead, and documented the deviation rather than following the plan just because it was written down. I'd revisit this the moment a route actually becomes async."*

---

## Known Gap: Test-Storage Cleanup Not Implemented
**Phase:** A5
**Date:** 23-07-2026

**What was found:** Unlike the database (rolled back per test via the SAVEPOINT pattern), files written to disk during upload tests (`storage_test/`) are not cleaned up automatically — confirmed empirically: after a full test run, dozens of orphaned PDF folders remained in `storage_test/` despite all corresponding DB rows being rolled back.

**Status:** Named, not fixed. `storage/` (the real dev storage directory) was separately confirmed untouched by any test run — the actual risk (test writes polluting real data) doesn't exist; this is purely a test-artifact accumulation issue in a disposable, gitignored directory.

**Interview angle:** *"My test isolation covers the database but not the filesystem — uploaded test files accumulate in a separate test-only storage directory across runs. I verified the real storage directory is never touched, so there's no data-safety risk, but a proper fix would be a tmp_path-based fixture or a session-end cleanup step. I left it as a named gap rather than building it, since it doesn't affect correctness, only disk usage in a throwaway, gitignored folder."*

---

## Auth Flow Test Coverage: Signup, Login, Refresh, Logout
**Phase:** A5
**Date:** 23-07-2026

**What was done:** Added `tests/integration/test_auth.py` — 10 tests covering signup (success + duplicate-email 409), login (success, wrong password, unknown email), refresh (success + invalid token), and logout (revokes token + idempotent on unknown token). Specifically included a test asserting the login endpoint returns an *identical* status code and detail message for "wrong password" vs. "unknown email" — directly verifying the anti-enumeration property documented in `auth.py`'s own code comments, rather than just trusting the comment.

**Why this matters:** This was initially scoped out of A5 as a named gap (auth got exercised only indirectly via the `signed_up_client` fixture used by every other test file) and closed deliberately before moving to A6, rather than left open. Coverage on `app/routers/auth.py` went from 55% to 99%.

**Interview angle:** *"I initially scoped auth out of A5 since it was getting indirect coverage from every other test's setup fixture, but I went back and closed it properly before moving on — including a test that doesn't just check status codes, but actually verifies the anti-enumeration security property I'd documented: that a wrong password and an unknown email produce byte-identical responses, so an attacker can't use the login endpoint to enumerate valid accounts."*

---

## A5 Final State
**Phase:** A5
**Date:** 23-07-2026

**Summary:** 33 automated tests (10 auth, 4 search, 4 upload, 1 ingestion idempotency, 3 tenant isolation via API, 5 chunking, 4 parsing, 2 tenant isolation via repository), 89% overall code coverage, run together in a single suite with no cross-test pollution. Manual verification scripts from earlier phases (`test_chunking.py`, `test_parsing.py`, `test_reprocess.py`, `smoke_test_isolation.py`) were deleted after their scenarios were formalized as real pytest cases.

**Interview angle:** *"By the end of A5 I had 33 tests replacing what used to be four manual scripts I had to remember to re-run by hand. The same scenarios are now checked automatically, every time, and I have an honest coverage number — 89% — rather than a vague sense that things probably still work."*


# Phase A6 Decisions.
## A6 (CI/CD Pipeline) — Paused Mid-Setup, Deferred to End of Project
**Phase:** A6
**Date:** 25-07-2026

**What was done:** Started A6 — installed Ruff (`ruff==0.16.0`, committed to `requirements.txt` on `main`), began configuring `pyproject.toml` for lint/format rules, and set up a `ci/setup-github-actions` branch to hold the work. Paused before writing the actual GitHub Actions workflow file. The `pyproject.toml` config was deleted rather than left half-correct; `main` currently has the unused `ruff` dependency with no matching config, and the `ci/setup-github-actions` branch is stale (predates the one commit that landed on `main` directly, bypassing the branch/PR flow that was the intended workflow for this phase).

**Why paused:** No functional dependency blocks this — nothing in Phase A or B requires CI/CD to exist; A7 can be deployed manually, and Phase B doesn't touch this at all. The friction hitting so far was entirely terminal/editor mechanics (heredocs not pasting cleanly into `nano`, multi-line paste behavior), not the CI/CD concepts themselves — a different kind of blocker than the actual engineering work in this project, and not worth grinding through at the cost of momentum on higher-value phases.

**Status:** Deliberately deferred, not abandoned — to be resumed at the end of the project, after Phase A and B are complete, using a cleaner setup approach (avoiding the heredoc/paste issues that caused the friction this round).

**Trade-off accepted:** `main` temporarily carries an unused `ruff==0.16.0` line with no config behind it — a small, harmless loose end, cheap to close when A6 resumes. No automated test/lint gate exists yet, meaning pushes to `main` between now and A6's completion aren't protected by CI — an accepted risk given the project is solo-developed and each phase is already manually verified before moving on.

**Interview angle:** *"I started A6, got Ruff installed and was mid-way through the GitHub Actions config, and made a deliberate call to pause it — not because the CI/CD work itself was hard, but because I hit a run of pure terminal-tooling friction that wasn't worth grinding through at the cost of momentum on the actual differentiating engineering in Phase B. I'd rather come back to it later with a cleaner setup than push through irritated and end up with a workflow file I don't fully understand."*

---

## No Frontend — Backend-Only Scope, `/docs`/Postman as Demo Surface
**Phase:** Scope (cross-cutting)
**Date:** 25-07-2026

**Options considered:** Build a minimal frontend now, in parallel with Phase A/B vs. defer any frontend decision entirely until Phase A and B are both complete vs. never build one, rely permanently on `/docs`/Postman for demos

**Chosen:** Defer — no frontend work happens during Phase A or B; revisit only after both are fully complete

**Why:** The spec, execution plan, and every phase so far were written with a backend-only scope from the start — A7's own verification step is "confirm `/docs` works," not "confirm a UI works," which was never accidental. The interview-differentiating work in this project (citation verification, injection defense, hybrid retrieval, eval harness) lives entirely in the backend/AI layer; a frontend competing for time during Phase A/B would dilute focus away from the harder, rarer engineering this project is actually meant to demonstrate. Deferring the decision itself — rather than either committing to "never" or building one reactively mid-phase — keeps the option open without letting it become scope creep now.

**Trade-off accepted:** No polished visual demo exists until after Phase B — interview demos until then rely entirely on Swagger UI (`/docs`) and Postman walkthroughs. If a live visual demo becomes needed sooner (e.g. sharing the project link informally before Phase B finishes), this decision would need revisiting.

**Interview angle:** *"This project never had a frontend in scope — deliberately. The verification checkpoints throughout the plan use Swagger UI and Postman, not a UI, because the differentiating engineering here is the backend and AI-safety layer: citation verification, injection defense, hybrid retrieval. I made an explicit call to defer any frontend decision until after Phase B, rather than let it dilute focus or get bolted on reactively mid-build."*

---


# Phase A7 Decisions

---

## Hosting Platform Selection: Render over Fly.io
**Phase:** A7
**Date:** 25-07-2026

**Options considered:** Render vs Fly.io (both free-tier, both viable for a containerized FastAPI deployment)

**Chosen:** Render

**Why:** This was my first deployment ever, and Render's dashboard-driven UX gives more visual feedback while learning what's actually happening at each step — service creation, environment variables, build logs — versus Fly.io's more CLI-driven flow. Fly.io generally has faster cold-starts and a steeper learning curve; Render trades some of that performance for a gentler first-deployment experience, which mattered more given zero prior deployment experience.

**Trade-off accepted:** Render's free tier spins down after 15 minutes of inactivity, and the first request after idle can take 30-60 seconds to respond — a real, user-facing limitation for a live demo, explicitly documented in the README rather than discovered by surprise.

**Interview angle:** *"I chose Render over Fly.io for my first deployment specifically for the learning experience — a dashboard-driven flow with visible build logs at every step, versus a CLI-first tool. I made the trade-off deliberately: Render's free tier has a real cold-start delay I now have to account for and document, but the platform itself was the right choice for actually understanding what a deployment pipeline does, not just running a command that works."*

---

## Hosted Database Selection: Neon over Supabase
**Phase:** A7
**Date:** 25-07-2026

**Options considered:** Neon vs Supabase (both free-tier hosted Postgres)

**Chosen:** Neon

**Why:** Supabase bundles Postgres with auth, storage, and realtime features that overlap with things I've already built myself (JWT auth from A4, local disk storage from A3) — using it would mean either ignoring most of its surface area or being tempted into scope creep. Neon is Postgres-only, which matches exactly what this project needs from a hosted database: nothing more.

**Trade-off accepted:** None material — Neon's feature set is a strict subset of what I needed, no capability was given up.

**Interview angle:** *"I picked Neon over Supabase because Supabase's extra features — auth, storage, realtime — would have been redundant against systems I'd already built myself. I wanted a database, not a platform, and didn't want the temptation of scope creep into features this project doesn't need."*

---

## Postgres Version Pinned to 16 on Neon (Not Neon's Default of 18)
**Phase:** A7
**Date:** 25-07-2026

**Options considered:** Accept Neon's default Postgres version (18) vs explicitly select 16 to match local dev

**Chosen:** Postgres 16, matching the local Docker Compose environment exactly

**Why:** My local dev database (per the A2 decision) runs Postgres 16, and my migrations — including the hand-written `GENERATED ALWAYS AS ... STORED` column fix from A4 — were tested against that exact version. A version mismatch between dev and prod is a known source of subtle, hard-to-diagnose behavior differences; keeping them identical removes an entire class of "works locally, breaks in prod" risk for zero cost.

**Trade-off accepted:** None — explicitly selecting a dropdown option instead of accepting a default costs nothing.

**Interview angle:** *"Neon defaulted to Postgres 18, but I deliberately pinned it to 16 to match my local Docker environment exactly — my migrations, including a hand-written generated-column fix from A4, were tested against 16 specifically. Dev/prod version parity isn't glamorous, but it's exactly the kind of detail that prevents a confusing bug three weeks from now."*

---

## Docker Language Auto-Detect Mismatch on Render (Caught Before Deploying)
**Phase:** A7
**Date:** 25-07-2026

**What was found:** When creating the Render web service, Render auto-detected "Language: Python 3" instead of Docker — silently defaulting to its own native Python buildpack (auto-filled Build/Start Command fields showing `pip install -r requirements.txt` / `gunicorn your_application.wsgi`, the latter being generic Django-style boilerplate, not even correct for a FastAPI/uvicorn app). Had this gone unnoticed, Render would have completely bypassed the multi-stage Dockerfile that had already been written and tested locally.

**Fix:** Manually changed the "Language" dropdown from `Python 3` to `Docker` before deploying, which removed the Build/Start Command fields entirely (correct — the Dockerfile's own `CMD` defines the start command) and confirmed Render would build from the actual Dockerfile.

**Why this matters:** This wasn't a hypothetical risk — it's the literal default behavior Render would have shipped with if the setup screen hadn't been read carefully. Auto-detected tooling defaults are worth verifying explicitly, not trusting blindly, especially the first time using a new platform.

**Interview angle:** *"Render auto-detected my repo as a plain Python app and was about to deploy using its own buildpack and a generic gunicorn start command, completely ignoring the Dockerfile I'd already built and tested — I caught it by actually reading the auto-filled fields instead of clicking through the setup screen on autopilot, and switched the language selector to Docker before deploying."*

---

## `.dockerignore` Added After Discovering 228MB Build Context
**Phase:** A7
**Date:** 25-07-2026

**What was found:** The first local `docker build` reported `transferring context: 228.00MB` — far too large for a FastAPI backend's actual source code. Root cause: no `.dockerignore` existed, so Docker was sweeping `storage/`, `storage_test/` (dozens of test PDFs accumulated across earlier phases), and other local-only artifacts into the build context, and `COPY . .` in the Dockerfile was copying all of it into the final image.

**Fix:** Added a `.dockerignore` file excluding `venv/`, `storage/`, `storage_test/`, `__pycache__/`, `.pytest_cache/`, `.git/`, `.env`, `.env.test`, `docs/`, and `.coverage`. Rebuilding afterward dropped the build context from 228MB to 9.33kB, and subsequent builds became dramatically faster due to Docker's layer caching working correctly on the now-minimal context.

**Why this matters:** Without this fix, every deployed image would have silently shipped dozens of local test PDFs and potentially the entire `venv/` directory — bloating the image, slowing every future build/deploy, and leaking local test artifacts into what's actually running in production. Caught by actually reading the build output line-by-line, not by assuming the build "just worked" because it completed successfully.

**Interview angle:** *"My first Docker build transferred 228MB of build context for what should be a lightweight FastAPI app — I hadn't written a `.dockerignore`, so Docker was sweeping in test PDFs and other local-only artifacts that had accumulated over five phases of development. Adding `.dockerignore` dropped that to under 10KB and meant my deployed image wasn't silently shipping test data that had nothing to do with the running application."*

---

## Multi-Stage Dockerfile Build
**Phase:** A7
**Date:** 25-07-2026

**Options considered:** Single-stage Dockerfile (install dependencies and run in the same image) vs multi-stage build (separate build stage for dependency installation, copy only the result into a clean final image)

**Chosen:** Multi-stage build — a `builder` stage runs `pip install --user`, and the final runtime stage copies only the installed packages (`/root/.local`) plus application code, starting from a fresh `python:3.12-slim` base.

**Why:** A single-stage build would leave pip's build artifacts, caches, and any transient install-time files inside the final image — none of which are needed at runtime. Multi-stage builds produce a smaller final image with a smaller attack surface, at the cost of a slightly longer/more complex Dockerfile.

**Trade-off accepted:** More verbose Dockerfile (two `FROM` statements, an explicit `--from=builder` copy) versus a single-stage file — a small, one-time complexity cost for a real, recurring image-size benefit.

**Interview angle:** *"I used a multi-stage Docker build so my final deployed image only contains what's actually needed at runtime — the installed Python packages and my application code — not the pip cache and build artifacts left over from installing dependencies. It's a standard production pattern, and worth the extra few lines of Dockerfile for a meaningfully smaller, cleaner final image."*

---

## Credential Exposure and Rotation: Neon Password and JWT Secret
**Phase:** A7
**Date:** 25-07-2026

**What happened:** During the Alembic-against-Neon migration step and the first local Docker container test, the real Neon database connection string (including password) was pasted directly into the AI assistant chat twice, and the real `JWT_SECRET_KEY` value once — despite being explicitly asked not to, to keep credentials out of any channel beyond a password manager or gitignored local file.

**Response:** Reset the Neon database password immediately upon being flagged, generated a fresh `JWT_SECRET_KEY` via `secrets.token_urlsafe(64)`, and used only the rotated credentials going forward — including in Render's environment variables, entered directly into Render's dashboard rather than shared anywhere else.

**Why this matters:** This is a genuine security-hygiene lapse worth documenting honestly rather than omitting — the actual behavior that matters isn't "never make this mistake," it's "notice it, rotate immediately, and don't let a leaked credential stay live." A real production incident response looks exactly like this at small scale: contain, rotate, verify.

**Trade-off accepted:** None — the fix (password rotation) is a complete remediation with no residual risk once the old credentials were invalidated.

**Interview angle:** *"Early in my first deployment, I pasted a real database credential into a chat channel I'd been told to keep it out of — a genuine mistake, not a hypothetical one. What matters is what I did next: I rotated the password immediately, generated a fresh JWT secret, and made sure only the new credentials were ever used going forward. I'd rather be honest about that than pretend it didn't happen — recognizing and immediately remediating a credential exposure is itself a real, demonstrable security practice."*

---

## Free-Tier Cold Start Investigated, Not Assumed
**Phase:** A7
**Date:** 25-07-2026

**What was found:** The first live upload request against the deployed API returned a plain-text `Internal Server Error` with no JSON body — but a follow-up request against the same file immediately returned a normal, successful response with `"duplicate": true`. Rather than assuming the first request had genuinely failed server-side, checked the actual evidence: a `GET /documents` call showed exactly one document row existed, meaning the first request had, in fact, succeeded in creating the document — only the response delivery back to the client was disrupted.

**Conclusion:** The most likely explanation is Render's free-tier cold-start behavior (the dashboard itself warns that an idle instance can delay the first request by 50+ seconds), not a bug in the application. The evidence (exactly one document row, correctly deduplicated second request) is consistent with this and inconsistent with a genuine server-side failure on the first request.

**Why this matters:** The instinct to verify actual state (query the document list, check the row count) rather than accept a confusing client-side error message at face value is the same discipline applied throughout this project's tenant-isolation and idempotency testing (A2, A3) — applied here to a deployment-environment quirk instead of application logic.

**Trade-off accepted:** Render's server logs for that exact request window weren't independently checked to fully rule out a transient server-side error — the dedup evidence was judged sufficiently conclusive on its own, though a stronger confirmation would have cross-referenced Render's logs directly.

**Interview angle:** *"My first live upload request came back as a generic Internal Server Error, but instead of assuming the app was broken, I checked the actual state — queried the document list and found exactly one row had been created, and a retry correctly triggered my dedup logic. That told me the request had actually succeeded server-side; only the response back to the client was disrupted, almost certainly by Render's free-tier cold-start delay, which the platform itself warns about. I verified against real state rather than trusting a confusing error message."*

---

## No Worker Deployed — Processing Intentionally Stays `pending` in Production
**Phase:** A7
**Date:** 25-07-2026

**What was done:** Deployed only the FastAPI web service to Render. No Redis instance and no RQ worker process were deployed alongside it — `REDIS_URL` is set to a placeholder value that nothing in the web service actually connects to at boot time. Verified live: an uploaded document's `parse_status` remains `pending` indefinitely on the deployed instance, since nothing is consuming the (non-existent, in production) job queue.

**Why:** A7's stated goal is proving the containerized web API deploys and serves real traffic correctly — not standing up the full async processing infrastructure, which is a separate, later concern (worker deployment, a hosted Redis instance, etc.). Scoping A7 to the web service alone keeps this phase's actual goal achievable and verifiable without conflating it with a second deployment target.

**Trade-off accepted:** The live demo cannot currently process uploaded documents end-to-end — uploads succeed and are stored, but parsing/chunking never happens on the deployed instance. Explicitly documented in the README as a known, deliberate limitation rather than left for a visitor to discover confused. This exact scenario — upload succeeds, processing stays `pending` with no worker running — was already proven safe and expected behavior locally in A3.

**Interview angle:** *"I deployed the web API on its own, deliberately, without a background worker — that's a separate deployment target I haven't built yet, not an oversight. I verified live that uploads succeed and are stored correctly, and that processing correctly stays pending with no worker running, which is exactly the behavior I'd already proven safe locally back in Phase A3. I documented this as a known limitation in the README rather than let someone discover a 'broken' feature that's actually just an intentionally unbuilt one."*

---

## A7 Final State
**Phase:** A7
**Date:** 25-07-2026

**Summary:** Application successfully containerized (multi-stage Dockerfile, `.dockerignore`-optimized build context), deployed to Render from GitHub with auto-deploy on push to `main`, backed by a hosted Neon Postgres 16 instance with the full migration chain applied. Live URL verified end-to-end: signup, login, document upload with correct org-wide deduplication, tenant-scoped document listing, version status polling, and full-text search all confirmed working against the real deployed stack — not just locally. README first pass written with architecture diagrams, honest documentation of current limitations (no worker deployed, free-tier cold starts), and setup instructions matched to the actual `docker-compose.yml`.

**Interview angle:** *"By the end of A7 I had a live, publicly reachable URL running the actual containerized application against a real hosted database — and I didn't just deploy it and call it done, I walked through the full upload-to-search flow against production to prove it actually works, catching real issues along the way: a build-context bloat, a platform auto-detect defaulting to the wrong build path, and a credential I had to rotate after a handling mistake. Each of those became something I understood and fixed, not just something that happened to me."*



### Phase - B 
# Phase B1 Decisions

---

## Embedding Model Selection: BAAI/bge-small-en-v1.5 over MiniLM
**Phase:** B1
**Date:** 28-07-2026

**Options considered:** `sentence-transformers/all-MiniLM-L6-v2` (common tutorial default) vs `BAAI/bge-small-en-v1.5`

**Chosen:** `BAAI/bge-small-en-v1.5`

**Why:** bge-small outperforms MiniLM on MTEB retrieval benchmarks while remaining CPU-friendly (133MB model weights, 384-dimension output) — no GPU required, consistent with this project's "no API cost, runs locally" embedding philosophy already stated in the spec. bge models are trained asymmetrically: queries require a specific instruction prefix (`"Represent this sentence for searching relevant passages: "`) prepended before embedding, while passages (chunks) are embedded plain. This is a real, non-obvious detail — getting it backwards doesn't error, it just silently produces worse retrieval with no diagnostic signal that anything is wrong.

**Trade-off accepted:** Slightly more implementation care required than MiniLM (the asymmetric prefix logic), in exchange for measurably better retrieval quality on the benchmark this model was evaluated against. Enforced this correctness structurally by splitting `embed_passages()` and `embed_query()` into two separate functions, where only the query function has access to the prefix constant — makes it hard to accidentally apply the prefix in the wrong place.

**Interview angle:** *"I chose bge-small over the more commonly-tutorialed MiniLM because it scores higher on retrieval-specific benchmarks while still being small enough to run on CPU with no GPU cost. The real engineering detail worth mentioning is that bge is trained asymmetrically — queries and passages need to be embedded differently, with a specific instruction prefix only on the query side. That's not enforced by the library; I enforced it by splitting my embedding code into two functions so it's structurally hard to mix them up."*

---

## Vector Store Selection: Chroma over Qdrant/Pinecone
**Phase:** B1
**Date:** 28-07-2026

**Options considered:** Qdrant (self-hosted) vs Pinecone (managed cloud) vs Chroma (self-hosted)

**Chosen:** Chroma, self-hosted via Docker Compose (`chromadb/chroma:0.5.20`)

**Why:** Qdrant's real advantages — RBAC, horizontal scaling — solve problems this project's data volume never actually hits; adopting it would mean operating infrastructure whose benefits are never exercised. Pinecone is a paid external dependency that adds a network round-trip and a failure mode (API availability during a demo) for zero benefit at this scale, and contradicts the project's "no API cost, everything runs locally" principle already established for embeddings. Chroma bolts onto the existing `docker-compose.yml` with a single new service block and integrates with metadata filtering sufficient for B1-B3's actual needs.

**Trade-off accepted:** Chroma is less battle-tested at production scale than Qdrant, and lacks Qdrant's RBAC/clustering — a legitimate limitation to name explicitly if asked "would you use this in production," rather than implying Chroma was chosen for anything other than fit-for-scale.

**Interview angle:** *"I picked Chroma over Qdrant and Pinecone because the advantages of the more 'production-grade' options — Qdrant's RBAC and horizontal scaling, Pinecone's managed infrastructure — solve problems I don't actually have at this project's scale. Pinecone specifically would have added a paid external dependency and a network failure mode for no real benefit. I'd revisit this decision if this system needed to scale to millions of vectors or multiple operators — but building for that now would be complexity theater."*

---

## Separate `embedding_processing` RQ Queue, Single Worker Process
**Phase:** B1
**Date:** 28-07-2026

**Options considered:** (a) Embed inside the same job as chunking (`process_document_version_job`) vs (b) a separate downstream job on its own named queue. Also: one worker process listening to both queues vs two separate worker processes.

**Chosen:** (b) — separate `embedding_processing` queue, chunking job chains into it on success. One worker process (`run_worker.py`) listens to both `document_processing` and `embedding_processing`.

**Why:** Chunking is fast, deterministic, pure-CPU text work; embedding is a heavier, separate concern (model inference, more failure surface). Bundling them into one job means a transient embedding failure fails the entire ingestion, including chunking work that already succeeded — retrying would redo already-correct work. A separate queue lets embedding be retried independently. This queue was explicitly anticipated back in A3's decision log ("a named queue was used instead of RQ's default queue, anticipating future job types like embeddings"), so this is that anticipated moment, not new scope. Two separate worker *processes* were rejected as infrastructure complexity with no payoff at this project's actual concurrency (solo developer, one document at a time) — one worker consuming both queues is simpler to run and monitor, and can be split later if one queue ever starves the other.

**Trade-off accepted:** No dedicated status column (e.g. `embed_status`) exists on `DocumentVersion` or `Chunk` to track embedding success/failure the way `parse_status` tracks parsing — embedding failures currently surface only via RQ's own failure registry, not a queryable app-level field. Deliberately deferred rather than added reflexively; would need its own migration and design pass if the project later needs to *display* embedding status to a user, rather than just debug it via RQ.

**Interview angle:** *"I split embedding into its own RQ queue and job, chained off the successful completion of the existing chunking job, rather than doing both in one job — a transient failure in embedding shouldn't force re-doing chunking work that already succeeded. I deliberately kept it to one worker process consuming both queues rather than running two separate worker processes, since splitting them would be solving a scaling problem I don't actually have yet at this project's volume."*

---

## Single Chroma Collection with Metadata Filtering, Not Collection-Per-Tenant
**Phase:** B1
**Date:** 28-07-2026

**Options considered:** One Chroma collection per organization (tenant) vs a single shared collection (`contract_chunks`) with `org_id`/`document_id`/`document_version_id`/`is_current` stored as metadata on every vector, filtered at query time

**Chosen:** Single shared collection, metadata-filtered queries

**Why:** Collection-per-tenant means collection lifecycle management scales with organization count — creation, cleanup, and enumeration all become tenant-count-dependent operations. A single collection with metadata filtering avoids that entirely and is simpler to reason about and operate at this project's scale. Chroma's `where` clause supports compound filtering (`$and` across `org_id`, `document_id`, `is_current`) sufficiently for B1-B3's retrieval needs.

**Trade-off accepted:** A bug in metadata-filter construction is a more severe failure mode than in collection-per-tenant (where physical separation is the isolation boundary) — a malformed filter here could theoretically return cross-tenant results directly from Chroma. This is exactly why the `query()` function in `vector_store.py` is designed to return chunk IDs only, never content — see the next entry.

**Interview angle:** *"I used one shared Chroma collection with tenant/document metadata on every vector, rather than a collection per organization, because collection-per-tenant makes collection lifecycle scale with tenant count for no real isolation benefit at this project's scale. The trade-off is that isolation now depends on filter correctness rather than physical separation — which is exactly why I didn't stop at the Chroma layer for tenant isolation; Postgres is still the actual enforced boundary."*

---

## Vector Store as Untrusted Index, Postgres as the Real Tenant-Isolation Boundary
**Phase:** B1
**Date:** 28-07-2026

**Options considered:** Trust Chroma's metadata filter as the tenant-isolation boundary vs. treat it as a performance/relevance optimization only, with Postgres's existing tenant-scoped `ChunkRepository` as the actual enforced gate

**Chosen:** Chroma's `query()` function (`app/services/vector_store.py`) returns chunk ID strings only — never chunk content. Callers are structurally required to take those IDs to the existing tenant-scoped `ChunkRepository` to retrieve actual content.

**Why:** This directly mirrors the A2 decision to make the repository layer, not any individual query, the enforced tenant-isolation boundary, and the A4 decision to never fully trust a JWT's claims without re-verifying against the database. Chroma's metadata filter is real and useful for narrowing candidates and improving relevance, but it's an index, not an authorization system — a future bug in filter construction (a missing `org_id`, a typo) would otherwise become a direct cross-tenant data leak with no second check. By returning IDs only, any such bug is caught downstream by the repository's own `org_id` filter — the same mechanism your A2 isolation script already proved cannot return another tenant's data.

**Trade-off accepted:** An extra Postgres round-trip after every vector query (fetch chunk IDs from Chroma, then fetch actual content from Postgres by ID) instead of returning content directly from Chroma — a deliberate latency-for-correctness trade, same reasoning as A4's "re-query the DB every request" decision for `get_current_user`.

**Interview angle:** *"I designed my vector store wrapper to only ever return chunk IDs, never chunk content — so whatever calls it is structurally forced to go through my existing tenant-scoped repository to actually fetch data. That means even if I ever get the Chroma metadata filter wrong, the worst case is a query that returns nothing, not a query that leaks another tenant's contract text. It's the same principle as re-checking a JWT's claims against the database instead of trusting them blindly — don't let a single point of filtering be the only thing standing between a bug and a real data leak."*

---

## Bug: sentence-transformers Pulled GPU-Enabled Torch by Default, Exhausting Disk via CUDA Dependencies
**Phase:** B1
**Date:** 28-07-2026

**What was found:** `pip install -r requirements.txt` failed with `OSError: [Errno 28] No space left on device` partway through installing `sentence-transformers`. Root cause: `sentence-transformers` pulled in the default (GPU/CUDA-enabled) build of PyTorch as a transitive dependency, which in turn pulled a full NVIDIA CUDA toolkit — `nvidia-cublas` (423MB), `nvidia-cudnn-cu13` (366MB), `nvidia-nccl-cu13` (206MB), `triton` (197MB), `nvidia-cusparselt-cu13` (170MB), plus `torch` itself (526MB) — over 1.8GB of GPU libraries the project has no use for, since this WSL2 dev environment has no GPU passthrough configured.

**Fix:** Installed the CPU-only PyTorch build explicitly, before running the main install, using PyTorch's own package index: `pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu`. This satisfied `sentence-transformers`' torch dependency with the already-installed CPU build (192MB vs. the 526MB+1.8GB GPU variant), so re-running `pip install -r requirements.txt` never attempted to pull the CUDA stack at all.

**Why this matters:** This isn't just a disk-space workaround — it's the objectively correct dependency for this environment. The GPU build of torch is pure overhead for CPU-only inference; explicitly pinning the CPU build is a real, defensible engineering choice independent of the disk issue that surfaced it.

**Interview angle:** *"My dependency install failed with a disk-space error, and the actual root cause was that sentence-transformers was silently pulling in the GPU-enabled build of PyTorch — over 1.8GB of CUDA libraries — on a machine with no GPU to use them. The fix wasn't just freeing disk space; it was installing the CPU-only torch build explicitly, from PyTorch's own package index, before the main install ran. That's the objectively correct dependency for this environment regardless of the disk issue — I'd have wanted it that way even with unlimited disk space, since there's no reason to ship 1.8GB of unused GPU code."*

---

## Bug: WSL2's `/tmp` tmpfs Ceiling (1.8G) Silently Capped pip Installs Despite 952G Free on Disk
**Phase:** B1
**Date:** 28-07-2026

**What was found:** After fixing the CUDA-dependency issue above, the same `OSError: [Errno 28] No space left on device` recurred on a retry, despite `df -h /` showing 952G available on the actual filesystem. Root cause, found by checking `df -h /tmp` specifically: WSL2 mounts `/tmp` as `tmpfs` — a RAM-backed filesystem, capped at 1.8G, entirely separate from the 952G root filesystem. pip downloads wheel files into `/tmp` before installing them; several multi-hundred-MB downloads in flight simultaneously exhausted the 1.8G tmpfs ceiling, a limit invisible to `df -h /` because it's a different mount point.

**Fix:** Redirected pip's temp directory to the regular (non-tmpfs) filesystem for the session: `export TMPDIR=/home/nithin/pip_tmp` (with the directory created first via `mkdir -p`). Combined with the CPU-only torch fix above, the subsequent install completed without error.

**Why this matters:** `df -h /` reporting hundreds of gigabytes free was actively misleading about the real constraint — a classic case of checking the wrong metric and trusting a plausible-looking number instead of verifying the specific failure point. The fix required understanding WSL2's mount architecture (tmpfs vs. the main ext4 filesystem), not just retrying or clearing generic caches.

**Interview angle:** *"I hit a disk-space error that made no sense — my filesystem showed 952 gigabytes free, but the install kept failing with 'no space left on device.' The actual constraint was a completely different, much smaller filesystem: WSL2 mounts /tmp as a RAM-backed tmpfs capped at 1.8 gigabytes, invisible to a plain 'df -h /' check on the root filesystem. I found it by checking /tmp specifically instead of assuming the first plausible number I saw was the real bottleneck, then fixed it by redirecting pip's temp directory to the regular filesystem."*