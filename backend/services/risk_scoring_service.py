from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import numpy as np

router = APIRouter()

class FinancialMetrics(BaseModel):
    revenue: float
    ebitda: float
    net_profit: float
    total_debt: float
    cash_reserves: float
    current_assets: float
    current_liabilities: float

class SHAPValue(BaseModel):
    feature: str
    contribution: float
    base_value: float
    shap_value: float

class RiskScoreResult(BaseModel):
    probability_of_default: float
    credit_grade: str
    recommended_loan_limit: float
    recommended_interest_rate: float
    shap_explanations: List[SHAPValue]
    risk_drivers: List[Dict[str, Any]]
    positive_drivers: List[Dict[str, Any]]
    confidence_score: float
    scoring_timestamp: str

class CreditProfile(BaseModel):
    company_name: str
    financial_metrics: FinancialMetrics
    industry_risk: float
    litigation_risk: float
    management_quality: float
    operational_risk: float

# Mock XGBoost model predictions
def calculate_financial_ratios(metrics: FinancialMetrics) -> Dict[str, float]:
    """
    Calculate financial ratios from metrics
    """
    return {
        "debt_to_equity": metrics.total_debt / (metrics.net_profit + metrics.cash_reserves + 1),
        "interest_coverage": metrics.ebitda / (metrics.total_debt * 0.08 + 1),
        "current_ratio": metrics.current_assets / (metrics.current_liabilities + 1),
        "roa": metrics.net_profit / (metrics.current_assets + 1),
        "roe": metrics.net_profit / (metrics.cash_reserves + 1),
        "revenue_growth": 0.32,  # Mock 32% growth
        "margin_quality": metrics.ebitda / metrics.revenue if metrics.revenue > 0 else 0
    }

def generate_shap_values(metrics: FinancialMetrics, profile: CreditProfile) -> List[SHAPValue]:
    """
    Generate SHAP explanations for model predictions
    """
    ratios = calculate_financial_ratios(metrics)
    
    shap_values = [
        SHAPValue(
            feature="Debt-to-Equity Ratio",
            contribution=-0.15,
            base_value=1.8,
            shap_value=-0.12
        ),
        SHAPValue(
            feature="Interest Coverage",
            contribution=0.22,
            base_value=4.5,
            shap_value=0.18
        ),
        SHAPValue(
            feature="Current Ratio",
            contribution=0.18,
            base_value=1.2,
            shap_value=0.15
        ),
        SHAPValue(
            feature="Revenue Growth Rate",
            contribution=0.25,
            base_value=0.32,
            shap_value=0.20
        ),
        SHAPValue(
            feature="EBITDA Margin",
            contribution=0.20,
            base_value=0.185,
            shap_value=0.16
        ),
        SHAPValue(
            feature="Industry Risk Score",
            contribution=-0.12,
            base_value=profile.industry_risk,
            shap_value=-0.10
        ),
        SHAPValue(
            feature="Management Quality",
            contribution=0.15,
            base_value=profile.management_quality,
            shap_value=0.12
        ),
        SHAPValue(
            feature="Litigation Exposure",
            contribution=-0.08,
            base_value=profile.litigation_risk,
            shap_value=-0.06
        )
    ]
    
    return shap_values

def predict_probability_of_default(profile: CreditProfile) -> float:
    """
    Predict PD using mock XGBoost model
    """
    # Simulate XGBoost prediction
    base_pd = 0.08  # 8% base PD
    
    # Adjust based on risk factors
    pd = base_pd
    pd -= profile.financial_metrics.net_profit / (profile.financial_metrics.revenue + 1) * 0.03
    pd += profile.litigation_risk * 0.02
    pd -= (profile.management_quality / 10) * 0.02
    pd += profile.industry_risk * 0.01
    
    # Ensure PD is within bounds
    return max(0.01, min(0.30, pd))

def calculate_recommended_loan_limit(metrics: FinancialMetrics, pd: float) -> float:
    """
    Calculate recommended loan limit based on financials and PD
    """
    # Base loan multiple varies by credit quality
    if pd < 0.05:
        base_multiple = 2.5  # High quality
    elif pd < 0.10:
        base_multiple = 2.0  # Medium-high quality
    elif pd < 0.15:
        base_multiple = 1.5  # Medium quality
    else:
        base_multiple = 1.0  # Lower quality
    
    # Calculate based on revenue and EBITDA
    revenue_based = metrics.revenue * 0.15
    ebitda_based = metrics.ebitda * 2.0
    
    recommended_limit = min(revenue_based, ebitda_based) * base_multiple
    
    return round(recommended_limit, 2)

def calculate_interest_rate(pd: float, base_rate: float = 0.09) -> float:
    """
    Calculate interest rate based on PD
    """
    # Risk premium = 2-5% based on PD
    risk_premium = pd * 15  # Scale PD to risk premium
    
    return round(base_rate + risk_premium, 4)

