from __future__ import annotations

from .document_catalog import classify_document


BASE_COMPLIANCE_RULES = [
    {
        "regulation_code": "GST-RECON",
        "regulation_name": "GST Reconciliation - GSTR-1 vs GSTR-2A/2B vs GSTR-3B",
        "applicability": "core",
        "status": "pending_review",
        "rationale": "Required when GST filings or GST references exist to detect inflated turnover and circular trading.",
    },
    {
        "regulation_code": "MCA-FILING",
        "regulation_name": "Companies Act 2013 / MCA Annual Filing Review",
        "applicability": "core",
        "status": "pending_review",
        "rationale": "Validate incorporation status, annual returns, charges, and director changes for all corporate borrowers.",
    },
    {
        "regulation_code": "RBI-KYC-AML",
        "regulation_name": "RBI KYC, AML, and fraud-monitoring expectations",
        "applicability": "core",
        "status": "pending_review",
        "rationale": "Bank statement and related-party flow analysis should support AML-style exception detection.",
    },
    {
        "regulation_code": "LIT-SEARCH",
        "regulation_name": "e-Courts / NCLT / IBC litigation search",
        "applicability": "core",
        "status": "pending_review",
        "rationale": "Secondary research must identify legal disputes and insolvency signals.",
    },
    {
        "regulation_code": "CRA-RATING",
        "regulation_name": "Credit rating agency report review",
        "applicability": "conditional",
        "status": "pending_review",
        "rationale": "Applicable when external rating reports are available or the borrower is rated.",
    },
]


class ComplianceService:
    def build_checks(self, document_names: list[str], research_hits: list[dict], anomaly_result: dict | None = None) -> list[dict]:
        evidence_by_code: dict[str, list[str]] = {rule["regulation_code"]: [] for rule in BASE_COMPLIANCE_RULES}
        for name in document_names:
            rule = classify_document(name)
            if rule.document_type == "gst_filing":
                evidence_by_code["GST-RECON"].append(name)
            if rule.document_type == "bank_statement":
                evidence_by_code["RBI-KYC-AML"].append(name)
            if rule.document_type == "rating_report":
                evidence_by_code["CRA-RATING"].append(name)
            if rule.document_type == "annual_report":
                evidence_by_code["MCA-FILING"].append(name)
        for hit in research_hits:
            if hit["source_name"] == "MCA":
                evidence_by_code["MCA-FILING"].append(hit["title"])
            if hit["source_name"] == "e-Courts":
                evidence_by_code["LIT-SEARCH"].append(hit["title"])
        reconciliation = (anomaly_result or {}).get("gst_reconciliation") or {}
        identity_flags = ((anomaly_result or {}).get("identity_checks") or {}).get("flags", [])

        checks = []
        for base in BASE_COMPLIANCE_RULES:
            evidence = evidence_by_code.get(base["regulation_code"], [])
            status = "evidence_mapped" if evidence else "pending_review"
            if base["regulation_code"] == "CRA-RATING" and not evidence:
                status = "not_applicable"
            if base["regulation_code"] == "GST-RECON" and reconciliation:
                evidence = evidence + reconciliation.get("flags", [])
                status = "exception_found" if reconciliation.get("flags") else "reconciled"
            if base["regulation_code"] == "RBI-KYC-AML" and identity_flags:
                evidence = evidence + identity_flags
                status = "exception_found"
            checks.append({**base, "status": status, "evidence": evidence})
        return checks
