# Intelli-Credit Architecture Diagram

```text
                                   Intelli-Credit
                                         |
        ----------------------------------------------------------------
        |                              |                               |
        v                              v                               v
  Frontend UI                    Flask API Layer                Demo Launch / Ops
  Next.js / React               /api/v1/* routes               start_demo.bat
        |                              |                               |
        v                              v                               v
  CreditApplicationContext      PipelineOrchestrator           verify_demo_stack.ps1
        |
        ----------------------------------------------------------------
                                         |
                                         v
                              Intelligence Service Layer
                                         |
  -----------------------------------------------------------------------------------------
  |                    |                    |                    |                         |
  v                    v                    v                    v                         v
Document Service   OCR Service        Research Service     Scoring Service          CAM Service
  |                fallback OCR       simulated connectors explainable scoring      DOCX/PDF memo
  |                page confidence    MCA/e-Courts/RBI    PD/grade/limit/rate      formatted report
  |                table heuristics   news/sector graph   scenarios/covenants       transformer evidence
  |
  -----------------------------------------------------------------------------------------
  |                    |                    |                    |                         |
  v                    v                    v                    v                         v
Anomaly Service   Qualitative NLP    Early Warning       Transformer Explainability  Spark Simulator
GST-bank flags    officer note NLP   monitoring flags    semantic PDF evidence       demo big-data story
                                         |
                                         v
                               SQLAlchemy Persistence Layer
                                         |
                                         v
                       applications / documents / research / scorecard / CAM

```

## Data Flow

1. Documents are uploaded from the frontend or ingested by file path.
2. `DocumentProcessingService` extracts native text and triggers OCR fallback if confidence is low.
3. Extracted signals flow into:
   - anomaly analytics
   - qualitative note intelligence
   - research graph generation
   - explainable scoring
   - transformer evidence retrieval
4. The orchestrator combines all outputs into:
   - decision response
   - cockpit payload
   - CAM memo
5. The frontend reads the same application snapshot and renders:
   - risk scoring
   - anomalies
   - monitoring signals
   - sanction simulation
   - CAM download view
