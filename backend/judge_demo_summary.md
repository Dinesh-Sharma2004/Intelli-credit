# Intelli-Credit Credit Assessment Summary

## 1. Executive Overview
This report summarises the Intelli-Credit backend pipeline across the attached document set, including document extraction, secondary research, regulatory mapping, and explainable scoring.

- Total documents processed: `8`
- Document composition: `annual reports 4`, `sustainability reports 1`, `generic PDFs 3`
- Document-level risk flags identified: `6`

## 2. Credit Recommendation
- Recommended decision: `APPROVE`
- Risk grade: `A`
- Probability of default: `2.00%`
- Recommended sanction limit: `₹13.98 Cr`
- Recommended pricing: `9.50%`
- Decision summary: Decision APPROVE with PD 2.00%. Primary drivers: Litigation risk (negative_to_credit), Sector headwinds (negative_to_credit), Profitability quality (positive_to_credit).

## 3. Explainability Summary
- Directional faithfulness of score explanations: `1`
- Top-3 explanation overlap on recomputation: `1.0`

### Principal score drivers
- `Litigation risk`: `+0.1056` (Adverse)
- `Sector headwinds`: `+0.0620` (Adverse)
- `Profitability quality`: `-0.0384` (Supportive)
- `Risk-flag density`: `+0.0270` (Adverse)
- `Governance`: `-0.0216` (Supportive)

## 4. Extraction Quality
- Average overall grounding: `0.8715`
- Identifier grounding: `1.0`
- Keyword grounding: `0.9896`
- Risk-flag grounding: `0.625`

## 5. Company-Wise View
### About Kinara Capital
- Documents reviewed: `1`
- Document types: `annual_report`
- Average extraction confidence: `0.8`
- Average grounding score: `0.6667`
- Key risk flags: `Fraud wording detected`
- `b06e9f17-1f92-49f1-99a2-0adbadcc78d6_fy24-annual-report-kinara-capital.pdf` [annual_report] confidence `0.8`, grounding `0.6667`

### Vivriti Capital
- Documents reviewed: `2`
- Document types: `annual_report`
- Average extraction confidence: `0.89`
- Average grounding score: `0.8195`
- Key risk flags: `NPA wording detected`
- `230d73d3-5fc7-4301-892b-8a51e377d4f1_Annual Report FY 2024-25.pdf` [annual_report] confidence `0.98`, grounding `1.0`
- `40db794c-7d35-40ec-b8df-47eb27b351cf_VCL-ANNUAL REPORT FINAL.pdf` [annual_report] confidence `0.8`, grounding `0.6389`

### Vivriti Capital Private Limited
- Documents reviewed: `1`
- Document types: `annual_report`
- Average extraction confidence: `0.98`
- Average grounding score: `1.0`
- Key risk flags: `None reported`
- `06330e86-16f5-4169-8b9e-e63e5c6e1dcb_Consolidated Annual report_FY 2022-23.pdf` [annual_report] confidence `0.98`, grounding `1.0`

### Vivriti Capital Limited
- Documents reviewed: `1`
- Document types: `sustainability_report`
- Average extraction confidence: `0.8`
- Average grounding score: `1.0`
- Key risk flags: `Default-related reference detected`
- `d93c4915-3c1c-4524-9cd8-d8fc13a73f1e_Vivriti Sustainability Report 2024-25 2 Sep.pdf` [sustainability_report] confidence `0.8`, grounding `1.0`

### 7dda55e4-9c3a-4696-90e6-6a0e3652a8bb_1754051517
- Documents reviewed: `1`
- Document types: `generic_pdf`
- Average extraction confidence: `0.7`
- Average grounding score: `1.0`
- Key risk flags: `None reported`
- `7dda55e4-9c3a-4696-90e6-6a0e3652a8bb_1754051517.pdf` [generic_pdf] confidence `0.7`, grounding `1.0`

### Moneyboxx Capital Private Limited
- Documents reviewed: `1`
- Document types: `generic_pdf`
- Average extraction confidence: `0.98`
- Average grounding score: `1.0`
- Key risk flags: `None reported`
- `c6253418-2372-4afe-b345-28379667c16c_1754045722.pdf` [generic_pdf] confidence `0.98`, grounding `1.0`

### Moneyboxx Finance Limited
- Documents reviewed: `1`
- Document types: `generic_pdf`
- Average extraction confidence: `0.8`
- Average grounding score: `0.6667`
- Key risk flags: `Default-related reference detected, NPA wording detected`
- `c0541a6e-378d-43ef-a935-2a13ddc8d26e_1756892129.pdf` [generic_pdf] confidence `0.8`, grounding `0.6667`

## 6. Regulatory Coverage
- `GST-RECON`: `pending_review` - GST Reconciliation - GSTR-1 vs GSTR-2A/2B vs GSTR-3B
- `MCA-FILING`: `evidence_mapped` - Companies Act 2013 / MCA Annual Filing Review
- `RBI-KYC-AML`: `pending_review` - RBI KYC, AML, and fraud-monitoring expectations
- `LIT-SEARCH`: `evidence_mapped` - e-Courts / NCLT / IBC litigation search
- `CRA-RATING`: `not_applicable` - Credit rating agency report review

## 7. Important Caveat
- The attached PDF set spans multiple inferred borrower entities. Accordingly, the aggregated score shown here is suitable for demonstration of pipeline capability, but not for final underwriting of a single borrower without borrower-specific document segregation.