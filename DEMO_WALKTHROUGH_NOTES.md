# Intelli-Credit Judge Walkthrough Notes

## Demo Objective

Show that Intelli-Credit can move from borrower documents to a structured, explainable lending recommendation while remaining sensitive to Indian credit underwriting requirements.

## Suggested Demo Flow

1. Open the app at `http://127.0.0.1:3000`
2. Enter borrower details
3. Upload multiple documents on `/documents`
4. Open `/ingestor`
   - highlight OCR-aware extraction
   - show document confidence, extraction source, and structured signals
5. Open `/research`
   - explain MCA, e-Courts, RBI, news, and sector intelligence connectors
   - mention research graph outputs:
     - promoter risk
     - litigation risk
     - sector outlook
     - regulatory alerts
6. Open `/credit-officer`
   - add qualitative notes such as:
     - factory operating at 40% capacity
     - governance issue observed
     - labour issue noted
   - explain that these notes are converted into scoring adjustments
7. Open `/risk-scoring`
   - show PD gauge
   - show risk heatmap
   - show anomaly panel
   - show early warning signals
   - show covenant recommendations
   - show sanction simulator
8. Open `/cam-generator`
   - show professional CAM sections
   - explain that the memo includes:
     - XGBoost-style score reasoning
     - transformer evidence from PDFs
     - research-agent intelligence
     - anomaly summary
     - officer adjustment summary
     - monitoring triggers

## Key Judge Talking Points

### 1. Extraction Accuracy
- Native PDF extraction is used first
- OCR fallback activates when confidence is weak
- table-like data is reconstructed into structured JSON
- bounding-box style metadata is exposed for visual explainability

### 2. Research Depth
- Secondary research is orchestrated in parallel
- simulated connectors mimic realistic production integrations
- research graph translates findings into credit-relevant structured signals

### 3. Explainability
- scorecard exposes directional contributions and narrative reasons
- transformer layer links score drivers back to supporting PDF snippets
- CAM explicitly ties decision to evidence

### 4. Indian Context Sensitivity
- GST reconciliation concepts are built into anomaly logic
- MCA, RBI, e-Courts, NCLT / IBC style review is represented
- compliance mapping is aligned to corporate lending in India

## Best Demo Narrative

Use this line:

“Intelli-Credit does not just extract documents and output a score. It connects borrower filings, financial signal anomalies, market intelligence, officer observations, and evidence-backed explainability into a credit memo that a real credit manager can defend.”

## Suggested Backup Explanation If Asked About Live Data

“For hackathon stability, several live connectors are simulated but structured like production services. The orchestration, schema, scoring impact, and CAM integration are already built, so replacing mocks with live APIs is a contained service-layer upgrade.”
