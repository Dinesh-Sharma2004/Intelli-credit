from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Import service routers
from services.document_ingestor_service import router as ingestor_router
from services.research_agent_service import router as research_router
from services.risk_scoring_service import router as scoring_router
from services.cam_generator_service import router as cam_router
from services.advanced_ocr_service import router as ocr_router

# Import document processing API
from document_processing_api import create_document_api

app = FastAPI(
    title="Intelli-Credit API",
    description="AI-Powered Credit Decisioning Engine with IndicTrOCR + IndicTrans2",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestor_router, prefix="/api/ingestor", tags=["Document Ingestor"])
app.include_router(research_router, prefix="/api/research", tags=["Research Agent"])
app.include_router(scoring_router, prefix="/api/scoring", tags=["Risk Scoring"])
app.include_router(cam_router, prefix="/api/cam", tags=["CAM Generator"])
app.include_router(ocr_router, prefix="/api/ocr", tags=["Advanced OCR"])

# Create and include document processing API
doc_api = create_document_api()
app.mount("", doc_api)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Intelli-Credit API",
        "version": "1.0.0",
        "features": ["IndicTrOCR", "IndicTrans2", "Document Processing"]
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "operational",
        "components": {
            "document_processing": "ready",
            "document_ingestor": "ready",
            "research_agent": "ready",
            "risk_scoring": "ready",
            "cam_generator": "ready",
            "ocr": "ready"
        },
        "ocr_models": "IndicTrOCR + IndicTrans2"
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  Intelli-Credit API with IndicTrOCR + IndicTrans2")
    print("="*60)
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - Document Upload: POST /api/v1/documents/upload")
    print("  - Document List:   GET /api/v1/documents/list")
    print("  - Health Check:    GET /health")
    print("\nAPI Docs: http://127.0.0.1:8000/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)
