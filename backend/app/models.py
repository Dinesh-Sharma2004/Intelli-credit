from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CreditApplication(TimestampMixin, Base):
    __tablename__ = "credit_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    borrower_name: Mapped[str] = mapped_column(String(255), index=True)
    borrower_pan: Mapped[str | None] = mapped_column(String(16), nullable=True)
    borrower_gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    requested_amount: Mapped[float] = mapped_column(Float, default=0.0)
    requested_tenor_months: Mapped[int] = mapped_column(Integer, default=12)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents = relationship("SourceDocument", back_populates="application", cascade="all, delete-orphan")
    research_hits = relationship("ResearchFinding", back_populates="application", cascade="all, delete-orphan")
    compliance_checks = relationship(
        "ComplianceCheck", back_populates="application", cascade="all, delete-orphan"
    )
    scorecard = relationship(
        "RiskScorecard", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    cam_artifact = relationship(
        "CamArtifact", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )


class SourceDocument(TimestampMixin, Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("credit_applications.id"))
    document_name: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80))
    source_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(40), default="pending")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    application = relationship("CreditApplication", back_populates="documents")


class ResearchFinding(TimestampMixin, Base):
    __tablename__ = "research_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("credit_applications.id"))
    source_name: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str] = mapped_column(String(500))
    finding_type: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[str] = mapped_column(String(20), default="neutral")
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    application = relationship("CreditApplication", back_populates="research_hits")


class ComplianceCheck(TimestampMixin, Base):
    __tablename__ = "compliance_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("credit_applications.id"))
    regulation_code: Mapped[str] = mapped_column(String(80))
    regulation_name: Mapped[str] = mapped_column(String(255))
    applicability: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    rationale: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)

    application = relationship("CreditApplication", back_populates="compliance_checks")


class RiskScorecard(TimestampMixin, Base):
    __tablename__ = "risk_scorecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("credit_applications.id"), unique=True)
    model_version: Mapped[str] = mapped_column(String(80))
    probability_of_default: Mapped[float] = mapped_column(Float)
    risk_grade: Mapped[str] = mapped_column(String(20))
    recommended_limit: Mapped[float] = mapped_column(Float)
    recommended_rate: Mapped[float] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(20))
    score_breakdown: Mapped[dict] = mapped_column(JSON)
    shap_explanation: Mapped[list] = mapped_column(JSON)
    feature_vector: Mapped[dict] = mapped_column(JSON)
    explanation_summary: Mapped[str] = mapped_column(Text)
    human_override: Mapped[bool] = mapped_column(Boolean, default=False)

    application = relationship("CreditApplication", back_populates="scorecard")


class CamArtifact(TimestampMixin, Base):
    __tablename__ = "cam_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("credit_applications.id"), unique=True)
    docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    memo_json: Mapped[dict] = mapped_column(JSON)
    generation_status: Mapped[str] = mapped_column(String(20), default="pending")

    application = relationship("CreditApplication", back_populates="cam_artifact")
