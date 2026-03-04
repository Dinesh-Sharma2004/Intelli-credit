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

app = FastAPI(
    title="Intelli-Credit API",
    description="AI-Powered Credit Decisioning Engine",
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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Intelli-Credit API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "operational",
        "components": {
            "document_ingestor": "ready",
            "research_agent": "ready",
            "risk_scoring": "ready",
            "cam_generator": "ready"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
