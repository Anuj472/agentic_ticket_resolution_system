# 🤖 Agentic Ticket System

A production-grade, human-in-the-loop AI ticketing system built with **FastAPI**, **Next.js**, and **LangGraph**. This system automates ticket classification, resolution suggestion, and routing while maintaining a strict 90% confidence threshold for human intervention.

## 🌟 Key Features

- **6-Node Agentic Pipeline**: Powered by LangGraph for structured AI reasoning.
- **Hybrid RAG Layer**: Semantic search via Qdrant and BGE embeddings to retrieve past resolutions.
- **Smart Routing**: Automatic department assignment based on ticket content.
- **Human-in-the-Loop**: Tickets with <90% confidence are escalated for manual review.
- **Real-time Monitoring**: Full observability stack with Prometheus and Grafana.
- **Automation Detection**: Identifies recurring issues for runbook automation.

## 🏗️ Architecture Overview

The system is composed of several microservices coordinated via Docker Compose:

| Service | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15+ | Modern dashboard and live agent resolution UI. |
| **Backend** | FastAPI | High-performance API and LangGraph orchestrator. |
| **Agent State** | LangGraph | State management for the 6-node AI pipeline. |
| **Vector DB** | Qdrant | Stores ticket embeddings for semantic RAG lookup. |
| **Task Queue** | Celery + Redis | Handles background LLM processing and RAG indexing. |
| **Primary DB** | PostgreSQL | Persists tickets, users, and resolution history. |
| **Reverse Proxy** | Nginx | Unified entry point and API routing. |
| **Monitoring** | Prometheus + Grafana | Performance metrics and pipeline health tracking. |

---

## 🚀 Getting Started (New Device)

Follow these steps to get the system running locally on your machine.

### 1. Prerequisites
- [Docker & Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [OpenAI API Key](https://platform.openai.com/) (Required for the Agentic engine)

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/agentic-ticket-system.git
cd agentic-ticket-system
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your OpenAI key:
```env
# AI Engine
OPENAI_API_KEY=your_sk_...

# Database (Default Docker settings)
POSTGRES_USER=ticket_user
POSTGRES_PASSWORD=ticket_pass
POSTGRES_DB=ticket_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://ticket_user:ticket_pass@postgres:5432/ticket_db
DATABASE_SYNC_URL=postgresql://ticket_user:ticket_pass@postgres:5432/ticket_db

# Qdrant
QDRANT_HOST=qdrant
QDRANT_API_KEY=qdrant_secret
```

### 4. Launch the System
Run the entire stack using Docker Compose:
```bash
docker-compose up -d --build
```

### 5. Apply Database Migrations
Once the containers are healthy, initialize the database schema:
```bash
docker exec -it ticket_backend alembic upgrade head
```

### 6. Access the Dashboards
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Monitoring (Grafana)**: [http://localhost:3000/grafana](http://localhost:3000/grafana)
- **Task Monitor (Flower)**: [http://localhost:5555](http://localhost:5555)

---

## 🛠️ The Agentic Pipeline (LangGraph)

The system processes every ticket through a deterministic graph of 6 specialized nodes:

1. **Intake**: Sanity checks and language detection.
2. **Classify**: Categorizes into Infrastructure, Security, Network, etc., using GPT-4-nano.
3. **RAG Lookup**: Queries Qdrant for similar historical tickets and relevant KB articles.
4. **Route**: Calculates a combined confidence score (Embedding + LLM).
   - `> 90%`: Auto-resolves or suggests an automated answer.
   - `< 90%`: Escalates to Human Review.
5. **Resolve**: Generates a step-by-step resolution plan using GPT-4o-mini.
6. **Close**: Finalizes the state and prepares the ticket for human/automated closure.

---

## 👤 Human-in-the-Loop Workflow

When a ticket falls below the **90% confidence threshold**, it appears in the **Review Queue**. 
- The AI resolution plan is **hidden** to prevent hallucination bias.
- The human agent is provided with a dedicated space to input the manual resolution steps.
- Once submitted, the system learns from this human input to improve future RAG lookups.

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
