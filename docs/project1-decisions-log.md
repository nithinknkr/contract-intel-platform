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