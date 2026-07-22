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