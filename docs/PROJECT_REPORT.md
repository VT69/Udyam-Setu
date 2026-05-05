# Udyam Setu — Full Project Report & Architecture Deep Dive

This document serves as the comprehensive technical specification and structural map for **Udyam Setu**—a Unified Business Identifier (UBID) and Activity Intelligence platform built for the Karnataka Commerce & Industry hackathon (Theme 1).

---

## 1. Executive System Flow

The Udyam Setu platform operates through a two-stage sequential pipeline:

**Stage A: Entity Resolution (The UBID Pipeline)**
1. **Ingestion & Normalisation**: Fragmented business records from 40+ state departments (e.g., Factories, BESCOM) are ingested. `normalisation.py` sanitizes textual data (e.g., expanding abbreviations, computing Metaphone/Soundex hashes for names and phonetics).
2. **Blocking**: `blocking.py` runs multi-pass algorithms to group potential duplicate records into candidate pairs, drastically reducing the \(O(N^2)\) comparison space.
3. **Feature Engineering**: `features.py` computes similarity vectors (Jaccard distances, exact matches) between candidate pairs.
4. **ML Scoring & Decision**: `model.py` (XGBoost) scores the vectors. `decision_engine.py` categorizes pairs:
   - **> 0.92**: Auto-linked (merged into one Golden UBID).
   - **0.60 - 0.92**: Sent to the `Review Queue` for Human-in-the-Loop resolution.
   - **< 0.60**: Kept separate.

**Stage B: Activity Intelligence (The Operations Pipeline)**
1. **Telemetry Ingestion**: Disparate temporal events (e.g., inspections, utility bills) are ingested via `event_processor.py` and mapped to their respective UBIDs.
2. **Feature Rolling**: `feature_engineer.py` computes an 18-month rolling feature vector (recency, frequency, cross-department diversity) for every UBID.
3. **Classification**: `classifier.py` (LightGBM) predicts the current status: `ACTIVE`, `DORMANT`, or `CLOSED`.
4. **SHAP Explainability**: Both pipelines export SHAP (SHapley Additive exPlanations) values to the frontend, ensuring every AI decision is transparent and reversible.

---

## 2. Directory Structure & File Roles

### 2.1 Backend (`/backend`)
The API layer, powered by **FastAPI** and **SQLAlchemy**.

* **`app/main.py`**: The FastAPI application factory. Registers all routers and initializes database connections.
* **`app/database.py`**: Database connection management for PostgreSQL/TimescaleDB.
* **`app/schemas/`**: Pydantic models for request validation and serialization.
* **`app/db/models.py`**: SQLAlchemy ORM definitions (`UBID`, `DepartmentRecord`, `CandidatePair`, `Event`, `ActivityClassification`).

#### Routers (`app/routers/`)
Exposes the HTTP API to the frontend.
* **`entity_resolution.py`**: Endpoints for `POST /run-pipeline`, `GET /review-queue`, and `POST /review/{pair_id}`.
* **`activity.py`**: Exposes `GET /status/{ubid}`, the batch `POST /classify-all`, and the powerful `GET /query/cross-department` (the "Money Query" endpoint mapping natural language criteria to SQL).
* **`events.py`**: Endpoints for managing and attributing orphaned telemetry events.

#### Services (`app/services/`)
Contains the core business logic and algorithms.
* **`normalisation.py`**: 
  - `normalize_business_name()`: Cleanses text, strips legal suffixes (Pvt Ltd), and generates phonetic tokens.
  - `normalize_address()`: Standardizes Karnataka addresses and pincodes.

* **`entity_resolution/`**
  - **`blocking.py`** (`BlockingEngine`): Uses algorithms like `_block_anchor` (PAN/GSTIN) and `_block_phonetic_pin` to yield viable pairs.
  - **`features.py`**: Calculates the mathematical distance between records in a pair.
  - **`model.py`** (`EntityResolutionModel`): Loads the `model.pkl`. Contains `predict_with_shap()` to return both probability and feature contributions.
  - **`decision_engine.py`**: Contains the strict thresholding logic.
  - **`pipeline.py`**: The orchestrator. Combines the above into a Celery asynchronous task (`@celery_app.task`).

* **`activity/`**
  - **`event_processor.py`** (`EventProcessor`): Ingests raw events and attempts to attribute them to UBIDs. Unmatched events are flagged as `UNATTRIBUTABLE`.
  - **`feature_engineer.py`** (`ActivityFeatureEngineer`): Calculates features like `days_since_last_event`, `events_per_month_trend`, and `signal_diversity_ratio`.
  - **`classifier.py`** (`ActivityClassifier`): Executes LightGBM inference to yield operational status and triggers review flags for high-entropy outputs.

