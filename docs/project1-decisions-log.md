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