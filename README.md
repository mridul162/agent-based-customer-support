<div align="center">

# Agent-Based Customer Support

### Production-Oriented AI Customer Support Platform

A modular AI customer support platform built with **FastAPI**, **PostgreSQL**, **OpenAI**, **LangGraph**, and **Retrieval-Augmented Generation (RAG)** that demonstrates modern AI Engineering practices including tool calling, structured outputs, observability, evaluation pipelines, and clean backend architecture.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)]()
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1--mini-412991.svg)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-blueviolet.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

</div>

---

# Overview

Modern customer support systems require far more than simply generating text with an LLM. They need structured business logic, reliable tool execution, knowledge retrieval, observability, and continuous evaluation.

This project demonstrates how to engineer an AI-powered customer support platform using modern backend engineering principles while keeping the AI components modular, testable, and maintainable.

The system combines:

- Large Language Models
- Tool Calling
- Retrieval-Augmented Generation (RAG)
- PostgreSQL
- LangGraph
- Clean Service/Repository Architecture
- Evaluation Framework
- Observability

Rather than focusing solely on prompt engineering, this project emphasizes **building AI systems as production-quality software**.

---

# Features

## AI Capabilities

- OpenAI GPT-4.1-mini integration
- Tool Calling
- Structured Outputs
- Prompt Engineering
- LangGraph workflow orchestration
- Retrieval-Augmented Generation (RAG)
- Knowledge Base retrieval
- Embedding pipeline
- Vector search

---

## Customer Support Features

- Order Status
- Order Cancellation
- Delivery Address Update
- Delivery Estimation
- Ticket Creation
- Ticket Retrieval
- Ticket Update
- Ticket Listing
- Escalation Creation
- Escalation Tracking
- Knowledge Retrieval

---

## Engineering Features

- FastAPI REST API
- PostgreSQL
- SQLAlchemy ORM
- Dependency Injection
- Repository Pattern
- Service Layer
- Pydantic Schemas
- Configuration Management
- Modular Architecture
- Logging
- Observability
- Evaluation Framework

---

# System Architecture

```text
                        Customer
                            │
                            ▼
                     FastAPI Endpoint
                            │
                            ▼
                     Support Agent
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
      LangGraph Workflow             Observability
            │                               │
            ▼                               ▼
      Tool Selection                  Metrics / Logs
            │
            ▼
      Tool Execution
            │
      ┌─────┴─────────────┐
      │                   │
      ▼                   ▼
 Service Layer       RAG Pipeline
      │                   │
      ▼                   ▼
Repository Layer    Knowledge Base
      │
      ▼
 PostgreSQL
```

---

# Project Structure

```text
agent-based-customer-support
│
├── app
│   ├── agents
│   ├── api
│   ├── config
│   ├── database
│   ├── graphs
│   ├── llm
│   ├── mappers
│   ├── models
│   ├── nodes
│   ├── observability
│   ├── prompts
│   ├── rag
│   ├── repositories
│   ├── schemas
│   ├── services
│   ├── tools
│   └── main.py
│
├── artifacts
│   ├── parsed
│   ├── normalized
│   ├── chunked
│   ├── embeddings
│   └── pipeline_logs
│
├── evaluation
│   ├── datasets
│   ├── evaluators
│   ├── interfaces
│   ├── pipelines
│   ├── reports
│   ├── runners
│   ├── metrics.py
│   └── report_generator.py
│
├── knowledge_base
│   ├── faq
│   ├── payments
│   ├── policies
│   ├── products
│   ├── returns
│   └── shipping
│
├── docs
├── docker
├── scripts
├── tests
└── requirements
```

---

# Architecture Highlights

The project follows a layered architecture to keep business logic isolated from infrastructure concerns.

```
API
 │
 ▼
Agent
 │
 ▼
Tool
 │
 ▼
Service
 │
 ▼
Repository
 │
 ▼
Database
```

### Responsibilities

### API

- HTTP endpoints
- Request validation
- Response serialization

### Agent

- Understand user requests
- Decide which tool to invoke
- Coordinate workflow

