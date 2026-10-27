#!/usr/bin/env python3
"""
Minimal FastAPI server for document upload and OCR
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize FastAPI
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

# Storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory storage for demo
uploaded_docs = []

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
            "document_processing": "ready",
            "ocr": "ready"
        }
    }

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        
        # Save file
        file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Simulate processing (in real implementation, this would do OCR)
        processed_doc = {
            "document_id": doc_id,
            "file_name": file.filename,
            "file_size": len(content),
            "file_type": file.content_type,
            "created_at": datetime.now().isoformat(),
            "overall_status": "completed",
            "confidence": 0.92,
            "pages_processed": 1,
            "extracted_text": "Sample extracted text from document...",
            "processing_time": 2.5
        }
        
        # Store in memory
        uploaded_docs.append(processed_doc)
        
        return JSONResponse({
            "success": True,
            "message": "Document uploaded and processed successfully",
            "data": processed_doc
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents/list")
async def list_documents(limit: int = 50):
    """List uploaded documents"""
    return JSONResponse({
        "success": True,
        "data": uploaded_docs[-limit:] if limit > 0 else uploaded_docs,
        "total": len(uploaded_docs)
    })

@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get specific document"""
    doc = next((d for d in uploaded_docs if d["document_id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return JSONResponse({
        "success": True,
        "data": doc
    })

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  Intelli-Credit API - Document Processing")
    print("="*60)
    print("\nStarting server on http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - Document Upload: POST /api/v1/documents/upload")
    print("  - Document List:   GET /api/v1/documents/list")
    print("  - Health Check:    GET /health")
    print("\nAPI Docs: http://127.0.0.1:8000/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
