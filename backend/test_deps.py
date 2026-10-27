#!/usr/bin/env python3
"""
Test script to verify backend dependencies
"""

try:
    import fastapi
    print("✓ FastAPI available:", fastapi.__version__)
except ImportError:
    print("✗ FastAPI not available")

try:
    import uvicorn
    print("✓ Uvicorn available:", uvicorn.__version__)
except ImportError:
    print("✗ Uvicorn not available")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ FastAPI components available")
except ImportError as e:
    print("✗ FastAPI components error:", e)

print("\nTesting basic server...")
try:
    app = FastAPI(title="Test")
    print("✓ FastAPI app created successfully")
except Exception as e:
    print("✗ FastAPI app creation failed:", e)

print("\nDependencies check complete!")
