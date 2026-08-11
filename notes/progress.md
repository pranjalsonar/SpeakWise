SpeakWise - Backend Development Notes
Progress Log (Sprint 1 & Sprint 2)
Last Updated: 11 August 2026
Project Overview
SpeakWise is an AI-powered Public Speaking Coach that analyzes:
Speech content
Voice characteristics
Eye contact
Hand gestures
Body posture
Facial expressions
The backend is being developed using FastAPI, following a layered architecture to keep the project scalable and maintainable.
Current Backend Architecture
Client
    │
    ▼
FastAPI Routes
    │
    ▼
Service Layer
    │
    ▼
CRUD Layer
    │
    ▼
SQLAlchemy ORM
    │
    ▼
PostgreSQL
Each layer has a single responsibility.
Folder Structure
backend/
│
├── app/
│   │
│   ├── api/
│   │    └── routes/
│   │          ├── health.py
│   │          ├── speech.py
│   │          ├── users.py
│   │          └── auth.py
│   │
│   ├── auth/
│   │      ├── hashing.py
│   │      └── jwt_handler.py
│   │
│   ├── core/
│   │      └── config.py
│   │
│   ├── crud/
│   │      └── user.py
│   │
│   ├── db/
│   │      ├── database.py
│   │      └── session.py
│   │
│   ├── models/
│   │      └── user.py
│   │
│   ├── schemas/
│   │      ├── speech.py
│   │      ├── user.py
│   │      └── auth.py
│   │
│   ├── services/
│   │      ├── speech_service.py
│   │      ├── user_service.py
│   │      └── auth_service.py
│   │
│   └── main.py
│
├── requirements.txt
├── .env
└── README.md
Sprint 1 - Backend Foundation
Completed
FastAPI Setup
Created the FastAPI application.
Configured:
Project Name
Version
Host
Port
Swagger documentation available at:
/docs
Configuration Management
Introduced:
app/core/config.py
Purpose:
Centralize application configuration.
Load environment variables from .env.
Current configuration:
Project Name
Version
Host
Port
JWT Secret
JWT Algorithm
JWT Expiry
Health Endpoint
Implemented a simple health route to verify the backend is operational.
Speech Endpoint
Created the initial speech route and service.
At present, this is a placeholder used to validate API architecture.
Future versions will integrate Whisper and AI analysis.
Service Layer
Business logic is separated from routes.
Routes never contain business logic.
Schemas
Implemented Pydantic schemas for request and response validation.
Sprint 2 - Database Integration
PostgreSQL
Installed:
PostgreSQL 17
pgAdmin 4
Created database:
speakwise_db
SQLAlchemy
Installed:
SQLAlchemy
Alembic
psycopg2
Connected FastAPI to PostgreSQL.
Database Layer
Created:
database.py
Contains:
Engine
SessionLocal
Base
Session Management
Created:
session.py
Purpose:
Open database connection
Yield session
Automatically close session
Uses FastAPI dependency injection.
Models
Created first SQLAlchemy model:
User
Fields:
id
name
email
password
Automatic Table Creation
Current implementation:
Base.metadata.create_all()
Used only during development.
Future production version will use Alembic migrations.
CRUD Layer
Created:
crud/user.py
Responsibilities:
Retrieve user by email
Create user
No business logic exists in CRUD.
CRUD only communicates with the database.
User Schemas
Created:
UserCreate
UserResponse
Important design decision:
Passwords are never returned by the API.
User Registration
Implemented:
POST /users/register
Flow:
Client

↓

Validation

↓

Service

↓

CRUD

↓

PostgreSQL
Implemented:
Duplicate email detection
User insertion
Response model
Password Security
Initially passwords were stored as plain text.
This was replaced with bcrypt hashing.
Created:
auth/hashing.py
Functions:
hash_password()
verify_password()
Passwords are now hashed before storage.
Dependency Issue Resolved
Encountered compatibility issue:
passlib 1.7.4
with
bcrypt 5.0.0
Resolution:
Downgraded bcrypt to:
bcrypt==4.0.1
Recommendation:
Pin dependency versions inside requirements.txt.
Authentication Module
Created:
auth/jwt_handler.py
Responsibilities:
JWT creation
Expiry
Signing
Configuration loaded from:
.env
instead of hardcoding secrets.
Login Schemas
Created:
LoginRequest

Token
Used for authentication APIs.
Authentication Service
Created:
auth_service.py
Responsibilities:
Verify email
Verify hashed password
Generate JWT
Return access token
Authentication Route
Created:
POST /auth/login
Flow:
Client

↓

Find User

↓

Verify Password

↓

Generate JWT

↓

Return Access Token
Current Backend Capabilities
✔ FastAPI
✔ Swagger Documentation
✔ PostgreSQL
✔ SQLAlchemy ORM
✔ Layered Architecture
✔ Environment Configuration
✔ User Registration
✔ Duplicate Email Validation
✔ Password Hashing
✔ JWT Generation
✔ Login Endpoint
Architecture Principles
The project follows strict separation of concerns.
Routes
Responsible only for:
Receiving requests
Returning responses
No business logic.
Services
Responsible for:
Business rules
Validation
Authentication
Password hashing
No SQL queries.
CRUD
Responsible only for:
Database operations
No validation or business logic.
Models
Represent database tables.
Schemas
Represent request/response payloads.
Next Sprint
Authentication Completion
Remaining:
JWT verification
Protected routes
Current authenticated user
Logout
Refresh token (optional)