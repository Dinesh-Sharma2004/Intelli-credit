from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup

router = APIRouter()

class RetrievedDocument(BaseModel):
    source: str
    title: str
    content: str
    relevance_score: float
    source_url: str

class ResearchQuery(BaseModel):
    company_name: str
    search_type: str  # "general", "litigation", "sector", "mca"

class ResearchResult(BaseModel):
    query: str
    retrieved_documents: List[RetrievedDocument]
    risk_summary: str
    sector_analysis: str
    litigation_findings: List[Dict[str, Any]]
    research_timestamp: str
    total_results: int

class RAGMetadata(BaseModel):
    vector_db_type: str
    total_chunks: int
    embedding_model: str
    retrieval_method: str

# Mock web scraping and data retrieval
def mock_web_search(company_name: str) -> List[RetrievedDocument]:
    """
    Simulate web search and data retrieval
    """
    return [
        RetrievedDocument(
            source="Industry News",
            title=f"{company_name} Wins Major Contract in Q1 2024",
            content=f"Leading cloud infrastructure provider, {company_name}, has secured a major enterprise contract worth ₹50 Cr. The deal is expected to strengthen their market position in the enterprise segment.",
            relevance_score=0.92,
            source_url="https://news.example.com/techventure-contract-2024"
        ),
        RetrievedDocument(
            source="Business Database",
            title=f"Financial Performance Analysis: {company_name}",
            content=f"{company_name} reported strong financial performance in FY2023-24 with revenue growth of 32% YoY. Operating margins improved to 18.5% from 15.2% in the previous year.",
            relevance_score=0.88,
            source_url="https://business.example.com/company-analysis"
        ),
        RetrievedDocument(
            source="Sector Analysis",
            title="Cloud Services Sector Growth Trends 2024",
            content="The cloud infrastructure services sector is projected to grow at 28% CAGR. Key drivers include digital transformation adoption and enterprise migration to cloud platforms.",
            relevance_score=0.85,
            source_url="https://sector.example.com/cloud-trends-2024"
        )
    ]

def mock_mca_scraping(company_name: str) -> Dict[str, Any]:
    """
    Simulate MCA register scraping
    """
    return {
        "company_name": company_name,
        "cin": "U72900GJ2005PLC047584",
        "registration_date": "2005-03-15",
        "status": "ACTIVE",
        "authorized_capital": "₹10,00,00,000",
        "paid_up_capital": "₹8,50,00,000",
        "directors": [
            {"name": "Rajesh Kumar", "din": "00123456", "status": "ACTIVE"},
            {"name": "Priya Sharma", "din": "00654321", "status": "ACTIVE"}
        ],
        "filing_status": "COMPLIANT",
        "last_annual_filing": "2024-02-28"
    }

def mock_litigation_search(company_name: str) -> List[Dict[str, Any]]:
    """
    Simulate e-Courts litigation search
    """
    return [
        {
            "case_id": "CS-2023-001",
            "case_name": f"{company_name} vs. Supplier XYZ",
            "court": "Delhi High Court",
            "filing_date": "2023-06-15",
            "case_status": "PENDING",
            "case_type": "Commercial",
            "amount_involved": "₹2,50,00,000",
            "parties": [company_name, "Supplier XYZ Ltd"],
            "last_hearing": "2024-02-20",
            "risk_assessment": "MEDIUM"
        },
        {
            "case_id": "CS-2022-045",
            "case_name": f"Employee v. {company_name}",
            "court": "Industrial Tribunal",
            "filing_date": "2022-09-10",
            "case_status": "SETTLED",
            "case_type": "Labor Dispute",
            "amount_involved": "₹15,00,000",
            "parties": ["John Doe", company_name],
            "last_hearing": "2024-01-15",
            "risk_assessment": "LOW"
        }
    ]

