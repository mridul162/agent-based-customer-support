<div align="center">

# Agent-Based Customer Support

### Production-Ready Multi-Agent AI Customer Support Platform

A production-grade multi-agent customer support platform built with **FastAPI**, **LangGraph**, **PostgreSQL**, **OpenAI**, **RAG**, **Docker**, and **GitHub Actions CI** — demonstrating modern AI engineering practices including structured tool calling, agent routing, knowledge retrieval, evaluation pipelines, and clean layered architecture.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)]()
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1--mini-412991.svg)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blueviolet.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)]()
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-2088FF.svg)]()
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

</div>

---

## Overview

This project demonstrates how to build a **production-ready multi-agent customer support platform** using modern AI engineering practices. The system routes customer requests to specialized LangGraph agents, performs structured tool calling, retrieves knowledge through RAG, persists business data in PostgreSQL, exposes a FastAPI REST backend, provides a Streamlit operations dashboard, and includes an automated evaluation framework and CI pipeline.

Rather than focusing solely on prompt engineering, this project emphasizes **building AI systems as production-quality software** — with layered architecture, dependency injection, repository patterns, observability, and continuous evaluation.

---

## Multi-Agent Architecture

```
                        Customer
                            │
                            ▼
                    FastAPI REST API
                            │
                            ▼
                    Escalation Detection
                      (pre-routing gate)
                            │
                   ┌────────┴────────┐
                   │                 │
                   ▼                 ▼
           Router Graph        Escalation Agent
                   │
      ┌────────────┼────────────┬─────────────┐
      │            │            │             │
      ▼            ▼            ▼             ▼
 Ticket Agent  FAQ Agent  Order Agent  Escalation Agent
      │            │            │
      ▼            ▼            ▼
   Ticket       RAG /       Order
    Tools     Knowledge     Tools
      │          Tools         │
      └──────────┬─────────────┘
                 │
                 ▼
          PostgreSQL + Vector Store
```

### Specialist Agents

| Agent | Responsibility |
|---|---|
| **Router Agent** | Reads customer message, selects the correct specialist agent via LLM |
| **Ticket Agent** | Creates, retrieves, and updates support tickets |
| **Order Agent** | Handles order status, cancellation, address updates, and delivery estimates |
| **FAQ Agent** | Answers policy and product questions using RAG knowledge retrieval |
| **Escalation Agent** | Routes complex or sensitive cases directly to human support |

---

## System Architecture

The platform follows a strict layered architecture ensuring business logic is isolated from infrastructure concerns:

```
API (FastAPI)
      │
      ▼
Router Graph (LangGraph)
      │
      ▼
Specialist Agents
      │
      ▼
Nodes (Decision → Extraction → Validation → Execution → Response)
      │
      ▼
Tools (thin adapters)
      │
      ▼
Services (business rules)
      │
      ▼
Repositories (data access)
      │
      ▼
PostgreSQL
```

### Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **API** | HTTP endpoints, request validation, response serialisation |
| **Router Graph** | Intent routing, memory loading/writing, escalation detection |
| **Agent Nodes** | LLM decision, argument extraction, validation, tool execution, response building |
| **Tools** | Thin adapters — no business logic, delegate to services |
| **Services** | Business rules, transaction boundaries, workflow orchestration |
| **Repositories** | Database interaction only — never call commit/rollback |
| **PostgreSQL** | Persistent storage for tickets, orders, escalations, conversations |

---

## Features

### AI Capabilities

- Multi-Agent Architecture (Router + Specialist Agents)
- LangGraph Graph Orchestration
- Agent Routing with pre-routing escalation detection
- Structured Tool Calling via `ToolSpec` registry
- OpenAI Structured Outputs (Pydantic model parsing)
- Retrieval-Augmented Generation (RAG)
- Semantic vector search with FAISS
- OpenAI Embeddings pipeline
- Conversation Memory across turns
- Argument extraction from natural language (regex + memory fallback)
- Argument validation with targeted clarification prompts
- Prompt Engineering (modular, file-separated prompts)

### Customer Support Features

#### Order Management
- Order status lookup
- Order cancellation (with business-rule validation)
- Delivery address update
- Delivery time estimation

#### Ticket Management
- Create support ticket
- Retrieve ticket by ID
- Update ticket status
- List customer tickets

#### Escalation
- Rule-based escalation detection (legal, safety, fraud, human-request)
- Human escalation creation with queue routing
- Escalation tracking and persistence

#### Knowledge Retrieval
- FAQ answers
- Shipping policy questions
- Return and refund policy
- Product information
- Payment policy

### Engineering Features

