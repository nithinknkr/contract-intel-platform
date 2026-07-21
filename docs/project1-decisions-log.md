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