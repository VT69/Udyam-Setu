# Udyam Setu — Grand Finale Demo Script

## Setup (before judges arrive)

1. Ensure the Docker daemon is running on the host machine.
2. Spin up the infrastructure using `docker-compose up -d` (Postgres, TimescaleDB, Redis, Celery).
3. Open a terminal and run the demo initialization script:
   ```bash
   python scripts/demo_setup.py
   ```
4. Verify the output reports at least:
   - 3 auto-linked pairs (high confidence)
   - 5 pairs in the Human-in-the-Loop review queue
   - 10+ Active businesses, 5+ Dormant, 3+ Closed
5. Launch the React Dashboard:
   ```bash
   cd frontend
   npm start
   ```
6. Open browser to `http://localhost:3000`. Full screen the browser.

## Demo Flow (5 minutes)

### Minute 1: The Problem (30 seconds narration)
* **Action**: Open the main Dashboard (`/`).
* **Narration**: "Karnataka has thousands of records across 4 disparate departments—Factories, KSPCB, BESCOM, and Shop & Establishment. But how many actual businesses do we have? Until today, no one knew. This fragmentation leads to blind spots, redundant inspections, and revenue leakage."
* **Action**: Hover over the "Total UBIDs Created" and "Records Ingested" stats.

### Minute 2: Entity Resolution in Action
* **Action**: Navigate to the `Entity Resolution` page. Click the "Auto-Linked Pairs" tab, then find a high-confidence match.
* **Narration**: "Udyam Setu uses an XGBoost-driven pipeline to deduplicate these records. Here, the system auto-linked these fragments with 0.94 confidence." 
* **Action**: Point to the SHAP Waterfall chart.
* **Narration**: "...and here is exactly why. It matched the PAN, and the phonetics of the localized Kannada names aligned perfectly."
* **Action**: Switch to the `Review Queue` tab. Click `Review` on a borderline pair (Score ~0.71).
* **Narration**: "But when the model is uncertain, it asks a human. This pair scored 0.71. The text address is similar, but the NIC codes conflict. We use a Human-in-the-Loop interface so an operator can review the ML evidence and make a final call."
* **Action**: Type a reason and click `ESCALATE` or `KEEP SEPARATE`.

### Minute 3: Activity Intelligence
* **Action**: Navigate to `Activity Intelligence`. Search for one of the known Dormant UBIDs and click to open the `UBIDDetail` page.
* **Narration**: "Once we know *who* the business is, we need to know *what* they are doing. Are they active, dormant, or closed?"
* **Action**: Scroll to the `Event Timeline` and `Activity Evidence` quote block.
* **Narration**: "Here, our 18-month rolling Activity Classifier detected no BESCOM power consumption for 15 months and a missed KSPCB renewal. The system automatically flagged this business as Dormant with 0.81 confidence, providing complete transparency into the events that drove that verdict."

### Minute 4: The Money Query
* **Action**: Navigate to the `Query Builder` page.
* **Narration**: "Now for the killer application. A government official asks: 'Show me all active factories in pincode 560058 that haven't been inspected in 18 months.'"
* **Action**: Click the `Run This Query →` pre-fill button. Click the large `Run Query` button.
* **Narration**: "This query was impossible yesterday. It required joining 3 isolated department systems without a shared primary key. Udyam Setu answers it in milliseconds."
* **Action**: Scroll down to the results and expand the `View Raw SQL Execution Logic` drawer.
* **Narration**: "...with a full, auditable SQL trail."

### Minute 5: Non-Negotiables Check
* **Action**: (If time permits) Show PII scrubbing logic in the event adapters or jump to the configuration.
* **Narration**: "Finally, we built this for regulatory compliance. PII is scrubbed at ingestion, thresholds (like the 0.92 auto-link boundary) are completely configurable, and every automated decision can be reviewed and reversed. It is an intelligent, auditable, and resilient system for the State of Karnataka."
