# Intelli-Credit

AI-powered corporate credit appraisal platform built for the Intelli-Credit hackathon problem statement. The system ingests structured and unstructured borrower documents, runs secondary research, captures credit officer observations, computes an explainable risk recommendation, and generates a formal Credit Appraisal Memo (CAM) in DOCX and PDF.

## What This Project Does

Intelli-Credit is designed around the three hackathon pillars:

1. Data Ingestor
   Parses annual reports, financial statements, GST-style records, bank statements, legal notices, and other PDFs. The backend supports parallel document processing and stores extracted metadata, identifiers, risk flags, and structured signals.

2. Research Agent
   Runs parallel secondary research workflows for MCA, e-Courts, RBI, and news-style intelligence. It also supports credit officer qualitative overlays such as factory utilization, management quality, governance observations, and customer concentration.

3. Recommendation Engine
   Produces an explainable credit decision: an XGBoost probability-of-default model with exact TreeSHAP explanations, on top of OCR + NER document extraction, GST reconciliation, and a retrieval-based research agent. The output includes PD, risk grade, sanction limit, pricing recommendation, compliance mapping, and CAM generation. See [How Scoring Works](#how-scoring-works).

## Current Stack

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide icons

### Backend
- Flask
- SQLAlchemy
- PyPDF2, pypdfium2
- RapidOCR (ONNX Runtime)
- XGBoost, scikit-learn
- sentence-transformers (MiniLM, optional)
- python-docx
- reportlab
- pytest

### Supporting Components
- Parallel document processing
- Parallel research orchestration
- OCR-aware PDF handling hooks
- Explainability evaluation scripts
- Demo batch pipeline for attached PDFs

## Repository Structure

```text
intelli-credit/
├── backend/
│   ├── app/
│   │   ├── factory.py
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── ml/                  # PD model: features, synthetic training data, training, inference
│   │   │   └── artifacts/       # trained XGBoost model + metadata
│   │   └── services/            # OCR, NER, GST reconciliation, research, scoring, CAM ...
│   ├── synthetic_data/          # synthetic borrower document packs + research corpus
│   ├── tests/                   # unit / integration / security / e2e / regression
│   ├── pytest.ini
│   ├── requirements-flask.txt
│   ├── demo_synthetic_borrowers.py
│   ├── run_flask.py
│   ├── run_attached_pdf_pipeline.py
│   ├── evaluate_credit_explainability.py
│   ├── generate_demo_summaries.py
│   └── document_requirement_mapping.json
├── frontend/
│   ├── src/pages/
│   ├── src/context/
│   ├── src/lib/
│   └── package.json
├── start_backend.bat
├── start_frontend.bat
├── start_demo.bat
└── verify_demo_stack.ps1
```

## Key Features

- Multi-document ingestion for corporate credit analysis
- Support for annual reports, sustainability reports, generic PDFs, and file-path based ingestion
- Compliance mapping aligned to Indian credit appraisal context:
  - GST reconciliation expectations
  - MCA filing review
  - RBI KYC / AML expectations
  - e-Courts / NCLT / IBC litigation screening
  - CRA review where applicable
- Credit officer qualitative scoring inputs
- Five Cs breakdown:
  - Character
  - Capacity
  - Capital
  - Collateral
  - Conditions
- Explainable model output:
  - Probability of default
  - Risk grade
  - Recommended limit
  - Recommended rate
  - TreeSHAP feature contribution view
- Formal CAM generation in DOCX and PDF
- Demo summary and company-wise split reports for attached PDF batches

## Advanced Intelligence Improvements

The current implementation has been extended without changing the existing route structure or breaking the demo flow.

### Data Ingestor Extensions
- OCR fallback service at `backend/app/services/ocr_service.py`
- Native PDF extraction with OCR-aware fallback switching
- Page-level OCR confidence scoring
- Table reconstruction heuristics for financial layouts
- Bounding box style metadata for judge-friendly explainability
- Extraction source markers: `native` or `ocr`
- Thread-safe document caching and demo-mode acceleration

### Financial Intelligence Extensions
- GST vs bank anomaly analytics at `backend/app/services/anomaly_service.py`
- Heuristics for:
  - revenue mismatch
  - circular movement
  - same-day loops
  - receivable anomalies
  - GST liability vs bank mismatch
- Early warning engine at `backend/app/services/early_warning_service.py`

### Research Intelligence Extensions
- Enhanced simulated research connectors for:
  - MCA
  - e-Courts
  - RBI
  - news sentiment abstraction
  - sector risk signals
- Research graph output:
  - promoter risk
  - litigation risk
  - sector outlook
  - regulatory alerts

### Qualitative Intelligence Extensions
- Officer note processing at `backend/app/services/qualitative_intelligence.py`
- Sentiment analysis
- Keyword extraction
- Numeric adjustments to capacity / governance / management overlay

### Explainable Scoring Extensions
- Richer feature vector pipeline
- PD banding
- risk premium calculation
- sanction sensitivity simulation
- scenario analysis
- covenant recommendations
- narrative reasons per TreeSHAP driver

### CAM Intelligence Extensions
- anomaly summary
- research intelligence summary
- transformer evidence section
- officer adjustment summary
- monitoring triggers
- covenant recommendations
- scenario analysis

### Cockpit Extensions
- New endpoint:
  - `GET /api/v1/applications/<id>/cockpit`
- Returns:
  - PD meter data
  - risk heatmap
  - document completeness
  - anomaly alerts
  - early warning signals
  - sanction bands
  - feature waterfall

### Demo Storytelling Extensions
- Spark simulator at `backend/app/services/spark_pipeline_simulator.py`
- Text architecture diagram in [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
- Judge walkthrough notes in [DEMO_WALKTHROUGH_NOTES.md](DEMO_WALKTHROUGH_NOTES.md)

## Backend API

Base URL:

```text
http://127.0.0.1:5000/api/v1
```

Available endpoints:

```text
GET  /health
POST /applications
GET  /applications/<application_id>
GET  /applications/<application_id>/cockpit
POST /applications/<application_id>/documents/ingest
POST /applications/<application_id>/decision
GET  /schema/processing
POST /schema/compliance-matrix
GET  /applications/<application_id>/cam/<pdf|docx>
GET  /cams/download?path=<CAM file name or path inside storage/cams>   (anything else -> 403)
```

## Why This Project Is Needed

When a company asks a bank for a loan (for example ₹35 crore of working capital), a credit officer has to:

1. **Read a stack of documents**: annual reports, GST returns, bank statements, rating letters, legal notices. Many are scanned images.
2. **Check that they agree with each other**: do GST returns match each other? Do bank deposits match declared sales? Are the PAN / GSTIN genuine and consistent?
3. **Research the outside world**: company filings (MCA), court cases (e-Courts, NCLT insolvency), promoter news, RBI rules for the sector.
4. **Estimate the risk**: how likely is the borrower to default, and what loan amount and interest rate are safe?
5. **Write a Credit Appraisal Memo (CAM)** that justifies the decision to the credit committee and regulators.

Done by hand this takes days per borrower and is error-prone. Fraud (fake invoices, money cycled through group companies, inflated sales) usually only shows up when sources are **cross-checked**. Intelli-Credit does that cross-checking in seconds and **explains every number**, because lenders must justify decisions to RBI and auditors.

## What Happens When a User Opens It

The user is a credit officer. The navigation follows their workflow.

| Page | What the officer does | What the system does |
|---|---|---|
| **Dashboard** `/` | Sees the current case | PD, grade, limit, Five Cs radar, top drivers, document status. Shows "No Live Credit Case Yet" until a case exists |
| **Documents** | Enters borrower name, sector, amount; drops in PDFs / scans / CSVs | Creates the application, classifies each file, processes files in parallel: native text or **OCR**, **NER**, risk flags, GST/bank table parsing |
| **Data Ingestor** | Checks the extraction | Per-document facts: IDs, INR amounts, reconstructed tables, confidence |
| **Credit Officer** | Adds site-visit notes and management / governance ratings, then **runs the decision** | GST reconciliation → research agent → 15 risk scores → XGBoost PD → TreeSHAP → limit, rate, covenants → CAM |
| **Research** | Reviews outside evidence | Five findings (MCA, e-Courts, News, RBI, Sector) with severity and citations, litigation table, compliance mapping |
| **Risk Scoring** | Reviews the decision and reasons | PD gauge, grade, limit, rate, anomaly / early-warning alerts, SHAP bar per feature, Five Cs, sanction scenarios |
| **CAM Generator** | Downloads the memo | DOCX + PDF credit appraisal memo for the credit committee |

**Example (synthetic fraud-like borrower "Vertex Tradelinks"):** within ~3 seconds of upload, OCR reads the scanned rating letter (*CRISIL B, Negative*). Reconciliation finds GSTR-3B under-reported in all 12 months, ITC over-claimed by 32% and 36 round-trip transfers with related companies. Research finds an NCLT insolvency petition and an Enforcement Directorate search. The model returns **PD 43.7%, grade D, reject**, with litigation risk, anomaly score and early warnings as the main reasons, each traceable to a document or a cited source.

## How Scoring Works

```text
Documents ──► per-document checks ──► 15 risk scores (0–1) ──► XGBoost ──► PD % ──► grade / decision / limit / rate
                (confidence, flags)                                 │
                                                                    └──► TreeSHAP ──► why: per-feature pushes
                                                                                         ──► CAM reasons, covenants,
                                                                                             officer checks, monitoring
```

### Step 1: each document is checked on its own

**Confidence score** ("how well could we read this file?"): starts at 0.35, capped at 0.98.

| Found in the file | Points |
|---|---|
| Any readable text | +0.25 |
| An identifier (PAN / GSTIN / CIN) | +0.20 |
| Rupee amounts | +0.10 |
| Useful keywords | +0.10 |
| Structured GST / bank tables | +0.15 |
| Text quality / OCR confidence | +0.08 × native confidence, +0.05 × OCR confidence |

**Risk flags**: phrases such as *qualified opinion*, *going concern*, *NPA*, *fraud*, *overdue*, *litigation*, *related party* each add a flag.

**OCR and NER**: PDFs with a usable text layer are read directly. Scanned pages are rendered with pypdfium2 and read by RapidOCR, which keeps confidence, bounding boxes and row-clustered tables. The financial NER extracts PAN (with holder type), GSTIN (GSTN mod-36 check digit, plus OCR glyph repair such as `O`↔`0` that is accepted only when the check digit validates), CIN, IFSC, INR amounts normalised from lakh/crore, percentages, dates, fiscal years, credit ratings, organisations and persons.

### Step 2: the 15 risk scores (exact formulas)

The model never reads documents. It reads **15 numbers in [0, 1]**. *Strengths*: higher = safer. *Risks*: higher = riskier.

Notation: `[condition]` = 1 if true else 0; `clip(x, a, b)` keeps x between a and b. Keyword groups are counted over all document text:

| Group | Words |
|---|---|
| profit | profit, ebitda, pat, return on assets, roe, growth, margin |
| liquidity | cash, liquidity, collections, receivables, operating cash |
| bank | bank, statement, account, repayment, deposits |
| debt | debt, borrowing, liability, gearing, leverage |
| governance | board, audit committee, csr, esg, governance, compliance |
| stress | rbi, headwind, stress, downgrade, restructuring, wilful default |

Worked values are for the synthetic borrower **Vertex Tradelinks**.

#### A. Coverage

| # | Score | Type | Formula | Vertex |
|---|---|---|---|---|
| 1 | Document coverage | strength | `min((docs / 6) × 0.7 + mean document confidence × 0.3, 1)` | (4/6)·0.7 + 0.9675·0.3 = **0.757** |
| 2 | Identifier coverage | strength | `min(IDs found / (3 × docs) × 2, 1)` (CIN, PAN, GSTIN per document) | 5/12 × 2 = **0.833** |

#### B. Financial health (mostly from the annual report)

**3. GST consistency** (strength)
```text
h = clip(0.42 + min(0.18 × docs with GSTIN, 0.24) + 0.12 × [GST words present]
         − min(0.12 × count("circular trading" | "inflated turnover" | "bogus" | "mismatch"), 0.30), 0.08, 0.95)
if GST returns were uploaded:  clip(0.4 × h + 0.6 × (1 − GST reconciliation risk), 0.05, 0.98)
```
Vertex: 0.4 × 0.78 + 0.6 × (1 − 0.8) = **0.432**

**4. Cash-flow stability** (strength)
```text
clip(0.44 + min(0.03 × (liquidity + bank words), 0.24) + 0.08 × [any % above 20]
     + 0.12 × min(rupee amounts found / 18, 1) − min(0.04 × stress words, 0.22), 0.12, 0.94)
officer adjustment: −0.12 if capacity utilisation < 50 %, −0.06 if < 65 %   (then clip 0.05–0.98)
```
Vertex (utilisation 40 %): **0.413**

**5. Profitability** (strength)
```text
clip(0.40 + min(0.035 × profit words, 0.28) + 0.10 × [any % between 8 and 40]
     − min(0.08 × flags mentioning default / NPA / going concern / fraud, 0.28), 0.10, 0.95)
```
Vertex: **0.70**

**6. Leverage headroom** (strength; higher = less debt pressure)
```text
clip(0.66 − min(0.025 × debt words, 0.20) − 0.08 × [loan > ₹15 cr] − 0.06 × [loan > ₹30 cr]
     − 0.05 × [related-party flag], 0.12, 0.90)
```
Vertex (₹35 cr requested, related-party flag): **0.42**

#### C. People and management

**7. Governance** (strength)
```text
clip(0.46 + min(0.03 × governance words, 0.24) + 0.18 × officer governance score
     + 0.07 × [board / audit committee / ESG mentioned]
     − min(0.09 × flags for fraud / qualified opinion / going concern, 0.27), 0.10, 0.96)
+ governance delta from officer notes (governance / labour issues)        (clip 0.05–0.98)
```
Vertex: **0.551**

**8. Management overlay** (strength; driven mostly by the officer)
```text
0.35 × utilisation% / 100 + 0.30 × management quality / 10 + 0.20 × inventory rating / 10
+ 0.15 × (1 − customer concentration% / 100) + 0.04 × [management words in documents]
− note penalty
note penalty = 0.12 × max(0, −note sentiment) + (0.12 if utilisation < 50 %, 0.06 if < 65 %)
               + governance-issue penalty (0.03 per mention, max 0.12) + labour penalty (0.04 per mention, max 0.12)
```
Vertex: 0.14 + 0.12 + 0.06 + 0.0435 − 0.27 = **0.0935** (notes: "weak records, governance issue", utilisation 40 %)

#### D. Outside-world risk (from the research agent)

Each research finding first gets its own risk:
```text
finding risk = max over evidence of (severity × recency) + 0.05 × (severe items − 1)
recency      = e^(−age_days / 730)                    # ≈ 2-year decay, measured from the newest signal
severity     = lexicon: insolvency/IBC 0.9, NCLT 0.85, fraud/ED 0.85–0.9, default/NPA 0.75,
               recovery suit 0.7, downgrade 0.6, penalty 0.45 … ; mitigants ("upgrade", "order win") reduce it
```
Retrieval is TF-IDF (optionally fused with MiniLM). Entity connectors (MCA, e-Courts, News) only use records whose company name matches the borrower (token Jaccard ≥ 0.6 after removing "Pvt", "Ltd" and similar), so look-alike companies are ignored. Sector connectors (RBI, Sector) use sector-matched or general notes. Summaries are extractive, with `[E1]`-style citations.

| # | Score | Type | Formula | Vertex |
|---|---|---|---|---|
| 9 | Litigation risk | risk | `clip(0.18 + min(0.10 × litigation findings, 0.20) + 0.45 × court-records risk + min(0.08 × doc flags for litigation/default/fraud/NPA, 0.22) + 0.08 × [IBC/NCLT in documents], 0.08, 0.95)` | 0.18 + 0.10 + 0.45·0.9518 = **0.708** |
| 10 | Sector headwinds | risk | `clip(0.30 + 0.35 × sector risk + min(0.06 × negative findings, 0.18) + 0.10 × [RBI/stress/regulatory words] + 0.08 × [default/NPA flags], 0.10, 0.92)` | 0.929 → capped **0.92** |
| 11 | Promoter risk | risk | highest promoter risk among MCA and News findings | **0.95** (ED search) |

#### E. Red flags

**12. Risk-flag density** (risk): `min(total flags / docs / 4, 1)`. Vertex: 4 / 4 / 4 = **0.25**

**13. Early warning** (risk): points add up, capped at 1

| Trigger | Points |
|---|---|
| "EBITDA decline" / margin pressure in documents | +0.18 |
| Rising debtor / receivable days | +0.16 |
| GST filing delay mentioned in text | +0.14 |
| Rating downgrade / negative outlook | +0.20 |
| Litigation finding | +0.12 (+0.04 each, max 0.24) |
| GSTR-3B filed late ≥ 2 times | +0.06 + 0.02 per late filing (max 0.18) |
| ≥ 3 round-trip transfers | +0.12 |
| Anomaly score > 0.35 | +0.12 |

Vertex: 0.20 + 0.16 + 0.18 + 0.12 + 0.12 = **0.78**

**14. GST reconciliation risk** (risk), from uploaded GST returns and bank statement
```text
R = 0.25 × gap + 0.25 × ITC + 0.20 × coverage + 0.20 × round_trip + 0.10 × late
gap        = min(mean |GSTR-1 − GSTR-3B| / GSTR-1 ÷ 0.20, 1)
ITC        = min(mean max(ITC claimed in 3B − ITC available in 2B, 0) / available ÷ 0.20, 1)
coverage   = min(max(0.85 − bank credits / (GST turnover × 1.18), 0) ÷ 0.45, 1)
             (half weight above 1.6×, which suggests unreported sales)
round_trip = min(share of bank credits sent back to the same counterparty within 3 days (±2 %) ÷ 0.25, 1)
late       = min(late GSTR-3B filings ÷ 6, 1)
```
Unusual return periods are reported when a robust (median/MAD) z-score ≥ 3.5 **or** an Isolation Forest outlier is **also** materially off (e.g. gap above 10 % and ≥ 5 points above the median). This stops clean borrowers from being flagged.

Vertex: gap 1, ITC 1, coverage **0**, round-trip 1, late 1 → **0.80**. The coverage check alone *missed* this borrower: circular money flowing back in pushed bank credits to 102 % of turnover. The round-trip check caught it.

**15. Anomaly score** (risk)
```text
with GST data:     max(R, 0.25 × narrative keyword anomaly score) + 0.10 per identifier-consistency flag
without GST data:  narrative keyword anomaly score
```
Identifier checks: the application PAN must appear in the documents, the GSTIN must embed the PAN, and the GSTIN check digit must be valid. Vertex: **0.80**

> **Limitation:** scores 3–10 are hand-designed rules on keyword counts. They are the weakest part of the pipeline. XGBoost learns how to combine them but cannot fix weak inputs. The next improvement is to replace keyword counts with real financial ratios extracted from the statements (debt/EBITDA, DSCR, current ratio).

### Step 3: XGBoost turns the 15 scores into a probability of default

**Training** (`python -m app.ml.train_pd_model`): 8,000 simulated borrowers. A latent credit-quality factor makes the features correlate realistically; sector stress is a shared shock; ~45 % have no GST data; defaults are drawn from a logistic model with a litigation × anomaly interaction and noise; features are observed with measurement error; default rate 9.8 %. Split 70/15/15. Settings: depth-3 trees, learning rate 0.05, early stopping on validation log-loss. **Monotone constraints** guarantee that a higher risk score can never lower PD and a higher strength score can never raise it. Only the early-stopped trees are saved (99 trees), and a regression test checks that the served model reproduces the recorded metrics.

| Metric (held-out test) | Value |
|---|---|
| ROC-AUC | 0.832 |
| KS | 0.513 |
| Brier score | 0.074 |
| Expected calibration error | 0.025 |

**Inference**: run the 15 scores through all 99 trees. Each asks at most 3 yes/no questions and ends at a leaf value. Vertex's path through tree 0:
```text
leverage_score = 0.420 ≥ 0.2805 → litigation = 0.708 ≥ 0.4060 → GST consistency = 0.432 < 0.4802 → leaf +0.0645
```
Then add everything in log-odds and convert:
```text
margin = logit(base rate 0.0977) + Σ leaf values = −2.2233 + 1.9687 = −0.2546
PD     = 1 / (1 + e^(−margin))   = 0.4367  → 43.7 %
```

**Decision policy** (`ScoringService.decision`, aligned with grade bands):

| PD | Grade | Decision |
|---|---|---|
| < 12 % | AAA … BBB | approve |
| 12 % – 22 % | BB, B | review (credit committee) |
| ≥ 22 % | CCC, D | reject |

Limit = exposure × support score (weighted strengths) × max(0.22, 1 − 2.4 × PD). Rate = 9 % + risk premium (2 % + 22 % × PD + 3 % × anomaly, bounded 1–9 %).

### Step 4: SHAP explains the probability

SHAP uses **the same 15 scores** (the borrower's input row) plus **the trained trees**: their split questions, leaf values, and how many training borrowers went down each branch. It does not re-read documents.

**Question answered**: the average borrower's margin is −2.2435 (≈ 9.6 % PD) and Vertex's is −0.2546. How much of that +1.99 gap does each score own?

**Method (Shapley values)**: treat the 15 scores as players in a team. A feature's share is its average marginal effect when it joins every possible group of the other features. When a tree meets a question about a feature that is "hidden" in the current group, it follows **both** branches, weighted by the share of training borrowers that went each way. **TreeSHAP** computes this exactly from the tree structure instead of trying all 2¹⁵ = 32,768 groups. XGBoost implements it natively (`pred_contribs=True`); see `app/ml/pd_model.py`.

*Tiny example:* one tree asks "litigation ≥ 0.406?". 30 % of training borrowers went *yes* (leaf +0.20) and 70 % went *no* (leaf −0.05). Without knowing litigation, the expected output is 0.3·0.20 + 0.7·(−0.05) = +0.025. Knowing Vertex's 0.708 gives +0.20, so litigation's share from this tree is **+0.175**.

**Vertex's result** (log-odds; + raises risk, − lowers it):

| Feature | Value | SHAP |
|---|---|---|
| Litigation risk | 0.708 | **+0.546** |
| Anomaly score | 0.800 | **+0.472** |
| Early warning score | 0.780 | +0.280 |
| GST reconciliation risk | 0.800 | +0.269 |
| Management overlay | 0.094 | +0.256 |
| Governance | 0.551 | +0.221 |
| Cash-flow stability | 0.413 | +0.176 |
| Sector headwinds | 0.920 | +0.109 |
| Promoter risk | 0.950 | +0.097 |
| Risk-flag density | 0.250 | +0.048 |
| GST consistency | 0.432 | +0.039 |
| Document coverage | 0.757 | −0.012 |
| Leverage headroom | 0.420 | −0.090 |
| Identifier coverage | 0.833 | −0.179 |
| Profitability quality | 0.700 | **−0.242** |

```text
−2.2435 (average) + Σ SHAP = −0.2546 = model margin exactly  →  PD 43.7 %
```
Additivity is checked by unit tests for every prediction. (The `shap` package 0.51 gives values within ~6 % of these, but its values do not sum to the XGBoost 3.x margin, so the native XGBoost values are used.)

**SHAP is not a what-if**: changing only Vertex's litigation from 0.708 to 0.18 gives PD 21.5 % instead of 43.7 %. That is a counterfactual, useful for advice. The SHAP value (+0.546) is litigation's *fair share* averaged over all combinations of the other features.

### Step 5: what happens with feature importance

1. **Explain the decision**: the top risks and strengths go into the CAM ("rejected mainly due to litigation risk, transaction anomalies and early-warning signals").
2. **Direct the officer's review**: verify the biggest drivers first (e.g. confirm the NCLT case, ask for an explanation of the ITC excess).
3. **Set targeted covenants** (automatic): anomaly / GST risk → monthly GST-bank reconciliation submission; litigation → immediate notification of legal notices or NCLT filings; early warning → enhanced monitoring on EBITDA or collections.
4. **Tell the borrower what to fix**: use what-if PDs to show which changes would move the decision.
5. **Monitor after disbursal**: the drivers at approval become the early-warning signals to track.
6. **Audit the model** *(next step, not yet built)*: average |SHAP| across the portfolio to check that the model relies on sensible features, and to detect drift, bias and redundant features.

The **evidence search** links reasons to text: the top SHAP drivers and research findings become queries, and MiniLM (or keyword fallback) retrieves the supporting document passages shown in the CAM.

## Synthetic Data

`python -m synthetic_data.generator` (from `backend/`) writes `backend/data/synthetic/`. The values are deterministic: seed 7.

| Persona | Profile | PD | Grade | Decision |
|---|---|---|---|---|
| Sunrise Agro Foods Pvt Ltd | Healthy food processor: clean GST, no litigation | 0.87 % | AAA | approve |
| Meridian Steel Components Ltd | Stressed: falling EBITDA, late GST filings, recovery suit | 13.2 % | BB | review |
| Vertex Tradelinks Pvt Ltd | Fraud-like: GSTR-1/3B gap, excess ITC, round-tripping, NCLT, ED search | 43.7 % | D | reject |

Each pack contains a text annual report PDF, a **scanned (image-only) rating report** that requires OCR, 12 months of GST returns (CSV), a bank statement (CSV) and `application.json` with officer inputs. A public-risk-signal corpus (`research_corpus.jsonl`) includes **look-alike distractor companies** (Sunrise Pharma, Vertex Logistics, Meridian Textiles) to test entity matching. All identifiers are syntactically valid (including the GSTIN check digit) but fictitious. `--training-csv` also exports the 8,000-row PD training population and retrains the model.

## Running and Testing

```bash
cd backend
pip install -r requirements-flask.txt
python -m synthetic_data.generator --training-csv   # demo data + corpus + retrained PD model
python run_flask.py                                 # API on http://127.0.0.1:5000
python demo_synthetic_borrowers.py                  # push the 3 personas through the running API

pytest                                  # full suite: 193 tests, ~30 s
pytest -m unit                          # or: integration | security | e2e | regression | ocr | slow
pytest tests/regression --update-golden # accept an intentional change in decisions
```

| Suite | Tests | Covers |
|---|---|---|
| unit | 147 | NER and GSTIN check digit / OCR repair, GST reconciliation and round-trips, PD model (TreeSHAP additivity, monotonicity, reproducibility), research agent (entity scoping, citations, fallbacks), OCR, ingestion, scoring policy, compliance, CAM |
| integration | 11 | API lifecycle, validation errors, cockpit, re-running decisions, CAM download |
| security | 13 | Path traversal on CAM download, upload filename traversal, disallowed types, oversized uploads (413) |
| e2e | 12 | Three personas from upload to CAM, tampered-PAN detection, latency budgets |
| regression | 9 | Golden decision snapshots per persona; model quality (AUC ≥ 0.78, KS ≥ 0.40, ECE ≤ 0.05); served model reproduces recorded metrics |

`pytest.ini` sets `--basetemp=.pytest_tmp` because the default `%TEMP%\pytest-of-<user>` folder is access-denied on some Windows machines.

## Limitations

- The PD model is trained on a **simulated** portfolio. Retrain and recalibrate on real loan-performance data before any real use.
- The research agent searches a **local synthetic corpus**, not live MCA / e-Courts / news feeds. The connectors and scoring are built so live sources can be plugged in.
- Scores 3–10 use keyword heuristics. Extracting financial ratios from statements would be more reliable.
- Portfolio-level (global) SHAP monitoring is not implemented yet.

## End-to-End Flow

1. Create an application
2. Upload or ingest borrower documents
3. Run decisioning
4. Review:
   - extracted document signals
   - research findings
   - compliance mapping
   - scorecard and explainability
   - generated CAM artifacts

## Setup

### Prerequisites

- Windows machine recommended for the included `.bat` launchers
- Python 3.13 recommended
- Node.js 18+ and npm
- Git

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/Dinesh-Sharma2004/Intelli-credit
cd Intelli-credit
```

### 2. Backend setup

```powershell
cd backend
"C:\Program Files\Python313\python.exe" -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If you want a lighter environment for the current Flask prototype, install only the runtime dependencies actually used by the demo if needed.

### 3. Frontend setup

```powershell
cd ..\frontend
npm install
```

### 4. Environment configuration

The frontend is already configured to target the local Flask API:

```text
frontend/.env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000/api/v1
```

The root `.env` and backend `.env.example` can be used as templates for future expansion.

## Running the Project

### Recommended: one-click demo launcher

From the project root:

```powershell
.\start_demo.bat
```

This opens:
- backend terminal on port `5000`
- frontend terminal on port `3000`
- verification script for the live stack

### Manual backend start

```powershell
cd backend
"C:\Program Files\Python313\python.exe" run_flask.py
```

Backend URL:

```text
http://127.0.0.1:5000/api/v1/health
```

### Manual frontend start

```powershell
cd frontend
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:3000
```

### Important note on Next.js permissions

In some restricted Windows shells, `next dev` may fail with `spawn EPERM`. If that happens, run the frontend terminal as Administrator once and then start:

```powershell
.\start_frontend.bat
```

## Demo Pages

- `/`
- `/documents`
- `/ingestor`
- `/research`
- `/credit-officer`
- `/risk-scoring`
- `/cam-generator`

## Testing and Verification

### Backend smoke tests

```powershell
cd backend
"C:\Program Files\Python313\python.exe" -m pytest          # 193 tests; see "Running and Testing" above
```

### Frontend TypeScript verification

```powershell
cd frontend
npx tsc --noEmit
```

## Running the Attached PDF Pipeline

The repository includes a batch pipeline for the user-provided PDFs.

Run:

```powershell
"C:\Program Files\Python313\python.exe" backend\run_attached_pdf_pipeline.py
```

Outputs include:
- `backend/attached_pdf_pipeline_report.json`
- extracted document signals
- compliance mapping
- scorecard
- explainability metrics

## Explainability Evaluation

Run:

```powershell
"C:\Program Files\Python313\python.exe" backend\evaluate_credit_explainability.py
```

Output:
- `backend/credit_explainability_report.json`

This evaluates:
- extraction grounding proxy for transformer-style extraction
- directional faithfulness and explanation overlap for the XGBoost-style scoring layer

## Generating Demo Summary Reports

Run:

```powershell
"C:\Program Files\Python313\python.exe" backend\generate_demo_summaries.py
```

Outputs:
- `backend/company_wise_pipeline_report.json`
- `backend/judge_demo_summary.md`

## CAM Generation

The backend generates:
- DOCX CAM
- PDF CAM

Artifacts are stored under:

```text
backend/generated_cams/
```

The current formatting includes:
- executive summary
- borrower metadata
- Five Cs assessment
- document review
- secondary research summary
- regulatory mapping
- explainability drivers
- formal credit recommendation

## Indian Regulatory Mapping Included

The backend maps documents and findings to the Indian lending context described in the problem statement:

- Companies Act 2013 / MCA annual filing review
- GSTR-1 vs GSTR-2A/2B vs GSTR-3B reconciliation expectations
- RBI KYC / AML / fraud monitoring expectations
- e-Courts / NCLT / IBC litigation screening
- Credit rating agency review where applicable
- ESG / BRSR style sustainability disclosure relevance where applicable

Reference file:

- [backend/document_requirement_mapping.json](backend/document_requirement_mapping.json)

## Important Implementation Notes

- This repo currently contains both legacy experiments and the active Flask-based hackathon backend.
- The live frontend now uses the Flask API on port `5000`.
- The PD model is a trained XGBoost model, but it is trained on synthetic data; it is not a production-calibrated underwriting model.
- Batch reports built from mixed-company PDF sets are valid as pipeline demonstrations, but not as final borrower-specific underwriting decisions.

## Known Limitations

- OCR (RapidOCR) runs for scanned PDFs and images in the Flask ingestion path; very long scans are limited to 8 pages in demo mode (25 otherwise).
- The research agent retrieves from a local public-risk-signal corpus (synthetic by default) rather than live web sources.
- Some older FastAPI-era files remain in the repo for reference and should not be confused with the active Flask stack.

## Recommended Demo Sequence

1. Start the stack with `start_demo.bat`
2. Open `http://127.0.0.1:3000`
3. Enter borrower details
4. Upload documents on `/documents`
5. Review extraction on `/ingestor`
6. Review research on `/research`
7. Add officer inputs on `/credit-officer`
8. Review recommendation on `/risk-scoring`
9. Download CAM on `/cam-generator`

## Architecture Diagram

See:

- [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)

## Judge Demo Notes

See:

- [DEMO_WALKTHROUGH_NOTES.md](DEMO_WALKTHROUGH_NOTES.md)

## Main Files to Know

- [backend/run_flask.py](backend/run_flask.py)
- [backend/app/factory.py](backend/app/factory.py)
- [backend/app/routes.py](backend/app/routes.py)
- [backend/app/services/document_service.py](backend/app/services/document_service.py)
- [backend/app/services/research_service.py](backend/app/services/research_service.py)
- [backend/app/services/scoring_service.py](backend/app/services/scoring_service.py)
- [backend/app/services/cam_service.py](backend/app/services/cam_service.py)
- [frontend/src/context/CreditApplicationContext.tsx](frontend/src/context/CreditApplicationContext.tsx)
- [frontend/src/lib/intelliCreditApi.ts](frontend/src/lib/intelliCreditApi.ts)

## License

This repository currently does not define a dedicated license file in the updated workflow. Add one before external distribution if required.

## Contact / Ownership

Repository target:

```text
https://github.com/Dinesh-Sharma2004/Intelli-credit
```

This README reflects the current implemented project state in this workspace.
