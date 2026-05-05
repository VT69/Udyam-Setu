# Udyam Setu — Hackathon Submission

**Theme 1: Unified Business Identifier (UBID) and Active Business Intelligence**  
*Karnataka Commerce & Industry*

## 📖 The Problem
Karnataka's business regulatory landscape spans 40+ isolated State department systems (Factories, KSPCB, BESCOM, Shop & Establishment). Because each system uses its own schema and identifiers, the State lacks a unified view of its industrial base. Master data cannot be linked, and activity signals are trapped in silos, leading to blind spots and revenue leakage. 

This project solves a strict two-part problem:
1. **Entity Resolution (UBID)**: Automatically link fragmented business records into a single Unique Business Identifier (UBID), anchored by PAN/GSTIN where available, using explainable confidence signals.
2. **Activity Intelligence**: Ingest disparate transaction streams (inspections, consumption, renewals) to classify each UBID as Active, Dormant, or Closed, with a fully auditable evidence timeline.

## 🚀 Our Solution: Udyam Setu
Udyam Setu is a production-grade, non-invasive intelligence layer that sits alongside existing department systems (satisfying the strict "no source system changes" non-negotiable constraint). 

### Key Capabilities
- **Deterministic & ML Entity Resolution**: A multi-pass blocking and XGBoost-driven deduplication engine. High-confidence pairs (>0.92) are auto-linked; ambiguous pairs are intelligently routed to a beautiful Human-in-the-Loop review queue.
- **Activity Classification Model**: An 18-month rolling timeseries classifier (LightGBM) that computes recency, frequency, and cross-department telemetry to predict true operational status.
- **Radical Explainability (SHAP)**: Every single automated decision is backed by mathematically rigorous SHAP (SHapley Additive exPlanations) values. The dashboard visualizes exactly *why* the model made a decision, ensuring total transparency for government operators.
- **Cross-Department Query Engine**: Enables complex targeting queries that were previously impossible, e.g., *"Active factories in PIN 560058 with no inspection in 18 months"*, translating multi-department constraints into highly optimized SQL.

## 🏗 Architecture & Tech Stack
- **Backend Core**: FastAPI (Python), highly modular and asynchronous.
- **Database**: PostgreSQL (with TimescaleDB for high-volume timeseries event ingestion).
- **Machine Learning**: XGBoost, LightGBM, RapidFuzz, SHAP for interpretability.
- **Task Queue**: Celery + Redis for heavy, asynchronous entity resolution workloads.
- **Frontend**: React 18, React Router v6, Tailwind CSS, Recharts for advanced SHAP waterfalls and status distributions.

## ⚖️ Hackathon Evaluation Alignment
- **Problem Relevance & Depth**: Directly addresses the fragmentation of Karnataka's MSME data without forcing a massive, unrealistic database migration.
- **Technical Implementation**: Implements true ML entity resolution (not just fuzzy string matching) and a dedicated Activity Intelligence pipeline capable of scaling to millions of records.
- **Real-World Deployability**: Operates strictly on deterministic / synthetic / scrubbed data. Hosted LLM calls on PII are explicitly forbidden by design, ensuring absolute data privacy.
- **Explainability**: Every automated decision is auditable, and the UI provides a seamless "Override" and "Escalate" workflow to keep humans in control.

## 🛠 Running the Project
The entire infrastructure is containerized for reproducibility.
```bash
# 1. Spin up the backend infrastructure (DB, Redis, API, Worker)
docker-compose up -d

# 2. Run the demo setup (seeds synthetic data & executes pipelines)
python scripts/run_demo.py

# 3. Launch the UI Dashboard
cd frontend
npm install
npm start
```
*Navigate to `http://localhost:3000` to view the command center.*

## 🎥 Deliverables
- **Presentation Flow**: See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for our exact 5-minute Grand Finale pitch choreography.
- **Code Repository**: Full open-source submission available in this repository.