- FastAPI REST API with OpenAPI/Swagger documentation
- PostgreSQL with SQLAlchemy ORM
- Dependency Injection via FastAPI `Depends()`
- Repository Pattern (no SQL in services)
- `get_session()` context manager (commit/rollback/close ownership)
- `ToolSpec` registry — single source of truth for all tools
- Pydantic schemas (request/response/state contracts)
- Structured logging with `request_id` context across all nodes
- Observability layer (execution traces, node timing, LLM metrics)
- Automated evaluation framework (dataset-driven, multi-dimensional)
- Docker & Docker Compose
- GitHub Actions CI pipeline
- Render deployment

---

## Available Tools

| Tool | Purpose |
|---|---|
| `create_ticket_tool` | Create a new support ticket |
| `get_ticket_tool` | Retrieve ticket by ID |
| `update_ticket_tool` | Update ticket status or response |
| `list_ticket_tool` | List all tickets for a customer |
| `get_order_status_tool` | Retrieve order status and details |
| `cancel_order_tool` | Cancel a PROCESSING or SHIPPED order |
| `update_delivery_address_tool` | Update delivery address for PROCESSING orders |
| `estimate_delivery_time_tool` | Estimate delivery date based on order status |
| `retrieve_knowledge_tool` | RAG-based knowledge base retrieval |
| `create_escalation_tool` | Create a human escalation with queue routing |
| `get_escalation_tool` | Retrieve escalation by ID |

All tools are registered in `TOOL_REGISTRY` via `ToolSpec` — adding a new tool requires editing one file only.

---

## RAG Pipeline

```
Knowledge Base (Markdown files)
         │
         ▼
    Document Parsing
         │
         ▼
    Normalisation
         │
         ▼
    Chunking
         │
         ▼
    OpenAI Embeddings
         │
         ▼
    FAISS Vector Store
         │
         ▼
    Semantic Retrieval
         │
         ▼
    LLM Grounded Answer
```

Knowledge sources:
- FAQ
- Shipping policies
- Return & refund policies
- Payment information
- Product information

---

## Evaluation Framework

The project includes a modular, dataset-driven evaluation framework that evaluates each AI capability independently.

### Evaluation Dimensions

| Dimension | Metric | Target |
|---|---|---|
| **Routing Accuracy** | Correct specialist agent selected | ≥ 95% |
| **Tool Selection Accuracy** | Correct tool chosen | ≥ 95% |
| **Tool Success Rate** | Tool executed without failure | ≥ 99% |
| **Retrieval Relevance** | Relevant context retrieved | ≥ 90% |
| **Response Correctness** | Final response satisfies expectation | ≥ 90% |
| **Average Latency** | Total response time | < 3 seconds |
| **Error Rate** | Failed requests | < 2% |

### Evaluation Datasets

| Dataset | Cases | Covers |
|---|---|---|
| `routing.json` | 15 | Agent routing, escalation detection |
| `tool_selection.json` | 15 | Tool choice, clarification triggers |
| `retrieval.json` | 15 | RAG relevance, fallback behaviour |
| `workflow.json` | 15 | End-to-end flows, memory recovery, persistence |

Evaluation runs as a manual GitHub Actions workflow — triggerable on demand without affecting production.

---

## Observability

Every request is fully traceable:

- `request_id` generated per request, flows through all graph nodes
- Structured logs with `request_id` and `customer_id` in every node
- Node execution timing (ms per node)
- LLM call metrics (latency, token usage, estimated cost)
- Tool execution success/failure tracking
- Execution traces stored per request

---

## CI/CD Pipeline

```
Push to Repository
        │
        ▼
GitHub Actions
        │
   ┌────┴────────────────┐
   │                     │
   ▼                     ▼
Install & Lint       Run Tests
(Ruff + imports)    (unit tests)
        │
        ▼
  Build Docker Images
        │
        ▼
  (Optional) Deploy to Render
```

Manual workflow:
- Run multi-agent evaluation suite

---

## Docker Support

```bash
# Start all services
docker-compose up --build

# Services started:
#   FastAPI backend   → http://localhost:8000
#   Streamlit dashboard → http://localhost:8501
#   PostgreSQL        → localhost:5432
```

Separate Docker images for:
- FastAPI backend
- Streamlit frontend

---

## Project Structure

