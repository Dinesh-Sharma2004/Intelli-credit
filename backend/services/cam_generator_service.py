from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import json
from pathlib import Path

# Document generation
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
except ImportError:
    print("Warning: python-docx not installed")

router = APIRouter()

class BorrowerProfile(BaseModel):
    company_name: str
    cin: str
    sector: str
    years_in_operation: int
    revenue: float
    employees: int

class CAMGeneratorRequest(BaseModel):
    borrower_profile: BorrowerProfile
    financial_summary: Dict[str, float]
    risk_assessment: Dict[str, Any]
    credit_score: float
    loan_limit: float
    interest_rate: float
    shap_drivers: List[Dict[str, Any]]
    qualitative_inputs: Optional[Dict[str, str]] = None

class CAMGeneratorResponse(BaseModel):
    cam_id: str
    status: str
    filename: str
    generation_time: str
    file_url: str
    sections_generated: List[str]

def create_cam_document(request: CAMGeneratorRequest) -> bytes:
    """
    Generate Credit Appraisal Memorandum (CAM) as DOCX
    """
    doc = Document()
    
    # Header
    title = doc.add_heading('CREDIT APPRAISAL MEMORANDUM', 0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    subtitle = doc.add_paragraph(f"Borrower: {request.borrower_profile.company_name}")
    subtitle.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    date_para = doc.add_paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y')}")
    date_para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    
    doc.add_paragraph()  # Blank line
    
    # BORROWER PROFILE
    doc.add_heading('1. BORROWER PROFILE', level=1)
    profile_table = doc.add_table(rows=7, cols=2)
    profile_table.style = 'Light Grid Accent 1'
    
    profile_data = [
        ["Company Name", request.borrower_profile.company_name],
        ["CIN", request.borrower_profile.cin],
        ["Sector", request.borrower_profile.sector],
        ["Years in Operation", str(request.borrower_profile.years_in_operation)],
        ["Annual Revenue", f"₹{request.borrower_profile.revenue/10000000:.2f}Cr"],
        ["Employee Count", str(request.borrower_profile.employees)],
    ]
    
    for i, (key, value) in enumerate(profile_data):
        row = profile_table.rows[i + 1]
        row.cells[0].text = key
        row.cells[1].text = value
    
    doc.add_paragraph()
    
    # FINANCIAL ANALYSIS
    doc.add_heading('2. FINANCIAL ANALYSIS (FY 2023-24)', level=1)
    
    fin_table = doc.add_table(rows=6, cols=2)
    fin_table.style = 'Light Grid Accent 1'
    
    fin_data = [
        ["Revenue", f"₹{request.financial_summary.get('revenue', 0)/10000000:.2f}Cr"],
        ["EBITDA", f"₹{request.financial_summary.get('ebitda', 0)/10000000:.2f}Cr"],
        ["Net Profit", f"₹{request.financial_summary.get('net_profit', 0)/10000000:.2f}Cr"],
        ["Total Debt", f"₹{request.financial_summary.get('total_debt', 0)/10000000:.2f}Cr"],
        ["Cash Reserves", f"₹{request.financial_summary.get('cash_reserves', 0)/10000000:.2f}Cr"],
    ]
    
    for i, (key, value) in enumerate(fin_data):
        row = fin_table.rows[i + 1]
        row.cells[0].text = key
        row.cells[1].text = value
    
    # Key Ratios
    doc.add_heading('Key Ratios:', level=2)
    ratios_text = f"""
    • Debt-to-Equity: {request.financial_summary.get('debt_to_equity', 1.5):.2f}x
    • Interest Coverage: {request.financial_summary.get('interest_coverage', 4.5):.2f}x
    • Current Ratio: {request.financial_summary.get('current_ratio', 1.2):.2f}x
    • EBITDA Margin: {request.financial_summary.get('ebitda_margin', 18.5):.1f}%
    • ROA: {request.financial_summary.get('roa', 12.5):.1f}%
    """
    doc.add_paragraph(ratios_text)
    
    doc.add_paragraph()
    
    # INDUSTRY & SECTOR ANALYSIS
    doc.add_heading('3. INDUSTRY & SECTOR ANALYSIS', level=1)
    
    sector_analysis = f"""
    Sector: {request.borrower_profile.sector}
    
    Market Overview:
    • Market Size: ₹45,000+ Crores
    • Growth Rate: 28% CAGR (2024-2028)
    • Key Drivers: Digital transformation, Enterprise cloud migration, Edge computing
    
    Competitive Position:
    • Market Share: ~3.2% (India market)
    • Primary Markets: Enterprise, Mid-market
    • Geographic Presence: 8 countries
    
    Sector Risks:
    • Increasing competition from hyperscalers
    • Regulatory uncertainty in data residency
    • Talent acquisition challenges
    • Commodity pricing pressure
    
    Opportunities:
    • High growth in enterprise cloud adoption
    • Government digitalization initiatives
    • AI/ML integration opportunities
    • Edge computing expansion
    """
    doc.add_paragraph(sector_analysis)
    
    doc.add_paragraph()
    
    # FIVE Cs OF CREDIT ANALYSIS
    doc.add_heading('4. FIVE Cs OF CREDIT ANALYSIS', level=1)
    
    five_cs = """
    CHARACTER (Management Quality):
    ✓ Experienced management team with 15+ years in technology sector
    ✓ Strong board composition with industry veterans
    ✓ Compliance record: Excellent (No regulatory violations)
    ✓ Assessment: STRONG
    
    CAPACITY (Repayment Ability):
    ✓ Revenue Growth: 32% YoY
    ✓ Operating Margins: 18.5% (Healthy)
    ✓ Interest Coverage: 4.5x (Adequate)
    ✓ Cash Generation: Strong and consistent
    ✓ Assessment: STRONG
    
    CAPITAL (Financial Position):
    ✓ Debt-to-Equity: 1.5x (Moderate)
    ✓ Cash Reserves: Adequate
    ✓ Working Capital: Positive and stable
    ✓ Reserves & Surplus: Growing
    ✓ Assessment: ADEQUATE
    
    COLLATERAL (Security):
    ✓ Customer Contracts: Long-term agreements
    ✓ Receivables Quality: Good (90+ days conversion)
    ✓ Tangible Assets: Moderate
    ✓ Market Value: Strong (Tech sector positively valued)
    ✓ Assessment: MODERATE
    
    COVENANTS (Terms & Conditions):
    ✓ Recommended Loan Limit: ₹15.50 Crores
    ✓ Tenor: 60 months
    ✓ Security: Pledge of assets + Personal guarantee
    ✓ Financial Covenants: Debt service coverage ratio >1.5x
    ✓ Reporting Requirements: Quarterly financials + Half-yearly reviews
    """
    doc.add_paragraph(five_cs)
    
    doc.add_paragraph()
    
    # RISK ASSESSMENT
    doc.add_heading('5. RISK ASSESSMENT & MITIGATION', level=1)
    
    risk_table = doc.add_table(rows=4, cols=3)
    risk_table.style = 'Light Grid Accent 1'
    
    # Header
    hdr_cells = risk_table.rows[0].cells
    hdr_cells[0].text = 'Risk Factor'
    hdr_cells[1].text = 'Assessment'
    hdr_cells[2].text = 'Mitigation'
    
    risk_data = [
        ["Litigation Exposure", "MEDIUM-LOW", "Legal review of ongoing cases; Quarterly updates"],
        ["Industry Competition", "MEDIUM", "Strong market position; Diversified customer base"],
        ["Market Concentration", "MEDIUM", "Top 5 customer concentration at 35%; Monitor quarterly"],
    ]
    
    for i, (risk, assess, mitig) in enumerate(risk_data):
        row = risk_table.rows[i + 1]
        row.cells[0].text = risk
        row.cells[1].text = assess
        row.cells[2].text = mitig
    
    doc.add_paragraph()
    
    # CREDIT SCORING
    doc.add_heading('6. CREDIT SCORING & RECOMMENDATION', level=1)
    
    scoring_table = doc.add_table(rows=6, cols=2)
    scoring_table.style = 'Light Grid Accent 1'
    
    score_data = [
        ["Probability of Default (PD)", f"{request.credit_score:.2%}"],
        ["Credit Grade", "A" if request.credit_score < 0.08 else "BBB"],
        ["Recommended Loan Limit", f"₹{request.loan_limit/10000000:.2f}Cr"],
        ["Recommended Interest Rate", f"{request.interest_rate*100:.2f}%"],
        ["Tenor", "60 months"],
        ["Risk Rating", "MEDIUM-LOW"],
    ]
    
    for i, (key, value) in enumerate(score_data):
        row = scoring_table.rows[i]
        row.cells[0].text = key
        row.cells[1].text = value
    
    doc.add_paragraph()
    
    # TOP RISK DRIVERS
    doc.add_heading('Top Risk Drivers:', level=2)
    for i, driver in enumerate(request.shap_drivers[:3], 1):
        doc.add_paragraph(
            f"{i}. {driver.get('feature', 'Risk')} - Impact: {driver.get('impact', 'Negative')}",
            style='List Number'
        )
    
    doc.add_paragraph()
    
    # FINAL RECOMMENDATION
    doc.add_heading('7. FINAL RECOMMENDATION', level=1)
    
    recommendation = f"""
    Based on the comprehensive credit analysis, we RECOMMEND APPROVAL of the credit facility with the following terms:
    
    Loan Amount: ₹{request.loan_limit/10000000:.2f} Crores
    Interest Rate: {request.interest_rate*100:.2f}% per annum
    Tenor: 60 months
    Repayment: EMI basis
    Security: Pledge of assets + Personal guarantee of promoters
    
    Rationale:
    ✓ Strong financial performance with 32% revenue growth
    ✓ Healthy operating margins and profitability
    ✓ Experienced management team in growing sector
    ✓ Manageable debt levels and good interest coverage
    ✓ Moderate litigation exposure with adequate mechanisms for monitoring
    
    Key Conditions:
    • Quarterly financial reporting and compliance certification
    • Half-yearly review meetings
    • Maintenance of debt service coverage ratio >1.5x
    • Consent for property encumbrance/hypothecation
    • Insurance coverage for key assets
    
    This facility is suitable for the company's growth capital requirements and is aligned with our risk appetite.
    """
    doc.add_paragraph(recommendation)
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    # Footer
    footer_para = doc.add_paragraph("---")
    footer_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    footer_text = doc.add_paragraph(
        f"CAM Generated by Intelli-Credit Engine | {datetime.now().strftime('%d-%m-%Y %H:%M:%S UTC')}"
    )
    footer_text.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    footer_text.runs[0].font.size = Pt(9)
    footer_text.runs[0].font.italic = True
    
    # Save to bytes
    file_bytes = io.BytesIO()
    doc.save(file_bytes)
    file_bytes.seek(0)
    
    return file_bytes.getvalue()

@router.post("/generate", response_model=CAMGeneratorResponse)
async def generate_cam(request: CAMGeneratorRequest) -> CAMGeneratorResponse:
    """
    Generate Credit Appraisal Memorandum
    """
    try:
        # Generate document
        doc_bytes = create_cam_document(request)
        
        # Save to documents directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CAM_{request.borrower_profile.company_name.replace(' ', '_')}_{timestamp}.docx"
        
        # Create documents directory if it doesn't exist
        docs_dir = Path("./generated_cams")
        docs_dir.mkdir(exist_ok=True)
        
        filepath = docs_dir / filename
        
        with open(filepath, "wb") as f:
            f.write(doc_bytes)
        
        return CAMGeneratorResponse(
            cam_id=f"CAM_{timestamp}",
            status="COMPLETED",
            filename=filename,
            generation_time=datetime.now().isoformat(),
            file_url=f"/api/cam/download/{filename}",
            sections_generated=[
                "Borrower Profile",
                "Financial Analysis",
                "Industry & Sector Analysis",
                "Five Cs of Credit",
                "Risk Assessment",
                "Credit Scoring",
                "Recommendation"
            ]
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CAM generation failed: {str(e)}")

@router.get("/download/{filename}")
async def download_cam(filename: str):
    """
    Download generated CAM document
    """
    try:
        filepath = Path("./generated_cams") / filename
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/template")
async def get_cam_template():
    """
    Get CAM template structure
    """
    return {
        "template_name": "Standard Credit Appraisal Memorandum",
        "sections": [
            {
                "number": 1,
                "title": "Borrower Profile",
                "required_fields": ["company_name", "cin", "sector", "revenue"]
            },
            {
                "number": 2,
                "title": "Financial Analysis",
                "required_fields": ["revenue", "ebitda", "debt", "cash"]
            },
            {
                "number": 3,
                "title": "Industry Analysis",
                "required_fields": ["sector_overview", "growth_drivers", "risks"]
            },
            {
                "number": 4,
                "title": "Five Cs of Credit",
                "required_fields": ["character", "capacity", "capital", "collateral", "covenants"]
            },
            {
                "number": 5,
                "title": "Risk Assessment",
                "required_fields": ["risk_factors", "severity", "mitigation"]
            },
            {
                "number": 6,
                "title": "Credit Scoring",
                "required_fields": ["pd_score", "grade", "loan_limit", "rate"]
            },
            {
                "number": 7,
                "title": "Recommendation",
                "required_fields": ["approval_status", "terms", "conditions"]
            }
        ],
        "output_formats": ["DOCX", "PDF"]
    }

@router.get("/preview/{company_name}")
async def get_cam_preview(company_name: str):
    """
    Get CAM preview without generating full document
    """
    return {
        "company_name": company_name,
        "preview_sections": {
            "borrower_profile": f"Section 1: Profile for {company_name}",
            "financial_summary": "Section 2: Latest financial performance",
            "sector_analysis": "Section 3: Industry positioning",
            "five_cs": "Section 4: Detailed credit analysis",
            "recommendation": "Section 7: Final approval recommendation"
        },
        "can_proceed": True
    }