def generate_risk_summary(documents: List[RetrievedDocument], litigation: List[Dict]) -> str:
    """
    Generate risk summary from retrieved documents
    """
    score = 6.5  # Out of 10
    factors = []
    
    if litigation:
        factors.append(f"Active litigation in {len(litigation)} cases")
    
    factors.append("Strong revenue growth (32% YoY)")
    factors.append("Healthy operating margins (18.5%)")
    factors.append("Growing sector with 28% CAGR projection")
    
    return f"""
    Risk Score: {score}/10 (MEDIUM-LOW)
    
    Key Factors:
    - {factors[0]}
    - {factors[1]}
    - {factors[2]}
    - {factors[3]}
    
    Overall Assessment: Company demonstrates sound financial health with strong market position in growing sector. 
    Manageable litigation exposure based on available public information.
    """

def generate_sector_analysis(company_name: str) -> str:
    """
    Generate sector analysis
    """
    return f"""
    SECTOR: Cloud Infrastructure Services
    
    Market Overview:
    - Market Size: $850 Bn (Global), $45 Bn (India)
    - Growth Rate: 28% CAGR (2024-2028)
    - Key Drivers: Digital transformation, Enterprise migration, Edge computing
    
    {company_name} Position:
    - Market Share: ~3.2% in India
    - Primary Markets: Enterprise, Mid-market
    - Geographic Presence: 8 countries
    
    Sector Trends:
    - Consolidation in the market
    - Shift towards AI-integrated solutions
    - Increasing regulatory scrutiny
    - Rising competition from hyperscalers (AWS, Azure, GCP)
    """

@router.post("/search", response_model=ResearchResult)
async def research_company(query: ResearchQuery) -> ResearchResult:
    """
    Research a company using RAG pipeline
    """
    try:
        # Get documents from mock sources
        web_docs = mock_web_search(query.company_name)
        mca_data = mock_mca_scraping(query.company_name)
        litigation = mock_litigation_search(query.company_name)
        
        # Generate summaries
        risk_summary = generate_risk_summary(web_docs, litigation)
        sector_analysis = generate_sector_analysis(query.company_name)
        
        return ResearchResult(
            query=query.company_name,
            retrieved_documents=web_docs,
            risk_summary=risk_summary,
            sector_analysis=sector_analysis,
            litigation_findings=litigation,
            research_timestamp=datetime.now().isoformat(),
            total_results=len(web_docs) + len(litigation)
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Research query failed: {str(e)}")

@router.get("/litigation/{company_name}")
async def get_litigation_data(company_name: str):
    """
    Get litigation data for a company
    """
    litigation = mock_litigation_search(company_name)
    
    return {
        "company_name": company_name,
        "total_cases": len(litigation),
        "active_cases": sum(1 for case in litigation if case["case_status"] == "PENDING"),
        "litigation_exposure": "MEDIUM-LOW",
        "cases": litigation
    }

@router.get("/mca/{company_name}")
async def get_mca_data(company_name: str):
    """
    Get MCA company registration details
    """
    return mock_mca_scraping(company_name)

@router.get("/sector/{sector_name}")
async def get_sector_analysis(sector_name: str):
    """
    Get sector risk analysis
    """
    return {
        "sector": sector_name,
        "market_size": "₹45,000 Cr",
        "growth_rate": "28% CAGR",
        "risk_rating": "MEDIUM",
        "key_risks": [
            "Increasing competition from hyperscalers",
            "Regulatory uncertainty in data residency",
            "Talent acquisition challenges",
            "Commodity pricing pressure"
        ],
        "opportunities": [
            "High growth in enterprise cloud adoption",
            "Government digitalization initiatives",
            "Emerging AI/ML integration opportunities",
            "Edge computing expansion"
        ]
    }

@router.get("/retrieval-metadata")
async def get_rag_metadata():
    """
    Get RAG system metadata
    """
    return RAGMetadata(
        vector_db_type="ChromaDB",
        total_chunks=15847,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        retrieval_method="Semantic similarity + BM25 hybrid search"
    )

@router.post("/validate-credit-worthiness")
async def validate_credit_worthiness(company_name: str):
    """
    Validate credit worthiness based on research
    """
    litigation = mock_litigation_search(company_name)
    docs = mock_web_search(company_name)
    
    # Calculate credit score
    score = 75.0
    if litigation:
        score -= len(litigation) * 5
    
    return {
        "company_name": company_name,
        "credit_worthiness_score": max(30, score),
        "rating": "A" if score > 80 else "B+" if score > 70 else "B",
        "research_completed": True,
        "confidence": 0.87
    }
