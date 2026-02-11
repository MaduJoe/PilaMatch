# CLAUDE_RUNBOOK.md
## Claude Code Execution Manual – Python MVP Implementation

This document is a complete step-by-step execution script to implement the Pilates & Yoga Matching Platform MVP using Claude Code.

Follow the steps EXACTLY in order.

---

# PREPARATION

Before starting, prepare:

- CLAUDE_CONTEXT_PACKAGE.md (already created)
- All PRD/API/DB documents included in that package

---

# STEP 0 – LOAD CONTEXT (RUN ONCE)

Run this FIRST:

Load and follow this context package strictly:

<PASTE CLAUDE_CONTEXT_PACKAGE.md HERE>

Rules:
- Implement step-by-step only.
- Never implement future modules early.
- Output code only unless explanation is explicitly requested.
- Do not modify API/DB design unless instructed.

---

# STEP 1 – PROJECT SKELETON

Prompt:

Step 1: Generate the full project skeleton for FastAPI + Streamlit.

Requirements:
- Separate backend/ and frontend/
- FastAPI async architecture
- SQLAlchemy + Alembic
- Pydantic schemas
- WebSocket support
- Environment configuration
- Docker support

Deliverables:
- Folder structure
- requirements.txt
- backend/app/main.py
- configuration files
- Dockerfile and docker-compose.yml
- README.md

Important:
- Do NOT implement business logic yet.

---

# STEP 2 – DATABASE LAYER

Prompt:

Step 2: Implement database layer exactly according to the DB schema.

Create:

- SQLAlchemy models
- Enums
- Session management
- Alembic setup
- Initial migration

Requirements:
- UUID primary keys
- PostgreSQL enums
- All indexes and constraints from design
- Proper relationships

Output:
- models files
- enums file
- alembic initial migration script

---

# STEP 3 – AUTH MODULE

Prompt:

Step 3: Implement Authentication module.

Endpoints:
- POST /api/v1/auth/signup
- POST /api/v1/auth/login
- GET  /api/v1/auth/me

Requirements:
- JWT authentication
- Password hashing
- Role-based access
- Dependency injection for current user

Output:
- routers
- services
- schemas
- security utilities

---

# STEP 4 – PROFILE MODULES

Prompt:

Step 4: Implement Instructor and Studio Profiles.

Endpoints:

Instructor:
- GET/PUT /api/v1/instructors/me
- GET     /api/v1/instructors/{id}

Studio:
- GET/PUT /api/v1/studios/me
- GET     /api/v1/studios/{id}

Requirements:
- Validation
- Role permissions
- Clean DTO responses

---

# STEP 5 – JOB POST MODULE

Prompt:

Step 5: Implement JobPost module.

Endpoints:
- POST   /api/v1/job-posts
- GET    /api/v1/job-posts
- GET    /api/v1/job-posts/{id}
- PUT    /api/v1/job-posts/{id}
- DELETE /api/v1/job-posts/{id}

Requirements:
- Filtering
- Sorting
- Studio ownership rules

---

# STEP 6 – APPLICATION MODULE

Prompt:

Step 6: Implement Application module.

Endpoints:
- POST /job-posts/{id}/applications
- GET  /applications/me
- POST /applications/{id}/withdraw

Rules:
- Prevent duplicate applications
- Validate permissions
- Proper error codes

---

# STEP 7 – OFFER + CONTRACT MODULE (CRITICAL)

Prompt:

Step 7: Implement Offer and Contract modules with strict state machine.

You MUST enforce:

- All transitions from STATE TRANSITION TABLE
- Transactional integrity
- Event logging for every transition
- Cancellation rules
- Payment requirements

Endpoints include:

Offers:
- POST /offers
- GET  /offers/me
- POST /offers/{id}/accept
- POST /offers/{id}/reject

Contracts:
- POST /contracts/from-offer/{id}
- GET  /contracts/me
- POST /contracts/{id}/set-in-progress
- POST /contracts/{id}/complete
- POST /contracts/{id}/cancel

Output:
- Services with validations
- Routers
- Event logs

---

# STEP 8 – PAYMENT MODULE

Prompt:

Step 8: Implement Payment and Payout modules.

Endpoints:
- POST /contracts/{id}/payments
- POST /payments/webhook

Requirements:
- TossPayments integration
- Idempotent webhook handling
- Payment → Contract status linkage
- Payout creation on completion

---

# STEP 9 – CHAT SYSTEM

Prompt:

Step 9: Implement Chat module.

Features:
- Thread-based chat
- Contract or Job scope
- WebSocket realtime
- System messages

Endpoints:
- POST /threads
- GET  /threads
- POST /threads/{id}/messages
- WS   /ws/threads/{id}

---

# STEP 10 – REVIEW / REPORT / SUPPORT

Prompt:

Step 10: Implement supporting modules.

Reviews:
- POST /contracts/{id}/reviews

Reports:
- POST /reports

Blocks:
- POST /blocks
- GET  /blocks/me

Support:
- POST /support/tickets
- GET  /support/tickets/me

---

# STEP 11 – STREAMLIT FRONTEND

Prompt:

Step 11: Build Streamlit frontend consuming the FastAPI backend.

Screens:

- Login / Signup
- Job exploration
- Job detail + apply
- My activity dashboard
- Chat
- Profile management

Requirements:
- Mobile friendly
- Token-based API calls
- Clean minimal UI

---

# STEP 12 – PWA & DEPLOYMENT

Prompt:

Step 12: Provide deployment setup.

Include:

- Docker configuration
- Render/Railway deployment guide
- .env.example
- Streamlit PWA approach

---

# STEP 13 – TESTS

Prompt:

Step 13: Create pytest test suite.

Coverage:

- Auth
- Job posts
- Applications
- Offers
- Contracts
- Payment webhook

---

# TROUBLESHOOTING COMMANDS

If Claude Code deviates, use:

Reset Command:

Stop. Follow the context package strictly.  
Implement only the current step.  
Output only the required files.

If over-implementing:

Do NOT implement next modules.  
Revert to the scope of this step only.

If broken code:

Fix only the errors in the current module without adding new features.

---

# GENERAL RULES

- Small steps only
- Never skip state validation
- No hardcoded secrets
- Clean Python typing
- Always follow API spec

---

END OF RUNBOOK