def calculate_credit_grade(pd: float) -> str:
    """
    Map PD to credit grade
    """
    if pd < 0.03:
        return "AAA"
    elif pd < 0.05:
        return "AA"
    elif pd < 0.08:
        return "A"
    elif pd < 0.12:
        return "BBB"
    elif pd < 0.18:
        return "BB"
    else:
        return "B"

@router.post("/calculate", response_model=RiskScoreResult)
async def calculate_risk_score(profile: CreditProfile) -> RiskScoreResult:
    """
    Calculate comprehensive risk score and loan recommendations
    """
    try:
        # Calculate PD
        pd = predict_probability_of_default(profile)
        
        # Calculate credit grade
        grade = calculate_credit_grade(pd)
        
        # Calculate loan limit
        loan_limit = calculate_recommended_loan_limit(profile.financial_metrics, pd)
        
        # Calculate interest rate
        interest_rate = calculate_interest_rate(pd)
        
        # Generate SHAP values
        shap_values = generate_shap_values(profile.financial_metrics, profile)
        
        # Identify risk drivers
        risk_drivers = [
            {
                "factor": "Debt-to-Equity Ratio",
                "value": 1.8,
                "threshold": 1.5,
                "risk_level": "MEDIUM",
                "impact": "Negative"
            },
            {
                "factor": "Litigation Exposure",
                "value": 2,
                "cases_active": 1,
                "risk_level": "MEDIUM-LOW",
                "impact": "Negative"
            },
            {
                "factor": "Industry Competitiveness",
                "value": 0.68,
                "benchmark": 0.75,
                "risk_level": "MEDIUM",
                "impact": "Negative"
            }
        ]
        
        # Identify positive drivers
        positive_drivers = [
            {
                "factor": "Revenue Growth",
                "value": 0.32,
                "benchmark": 0.15,
                "performance": "STRONG",
                "impact": "Positive"
            },
            {
                "factor": "EBITDA Margin",
                "value": 0.185,
                "benchmark": 0.12,
                "performance": "STRONG",
                "impact": "Positive"
            },
            {
                "factor": "Interest Coverage Ratio",
                "value": 4.5,
                "benchmark": 3.0,
                "performance": "HEALTHY",
                "impact": "Positive"
            },
            {
                "factor": "Management Quality",
                "value": 7.5,
                "benchmark": 6.0,
                "performance": "ABOVE AVERAGE",
                "impact": "Positive"
            }
        ]
        
        return RiskScoreResult(
            probability_of_default=round(pd, 4),
            credit_grade=grade,
            recommended_loan_limit=loan_limit,
            recommended_interest_rate=interest_rate,
            shap_explanations=shap_values,
            risk_drivers=risk_drivers,
            positive_drivers=positive_drivers,
            confidence_score=0.92,
            scoring_timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Risk scoring failed: {str(e)}")

@router.get("/model-info")
async def get_model_information():
    """
    Get information about the risk scoring model
    """
    return {
        "model_type": "XGBoost",
        "model_version": "v2.1.0",
        "training_date": "2024-01-15",
        "training_samples": 45000,
        "features_count": 42,
        "model_accuracy": 0.87,
        "auc_score": 0.92,
        "calibration_status": "EXCELLENT",
        "last_validation": "2024-02-28"
    }

@router.post("/batch-score")
async def batch_score_companies(companies: List[CreditProfile]):
    """
    Score multiple companies in batch
    """
    results = []
    for company in companies:
        pd = predict_probability_of_default(company)
        grade = calculate_credit_grade(pd)
        loan_limit = calculate_recommended_loan_limit(company.financial_metrics, pd)
        rate = calculate_interest_rate(pd)
        
        results.append({
            "company_name": company.company_name,
            "pd": round(pd, 4),
            "credit_grade": grade,
            "loan_limit": loan_limit,
            "interest_rate": rate
        })
    
    return results

@router.get("/feature-importance")
async def get_feature_importance():
    """
    Get feature importance from the model
    """
    return {
        "top_features": [
            {"feature": "Debt-to-Equity Ratio", "importance": 0.18},
            {"feature": "Revenue Growth", "importance": 0.16},
            {"feature": "Interest Coverage", "importance": 0.14},
            {"feature": "Current Ratio", "importance": 0.12},
            {"feature": "EBITDA Margin", "importance": 0.11},
            {"feature": "Industry Risk", "importance": 0.09},
            {"feature": "Management Quality", "importance": 0.08},
            {"feature": "Litigation Risk", "importance": 0.07},
            {"feature": "Working Capital Ratio", "importance": 0.05}
        ],
        "total_features": 42
    }
