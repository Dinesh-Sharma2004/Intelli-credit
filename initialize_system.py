"""
Script to initialize and seed the Intelli-Credit system with demo data
Run: python initialize_system.py
"""

import json
import csv
from pathlib import Path
from datetime import datetime

def create_demo_companies():
    """Create demo company data"""
    companies = [
        {
            "id": "COM001",
            "name": "TechVenture Solutions Pvt Ltd",
            "cin": "U72900GJ2005PLC047584",
            "sector": "Cloud Infrastructure",
            "established": "2005",
            "employees": 342,
            "revenue_cr": 245.67,
            "status": "ACTIVE"
        },
        {
            "id": "COM002",
            "name": "CloudServices Inc",
            "cin": "U72901DL2008PLC034892",
            "sector": "Cloud Services",
            "established": "2008",
            "employees": 278,
            "revenue_cr": 189.45,
            "status": "ACTIVE"
        }
    ]
    
    with open('backend/data/companies.json', 'w') as f:
        json.dump(companies, f, indent=2)
    print("✓ Created demo companies")

def create_config():
    """Create system configuration"""
    config = {
        "system": {
            "name": "Intelli-Credit",
            "version": "1.0.0",
            "environment": "demo"
        },
        "ml_model": {
            "type": "XGBoost",
            "version": "v2.1.0",
            "accuracy": 0.87,
            "auc_score": 0.92
        },
        "services": [
            "document_ingestor",
            "research_agent",
            "risk_scoring",
            "cam_generator"
        ],
        "features": {
            "ocr": True,
            "ner": True,
            "web_scraping": True,
            "litigation_tracking": True,
            "shap_explainability": True
        }
    }
    
    with open('backend/config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("✓ Created system configuration")

def main():
    print("=" * 50)
    print("Intelli-Credit System Initialization")
    print("=" * 50)
    
    Path('backend/data').mkdir(exist_ok=True)
    
    create_demo_companies()
    create_config()
    
    print("\n✓ System initialization completed!")
    print("\nNext steps:")
    print("1. Build services: docker-compose build")
    print("2. Start services: docker-compose up -d")
    print("3. Access frontend: http://localhost:3000")
    print("4. Access API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
