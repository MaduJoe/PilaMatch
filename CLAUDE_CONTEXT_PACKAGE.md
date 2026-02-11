# CLAUDE_CONTEXT_PACKAGE.md
## Pilates & Yoga Matching Platform – Claude Code Instruction Package

---

# 1. ROLE & INSTRUCTIONS

You are a senior Python full-stack engineer.

Your mission is to implement an MVP for a Pilates & Yoga instructor matching platform strictly according to the documents provided in this package.

## 1.1 Technology Stack

You MUST follow this stack:

- Backend: Python FastAPI (async)
- Frontend: Streamlit (PWA style)
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Realtime: FastAPI WebSocket
- Payment: TossPayments (Korea)
- Deployment: Render / Railway

## 1.2 Implementation Principles

- Follow the PRD exactly
- Follow the API specification exactly
- Enforce the state transition rules strictly
- All state changes must be logged
- Idempotent payment processing is mandatory
- Role-based permission checks are mandatory
- Write clean, modular Python code

---

# 2. PRODUCT OVERVIEW (PRD SUMMARY)

## 2.1 Product Vision

A platform that connects Pilates/Yoga instructors and studios, enabling the entire workflow—matching, confirmation, cancellation, payment, and review—inside the application without external communication.

## 2.2 Target Users

- Studio Managers
- Instructors

## 2.3 Market Scope

- Korea only
- Categories: Pilates, Yoga

## 2.4 Core Value

- Closed-loop workflow
- Structured cancellation process
- Built-in payment and settlement
- Trust-based review system

---

# 3. CORE WORKFLOWS

## 3.1 Job Post Based Flow

1. Studio creates job post  
2. Instructor applies  
3. Studio sends offer  
4. Instructor accepts  
5. Contract confirmed  
6. Studio pays  
7. Class completed  
8. Settlement & review  

## 3.2 Profile Based Flow

1. Instructor publishes profile  
2. Studio sends direct offer  
3. Instructor accepts  
4. Same flow as above  

---

# 4. API SPECIFICATION (SUMMARY)

## 4.1 Auth APIs

POST /auth/signup  
POST /auth/login  
GET  /auth/me  

## 4.2 Profiles

GET/PUT  /instructors/me  
GET      /instructors/{id}  

GET/PUT  /studios/me  
GET      /studios/{id}  

## 4.3 Job Posts

POST   /job-posts  
GET    /job-posts  
GET    /job-posts/{id}  
PUT    /job-posts/{id}  
DELETE /job-posts/{id}  

## 4.4 Applications

POST /job-posts/{id}/applications  
GET  /applications/me  
POST /applications/{id}/withdraw  

## 4.5 Offers

POST /offers  
GET  /offers/me  
POST /offers/{id}/accept  
POST /offers/{id}/reject  

## 4.6 Contracts

POST /contracts/from-offer/{id}  
GET  /contracts/me  
POST /contracts/{id}/set-in-progress  
POST /contracts/{id}/complete  
POST /contracts/{id}/cancel  

## 4.7 Payment

POST /contracts/{id}/payments  
POST /payments/webhook  

## 4.8 Chat

POST /threads  
GET  /threads  
POST /threads/{id}/messages  

## 4.9 Reviews

POST /contracts/{id}/reviews  

---

# 5. DATABASE DESIGN

Core entities:

- users
- instructor_profiles
- studio_profiles
- job_posts
- applications
- offers
- contracts
- contract_event_logs
- payments
- payouts
- chat_threads
- chat_messages
- reviews
- reports
- blocks
- support_tickets

### Key Rules

- UUID primary keys  
- PostgreSQL enums  
- All contract transitions logged  
- Unique constraints on:
  - applications(job_post_id, instructor_user_id)
  - reviews(contract_id, reviewer_user_id)

---

# 6. STATE TRANSITION RULES

## 6.1 Contract Statuses

APPLICATION → OFFER → CONFIRMED → IN_PROGRESS → COMPLETED  
                                      ↘ CANCELLED  

## 6.2 Core Rules

- Only valid transitions allowed  
- Every transition must create ContractEventLog  
- Payment must succeed before IN_PROGRESS  
- Cancellation requires reason  
- No transition allowed after CANCELLED or COMPLETED  

---

# 7. ERROR HANDLING REQUIREMENTS

### Must Implement

- INVALID_STATE_TRANSITION  
- PAYMENT_REQUIRED  
- DUPLICATE_APPLICATION  
- OFFER_NOT_PENDING  
- CONTRACT_NOT_IN_PROGRESS  
- CANCEL_REASON_REQUIRED  

All errors must return structured JSON:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