### 2.2 Frontend (`/frontend`)
The React 18 dashboard, utilizing **Tailwind CSS**, **Recharts**, and **Lucide React**.

* **`src/api/`**
  - **`client.js`**: Global Axios configuration targeting the FastAPI backend.
  - **`endpoints.js`**: Centralized dictionary of API calls (e.g., `api.er.getReviewQueue`).

* **`src/components/layout/`**
  - **`Layout.jsx`**, **`Sidebar.jsx`**, **`TopBar.jsx`**: The persistent shell and navigation infrastructure.

* **`src/components/ui/`** (Reusable Primitives)
  - **`ShapWaterfall.jsx`**: Custom Recharts horizontal bar chart mapping ML feature contributions (Saffron = positive push, Red = negative push).
  - **`EvidenceTimeline.jsx`**: Chronological stepper that automatically detects gaps > 3 months and injects visual warnings.
  - **`StatCard.jsx`**: Metric cards featuring 0-to-target numerical mounting animations.
  - **`ConfidenceBadge.jsx` / `StatusBadge.jsx`**: Standardized coloring for UI consistency.

* **`src/pages/`** (Core Views)
  - **`Dashboard.jsx`**: The command center. Dense information grid of KPIs, pie charts for status distributions, and queue depth alerts.
  - **`EntityResolution.jsx`**: Features the pipeline execution visualizer and the paginated list of pairs awaiting human arbitration.
  - **`ReviewTask.jsx`**: The split-pane Human-in-the-Loop interface. Renders Record A against Record B, highlighting discrepancies, displaying the SHAP reasoning, and providing keyboard shortcuts (M/S/E) for the operator to MERGE or SEPARATE.
  - **`ActivityIntelligence.jsx`**: Renders department-grouped active/dormant statistics and houses the manual override modal for ML correction.
  - **`UBIDDetail.jsx`**: The Golden Record view. Displays the master UBID, all fragmented department links, the ML explanation quote block, and the chronological Event Timeline.
  - **`QueryBuilder.jsx`**: The killer demo feature. Allows complex targeting (e.g., "Active Factories, PIN 560058, No inspection in 18 months") and exposes the raw SQL logic generated by the backend.

### 2.3 Machine Learning (`/ml`)
Offline training pipelines.
* **`entity_resolution/train.py`**: Bootstraps training data, trains the XGBoost deduplication model, applies Platt scaling for probability calibration, and saves `model.pkl`.
* **`activity_intelligence/train.py`**: Trains the LightGBM classifier on the rolling timeseries features to distinguish Active vs. Dormant vs. Closed states.

### 2.4 Scripts (`/scripts`)
Automation tools for setup and demonstration.
* **`seed_data.py`**: Generates complex synthetic Karnataka business data. Purposefully injects typos, missing door numbers, abbreviation variations, and fragmented department records to stress-test the ER pipeline.
* **`demo_setup.py`**: Automatically clears the DB, seeds the data, bypasses Celery to force a synchronous ER/Activity pipeline run, and exports the deterministic `demo_state.json`.
* **`run_demo.py`**: A lightweight CLI wrapper that executes the setup and validates Docker infrastructure readiness for presentation.

---

## 3. How the Pieces Fit Together (The "Active Factories" Query Flow)

To understand the architecture, follow the path of the target query: *"Active factories in 560058 with no inspection in 18 months"*.

1. **The Official** opens `QueryBuilder.jsx` and uses the sliders/toggles to set parameters.
2. **React** packages this into an Axios `GET` request to `api/endpoints.js` -> `crossDeptQuery`.
3. **FastAPI (`activity.py`)** receives the request and dynamically constructs an advanced SQL query using SQLAlchemy's `text()`.
4. **PostgreSQL** executes the query:
   - It searches `department_records` for `pincode=560058`.
   - It filters where the `ubid_id` maps to an `ActivityClassification` whose status is currently `ACTIVE`.
   - It runs a subquery against the `events` table (TimescaleDB) verifying no row exists for that UBID where `event_type=INSPECTION` and `date > NOW() - 18 months`.
5. **The Backend** returns the exact list of UBIDs along with the English translation of the query and the raw SQL syntax.
6. **The Frontend** renders the High-Impact Result Cards, allowing the official to click directly into `UBIDDetail.jsx` to verify the findings.