### Tools

- Thin execution layer
- No business logic
- Delegate work to services

### Services

- Business rules
- Validation
- Workflow orchestration

### Repository

- Database interaction
- Persistence abstraction

---

# Available Tools

| Tool | Purpose |
|-------|----------|
| get_order_status_tool | Retrieve order status |
| cancel_order_tool | Cancel an order |
| update_delivery_address_tool | Update shipping address |
| estimate_delivery_time_tool | Delivery estimation |
| retrieve_knowledge_tool | RAG-based knowledge retrieval |
| create_ticket_tool | Create support ticket |
| get_ticket_tool | Retrieve ticket |
| update_ticket_tool | Update ticket |
| list_ticket_tool | List customer tickets |
| create_escalation_tool | Create escalation |
| get_escalation_tool | Retrieve escalation |

---

# Retrieval-Augmented Generation

The project includes a modular RAG pipeline.

Pipeline:

```
Knowledge Base
      │
      ▼
Parsing
      │
      ▼
Normalization
      │
      ▼
Chunking
      │
      ▼
Embeddings
      │
      ▼
Vector Store
      │
      ▼
Semantic Retrieval
      │
      ▼
LLM Response
```

Knowledge sources include:

- FAQ
- Shipping
- Policies
- Payments
- Products
- Returns

---

# Evaluation Framework

One of the core goals of this project is to evaluate AI behavior rather than relying solely on manual testing.

The evaluation module currently supports:

- Dataset-driven evaluation
- Tool selection benchmarking
- Metrics aggregation
- Human-readable reports
- Latency measurement
- Failure analysis

Current evaluation datasets include scenarios such as:

- Order management
- Ticket management
- Knowledge retrieval
- Clarification requests
- Conversation memory
- Unsupported requests

This evaluation framework enables regression testing as new capabilities are added.

---

# Observability

The platform includes an observability layer to make AI workflows easier to inspect and debug.

Examples include:

- Execution tracing
- Node execution timing
- Tool execution metrics
- LLM execution metrics
- Pipeline logging

---

# Technology Stack

## Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic

## AI

- OpenAI GPT-4.1-mini
- LangGraph
- Tool Calling
- Structured Outputs
- Prompt Engineering

## Retrieval

- RAG
- Embeddings
- Vector Database

## Engineering

- Dependency Injection
- Repository Pattern
- Service Layer
- Evaluation Framework
- Observability

---

# Getting Started

Clone the repository

```bash
git clone https://github.com/mridul162/agent-based-customer-support.git

cd agent-based-customer-support
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Configure environment variables

```env
OPENAI_API_KEY=your_openai_key
DATABASE_URL=your_postgresql_url
```

Run the application

```bash
python -m app.main
```

---

# Roadmap

Completed

- FastAPI backend
- PostgreSQL integration
- SQLAlchemy ORM
- Tool Calling
- LangGraph workflow
- RAG pipeline
- Evaluation framework
- Observability
- Knowledge Base
- Modular architecture

In Progress

- Workflow improvements
- Expanded evaluation datasets
- Additional AI capabilities

Planned

- Multi-Agent architecture
- Web dashboard
- Authentication & authorization
- Conversation analytics
- Production deployment
- CI/CD pipeline
- Performance benchmarking

---

# What This Project Demonstrates

This project showcases practical experience in:

- AI Engineering
- Backend Engineering
- LLM Application Development
- Retrieval-Augmented Generation
- Software Architecture
- Database Design
- Evaluation Methodologies
- Observability
- API Development
- Production-oriented AI system design

---

# About the Author

**Asifur Rahman Mridul**

Electronics & Communication Engineering Graduate from KUET with a focus on AI Engineering, Large Language Models, Retrieval-Augmented Generation, MLOps, and scalable backend systems.

I enjoy building AI applications that combine sound software engineering principles with modern LLM technologies.

**GitHub:** https://github.com/mridul162

**LinkedIn:** *(Add your LinkedIn profile here.)*

---

# License

This project is released under the MIT License.