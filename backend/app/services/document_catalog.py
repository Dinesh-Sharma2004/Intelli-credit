from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentRule:
    document_type: str
    category: str
    problem_statement_pillars: tuple[str, ...]
    indian_regulations: tuple[str, ...]
    expected_signals: tuple[str, ...]


DOCUMENT_RULES: dict[str, DocumentRule] = {
    "annual_report": DocumentRule(
        document_type="annual_report",
        category="unstructured_financial",
        problem_statement_pillars=("data_ingestor", "recommendation_engine"),
        indian_regulations=(
            "Companies Act 2013",
            "MCA annual filing framework",
            "Ind AS / Schedule III",
            "SEBI LODR (if listed)",
        ),
        expected_signals=("auditor observations", "debt profile", "related party transactions", "contingent liabilities"),
    ),
    "sustainability_report": DocumentRule(
        document_type="sustainability_report",
        category="unstructured_esg",
        problem_statement_pillars=("research_agent", "recommendation_engine"),
        indian_regulations=("BRSR / SEBI ESG disclosures", "environmental and labor compliance"),
        expected_signals=("esg incidents", "governance posture", "supply chain resilience"),
    ),
    "gst_filing": DocumentRule(
        document_type="gst_filing",
        category="structured_tax",
        problem_statement_pillars=("data_ingestor", "recommendation_engine"),
        indian_regulations=("CGST Act", "GSTR-1", "GSTR-2A/2B", "GSTR-3B"),
        expected_signals=("sales consistency", "input tax credit mismatch", "circular trading"),
    ),
    "bank_statement": DocumentRule(
        document_type="bank_statement",
        category="structured_cashflow",
        problem_statement_pillars=("data_ingestor", "recommendation_engine"),
        indian_regulations=("RBI KYC/AML expectations", "fraud monitoring", "cash flow validation"),
        expected_signals=("cash churn", "bounced payments", "related party routing", "seasonality"),
    ),
    "rating_report": DocumentRule(
        document_type="rating_report",
        category="external_intelligence",
        problem_statement_pillars=("research_agent", "recommendation_engine"),
        indian_regulations=("SEBI CRA Regulations", "RBI prudential review"),
        expected_signals=("rating outlook", "covenant breaches", "liquidity commentary"),
    ),
    "board_minutes": DocumentRule(
        document_type="board_minutes",
        category="governance",
        problem_statement_pillars=("data_ingestor", "research_agent"),
        indian_regulations=("Companies Act 2013", "board governance and approvals"),
        expected_signals=("capex approval", "stress signals", "management changes"),
    ),
    "legal_notice": DocumentRule(
        document_type="legal_notice",
        category="legal",
        problem_statement_pillars=("data_ingestor", "research_agent", "recommendation_engine"),
        indian_regulations=("e-Courts / NCLT exposure", "IBC risk monitoring"),
        expected_signals=("litigation amount", "counterparty risk", "injunctions"),
    ),
    "generic_pdf": DocumentRule(
        document_type="generic_pdf",
        category="unclassified",
        problem_statement_pillars=("data_ingestor",),
        indian_regulations=("manual review required",),
        expected_signals=("title extraction", "key entity discovery"),
    ),
}


FILENAME_HINTS: dict[str, str] = {
    "annual report": "annual_report",
    "annual-report": "annual_report",
    "sustainability": "sustainability_report",
    "gst": "gst_filing",
    "gstr": "gst_filing",
    "bank": "bank_statement",
    "statement": "bank_statement",
    "rating": "rating_report",
    "board": "board_minutes",
    "legal": "legal_notice",
    "court": "legal_notice",
}


def classify_document(filename: str) -> DocumentRule:
    lowered = Path(filename).name.lower()
    for hint, doc_type in FILENAME_HINTS.items():
        if hint in lowered:
            return DOCUMENT_RULES[doc_type]
    return DOCUMENT_RULES["generic_pdf"]


def compliance_matrix_for_documents(document_names: list[str]) -> list[dict]:
    rows = []
    for document_name in document_names:
        rule = classify_document(document_name)
        rows.append(
            {
                "document_name": document_name,
                "document_type": rule.document_type,
                "category": rule.category,
                "problem_statement_pillars": list(rule.problem_statement_pillars),
                "indian_regulations": list(rule.indian_regulations),
                "expected_signals": list(rule.expected_signals),
            }
        )
    return rows
