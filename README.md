# 🤖 Agentic Ticket System

A production-grade, human-in-the-loop AI ticketing system built with **FastAPI**, **Next.js**, and **LangGraph**. This system automates ticket classification, resolution suggestion, and routing while maintaining a strict 90% confidence threshold for human intervention.

## 🌟 Key Features

- **6-Node Agentic Pipeline**: Powered by LangGraph for structured AI reasoning.
- **Hybrid RAG Layer**: Semantic search via Qdrant and BGE embeddings to retrieve past resolutions.
- **Smart Routing**: Automatic department assignment based on ticket content.
- **Human-in-the-Loop**: Tickets with <90% confidence are escalated for manual review.
- **Real-time Monitoring**: Full observability stack with Prometheus and Grafana.
- **Automation Detection**: Identifies recurring issues for runbook automation.

---

## 🏗️ Architecture Deep Dive

The system follows a modern microservices architecture designed for scalability and high availability:

| Service | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15+ | React-based dashboard with real-time pipeline visualization. |
| **Backend** | FastAPI | Asynchronous Python API and LangGraph orchestrator. |
| **Agent Engine** | LangGraph | State machine that manages the lifecycle of a ticket across AI nodes. |
| **Vector DB** | Qdrant | High-performance vector search engine for RAG. Uses Cosine Similarity. |
| **Embeddings** | BGE-small-en-v1.5 | Local transformer model for converting text to 384-dim vectors. |
| **Task Queue** | Celery + Redis | Asynchronous processing of RAG indexing and complex LLM tasks. |
| **Primary DB** | PostgreSQL | Relational database for structured ticket metadata and user accounts. |
| **Reverse Proxy** | Nginx | Handles API routing, timeouts, and SSL termination. |
| **Monitoring** | Prometheus | Scrapes metrics from FastAPI and Celery workers. |
| **Visualization** | Grafana | Dashboard for tracking system health and AI performance. |

---

## 🛠️ The Agentic Pipeline (Node-by-Node)

The heart of the system is the **LangGraph Pipeline**, which processes every ticket through 6 specialized nodes:

### 1. 📥 Intake Node
- **Function**: Sanity checks and ingestion.
- **Details**: Validates the ticket description length, detects the language, and extracts basic metadata. It prepares the "Agent State" that will travel through the rest of the graph.

### 2. 🧠 Classify Node
- **Function**: Department & Priority Assignment.
- **Details**: Uses GPT-4-nano to perform zero-shot classification into 6 categories: *Infrastructure, Application, Security, Database, Network, Access Management*. It also calculates an **Urgency Score** (0-1) based on the impact described.

### 3. 🔍 RAG Lookup Node
- **Function**: Semantic Context Retrieval.
- **Details**: 
  - Converts the ticket into a vector using the **BGE Embedding** model.
  - Searches the **Knowledge Base** collection (Threshold: 0.6) for relevant articles.
  - Searches the **Tickets** collection (Threshold: 0.7) for past resolved issues.
  - Identifies if the issue is a **Repeat Issue** (found ≥ 2 similar past tickets).

### 4. 🗺️ Routing Node
- **Function**: Intelligence & Escalation Logic.
- **Details**: Calculates a **Combined Confidence Score**. 
  - **Auto-Resolve (>= 90%)**: If confidence is high and a past solution exists, the AI is allowed to proceed.
  - **Human Escalation (< 90%)**: If the AI is uncertain, the ticket is flagged for `is_escalated = True`.
  - **Automation Candidate**: If an issue has appeared ≥ 3 times, it triggers an "Automation Opportunity" flag.

### 5. ⚡ Resolution Node
- **Function**: AI Resolution Generation.
- **Details**: Only runs if confidence is high. It pulls the retrieved RAG context (KB articles + past solutions) and uses GPT-4o-mini to generate a step-by-step resolution plan specifically tailored to the current user's problem.

### 6. ✅ Close Node
- **Function**: State Finalization.
- **Details**: Transitions the ticket status, logs the final trace of the agent's reasoning, and persists all AI metadata (category, priority, confidence, and solution) back to the PostgreSQL database.

---

## 🚀 Getting Started (New Device)

### 1. Prerequisites
- [Docker & Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [OpenAI API Key](https://platform.openai.com/)

### 2. Installation
```bash
git clone https://github.com/YOUR_USERNAME/agentic-ticket-system.git
cd agentic-ticket-system
docker-compose up -d --build
docker exec -it ticket_backend alembic upgrade head
```

### 3. Access
- **App**: [http://localhost:3000](http://localhost:3000)
- **Monitoring**: [http://localhost:3001](http://localhost:3001) (Grafana) | [http://localhost:9090](http://localhost:9090) (Prometheus)

---

## 👤 Human-in-the-Loop Workflow

When a ticket falls below the **90% confidence threshold**:
- The AI resolution plan is **hidden** to prevent hallucination bias.
- The human agent provides the manual resolution.
- The system **learns** from this human input by automatically indexing the final solution into the Vector DB, improving future RAG lookups.

---

## 📄 License
MIT License.
