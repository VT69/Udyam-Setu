# Udyam-Setu

Udyam Setu is a government business intelligence platform for Karnataka.

## Overview
This platform performs Entity Resolution across fragmented MSME identities across Indian regulatory databases (Factories, KSPCB, BESCOM, Shop & Establishment). It also features an Activity Intelligence pipeline that classifies the operational status of businesses (ACTIVE, DORMANT, CLOSED) using a LightGBM classifier over 18-month rolling timeseries data.

## Features
- **FastAPI Backend**: Asynchronous endpoints, SQLAlchemy ORM, TimescaleDB.
- **Entity Resolution**: Multi-pass blocking, XGBoost classifier with Platt scaling, and rule-based decision engine.
- **Activity Intelligence**: Rolling telemetry feature engineering and automated SHAP evidence summarization.
- **React Dashboard**: Recharts for explainability, Tailwind CSS, and a complex cross-department querying interface.
- **Asynchronous Task Queue**: Celery integration for heavy ML workloads and batch pipelines.

## Setup
Refer to `docker-compose.yml` for the complete infrastructure scaffolding (Postgres, Redis, API, Worker, Frontend).