```
agent-based-customer-support/
│
├── app/
│   ├── agents/          # SupportAgent facade, IntentClassifier
│   ├── api/             # FastAPI routes, dependencies
│   ├── config/          # Settings, environment management
│   ├── database/        # SQLAlchemy engine, get_session(), init_db
│   ├── graphs/          # LangGraph compiled graphs (router, react, escalation)
│   ├── llm/             # OpenAI client factory
│   ├── models/          # SQLAlchemy ORM models
│   ├── nodes/           # LangGraph nodes (decision, extraction, validation, etc.)
│   ├── observability/   # Metrics, execution tracing, timers
│   ├── prompts/         # Modular prompt files
│   ├── rag/             # RAG pipeline (chunking, embeddings, retrieval)
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic contracts (state, request, response)
│   ├── services/        # Business logic layer
│   ├── tools/           # Tool functions + ToolSpec registry
│   └── main.py          # FastAPI app factory + structured logging
│
├── evaluation/
│   ├── datasets/        # routing.json, tool_selection.json, retrieval.json, workflow.json
│   ├── evaluators/      # Per-dimension evaluators
│   ├── runners/         # Evaluation pipeline runners
│   ├── reports/         # Generated evaluation reports
│   └── metrics.py       # Metric definitions and success targets
│
├── knowledge_base/
│   ├── faq/
│   ├── payments/
│   ├── policies/
│   ├── products/
│   ├── returns/
│   └── shipping/
│
├── tests/               # Validation scripts per milestone
├── scripts/             # Utility scripts (seed data, etc.)
├── docker/              # Dockerfiles
├── docs/                # Architecture docs
└── requirements/
```

---

## Technology Stack

### Backend
- **Python 3.12+**
- **FastAPI** — REST API, dependency injection
- **PostgreSQL** — persistent storage
- **SQLAlchemy** — ORM, session management
- **Pydantic** — schema validation and structured outputs

### AI
- **OpenAI GPT-4.1-mini** — LLM for decisions, extraction, generation
- **LangGraph** — multi-agent graph orchestration
- **Structured Outputs** — Pydantic model parsing via OpenAI API
- **Tool Calling** — registry-driven tool execution

### Retrieval
- **FAISS** — vector similarity search
- **OpenAI Embeddings** — document and query embeddings
- **RAG Pipeline** — parse → normalise → chunk → embed → retrieve → generate

### Frontend
- **Streamlit** — operations dashboard (chat, tickets, health, evaluation)

### DevOps
- **Docker + Docker Compose** — containerised deployment
- **GitHub Actions** — CI (lint, test, build, evaluate)
- **Render** — cloud deployment

---

## Getting Started

**Clone the repository**

```bash
git clone https://github.com/mridul162/agent-based-customer-support.git
cd agent-based-customer-support
```

**Create and activate virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

**Install dependencies**

```bash
pip install -r requirements/requirements.txt
```

**Configure environment variables**

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/customer_support
APP_ENV=development
OPENAI_MODEL=gpt-4o-mini
```

**Initialise the database**

```bash
python -m app.database.init_db
```

**Run the application**

```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

**Run with Docker**

```bash
docker-compose up --build
```

---

## Roadmap

### Completed ✅

- Multi-agent architecture (Router + Specialist Agents)
- LangGraph graph orchestration
- Structured tool calling via `ToolSpec` registry
- FastAPI REST backend with dependency injection
- PostgreSQL persistence (tickets, orders, escalations, conversations)
- Repository pattern with `get_session()` transaction management
- Conversation memory across turns
- Argument extraction from natural language
- Argument validation with clarification prompts
- Rule-based escalation detection (legal, safety, fraud)
- RAG pipeline (parse → chunk → embed → retrieve → generate)
- Evaluation framework with dataset-driven benchmarks
- Observability layer (traces, timing, LLM metrics)
- Structured logging with `request_id` propagation
- Streamlit operations dashboard
- Docker + Docker Compose
- GitHub Actions CI pipeline
- Render deployment

### In Progress 🔄

- Expanded evaluation datasets
- Conversation analytics
- Additional knowledge base documents

### Planned 📋

- Authentication & multi-tenant support
- Admin dashboard
- Production monitoring (OpenTelemetry / LangSmith)
- Performance benchmarking
- Continuous deployment pipeline
- Web chat frontend

---

## What This Project Demonstrates

| Domain | Skills |
|---|---|
| **AI Engineering** | Multi-agent systems, LLM tool calling, RAG, structured outputs, prompt engineering |
| **Backend Engineering** | FastAPI, SQLAlchemy, PostgreSQL, dependency injection, repository pattern |
| **Software Architecture** | Layered architecture, separation of concerns, SOLID principles |
| **Evaluation Engineering** | Dataset-driven evaluation, metric definition, regression testing |
| **DevOps** | Docker, Docker Compose, GitHub Actions CI, cloud deployment |
| **Observability** | Request tracing, structured logging, execution metrics |
| **Production Thinking** | Transaction management, session lifecycle, graceful degradation, escalation flows |

---

## About the Author

**Asifur Rahman Mridul**

Electronics & Communication Engineering Graduate from KUET with a focus on AI Engineering, Large Language Models, Retrieval-Augmented Generation, MLOps, and scalable backend systems.

I enjoy building AI systems that combine sound software engineering principles with modern LLM technologies — systems that are not just functional, but observable, testable, and maintainable.

**GitHub:** [github.com/mridul162](https://github.com/mridul162)

**LinkedIn:** [linkedin.com/in/asifmridul](https://www.linkedin.com/in/asifmridul)

---

## License

This project is released under the [MIT License](LICENSE).