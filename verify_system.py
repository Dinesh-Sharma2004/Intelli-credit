#!/usr/bin/env python3
"""
System Verification & Health Check Script

This script verifies that all components of the document processing pipeline
are properly installed and configured.
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class SystemVerifier:
    """Verify system components and readiness."""

    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.warnings: List[str] = []
        self.workspace_root = Path(__file__).parent.parent

    # ==================== Verification Methods ====================

    def check_python_version(self) -> bool:
        """Check Python version (3.9+ required)."""
        print(f"\n{BOLD}🐍 Python Version{RESET}")
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"   Installed: Python {version}")

        if sys.version_info >= (3, 9):
            print(f"   {GREEN}✓ OK{RESET} (3.9+ required)")
            return True
        else:
            print(f"   {RED}✗ FAILED{RESET} (3.9+ required, got {version})")
            return False

    def check_package(self, package_name: str, import_name: str = None) -> bool:
        """Check if a package is installed."""
        if import_name is None:
            import_name = package_name

        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

    def get_package_version(self, package_name: str) -> str:
        """Get installed package version."""
        try:
            module = __import__(package_name)
            if hasattr(module, "__version__"):
                return module.__version__
            elif hasattr(module, "VERSION"):
                return module.VERSION
            else:
                return "unknown"
        except Exception:
            return "not installed"

    def check_core_dependencies(self) -> bool:
        """Check core Python dependencies."""
        print(f"\n{BOLD}📦 Core Dependencies{RESET}")

        required_packages = [
            ("torch", "PyTorch"),
            ("transformers", "Transformers"),
            ("fastapi", "FastAPI"),
            ("PyPDF2", "PyPDF2"),
            ("sqlalchemy", "SQLAlchemy"),
            ("pydantic", "Pydantic"),
            ("numpy", "NumPy"),
            ("PIL", "Pillow"),
        ]

        all_present = True
        for package, display_name in required_packages:
            import_name = package if package != "PIL" else "PIL"
            present = self.check_package(package, import_name)

            if present:
                version = self.get_package_version(package)
                print(f"   {GREEN}✓{RESET} {display_name:20} {version}")
            else:
                print(f"   {RED}✗{RESET} {display_name:20} NOT INSTALLED")
                all_present = False

        return all_present

    def check_optional_packages(self) -> bool:
        """Check optional packages."""
        print(f"\n{BOLD}💎 Optional Packages{RESET}")

        optional = [
            ("opencv", "cv2", "OpenCV"),
            ("requests", "requests", "Requests"),
            ("tqdm", "tqdm", "tqdm"),
            ("python_dotenv", "dotenv", "python-dotenv"),
        ]

        status = True
        for package, import_name, display_name in optional:
            present = self.check_package(import_name, import_name)

            if present:
                version = self.get_package_version(import_name)
                print(f"   {GREEN}✓{RESET} {display_name:20} {version}")
            else:
                print(f"   {YELLOW}○{RESET} {display_name:20} Not installed (optional)")
                self.warnings.append(f"{display_name} not installed (optional)")

        return status

    def check_ml_models(self) -> bool:
        """Check for ML model installations."""
        print(f"\n{BOLD}🤖 ML Models{RESET}")

        models = [
            ("OCR Model", "backend/models/indic_trocr"),
            ("Translation Model", "backend/models/indictrans2"),
            ("Fine-tuned Model", "backend/models/indictrans2_finetuned"),
        ]

        all_present = True
        for name, path in models:
            full_path = self.workspace_root / path
            if full_path.exists():
                print(f"   {GREEN}✓{RESET} {name:30} {full_path.relative_to(self.workspace_root)}")
            else:
                print(f"   {YELLOW}○{RESET} {name:30} Not downloaded yet")
                self.warnings.append(f"{name} not downloaded")
                all_present = False

        return all_present

    def check_directories(self) -> bool:
        """Check required directories exist."""
        print(f"\n{BOLD}📁 Workspace Directories{RESET}")

        required_dirs = [
            ("Backend", "backend"),
            ("Services", "backend/services"),
            ("Models", "backend/models"),
            ("Data", "backend/data"),
            ("Dataset", "backend/Dataset"),
            ("Frontend", "frontend"),
            ("Uploads", "backend/uploads"),
            ("Processed Docs", "backend/processed_documents"),
        ]

        all_present = True
        for name, path in required_dirs:
            full_path = self.workspace_root / path
            exists = full_path.exists()

            if exists:
                print(f"   {GREEN}✓{RESET} {name:20} {full_path.relative_to(self.workspace_root)}")
            else:
                print(f"   {RED}✗{RESET} {name:20} MISSING")
                all_present = False

        return all_present

    def check_files(self) -> bool:
        """Check required files exist."""
        print(f"\n{BOLD}📄 Required Files{RESET}")

        required_files = [
            ("Main Backend", "backend/main.py"),
            ("Requirements", "backend/requirements_simple.txt", False),
            ("OCR Module", "backend/modules/ocr_module.py", False),
            ("Translation Module", "backend/modules/translation_module.py", False),
            ("Document Processor", "backend/services/document_processor_service.py"),
            ("API Server", "backend/document_processing_api.py"),
            ("Integrated Pipeline", "backend/integrated_document_pipeline.py"),
            ("Fine-tuning", "backend/prepare_finetuning.py"),
            ("Demo", "backend/document_processing_demo.py"),
            ("Frontend Config", "frontend/next.config.js"),
            ("Frontend Package", "frontend/package.json"),
        ]

        all_present = True
        for name, path, *critical in required_files:
            is_critical = critical[0] if critical else True
            full_path = self.workspace_root / path
            exists = full_path.exists()

            status_char = "✓" if exists else "✗"
            status_color = GREEN if exists else (RED if is_critical else YELLOW)

            print(f"   {status_color}{status_char}{RESET} {name:25} {full_path.relative_to(self.workspace_root)}")

            if not exists and is_critical:
                all_present = False

        return all_present

    def check_database(self) -> bool:
        """Check database configuration."""
        print(f"\n{BOLD}🗄️  Database{RESET}")

        # Check for .env file
        env_file = self.workspace_root / ".env"
        if env_file.exists():
            print(f"   {GREEN}✓{RESET} .env file found")
        else:
            print(f"   {YELLOW}○{RESET} .env file not found (will use defaults)")
            self.warnings.append(".env file not found - using default database URL")

        # Check SQLAlchemy
        try:
            import sqlalchemy

            print(f"   {GREEN}✓{RESET} SQLAlchemy {self.get_package_version('sqlalchemy')} installed")
            return True
        except ImportError:
            print(f"   {RED}✗{RESET} SQLAlchemy not installed")
            return False

    def check_cuda(self) -> bool:
        """Check CUDA/GPU availability."""
        print(f"\n{BOLD}🔌 GPU / CUDA{RESET}")

        try:
            import torch

            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                device_memory = torch.cuda.get_device_properties(0).total_memory / 1e9

                print(f"   {GREEN}✓{RESET} CUDA Available")
                print(f"      Devices: {device_count}")
                print(f"      GPU: {device_name}")
                print(f"      Memory: {device_memory:.1f} GB")

                if device_memory >= 16:
                    print(f"      {GREEN}✓ Sufficient for fine-tuning (16GB+){RESET}")
                else:
                    print(f"      {YELLOW}⚠ Limited memory for fine-tuning{RESET}")
                    self.warnings.append(f"GPU memory {device_memory:.1f}GB (16GB recommended for fine-tuning)")

                return True
            else:
                print(f"   {YELLOW}○{RESET} No CUDA GPU detected (CPU mode)")
                print(f"      Fine-tuning will be slow (GPU recommended)")
                self.warnings.append("No GPU detected - fine-tuning will be slow")
                return False

        except ImportError:
            print(f"   {RED}✗{RESET} PyTorch not installed")
            return False

    def check_api_server(self) -> bool:
        """Check if API server is running."""
        print(f"\n{BOLD}🚀 API Server{RESET}")

        try:
            import requests

            try:
                response = requests.get("http://localhost:8000/api/v1/status/models", timeout=2)
                if response.status_code == 200:
                    print(f"   {GREEN}✓{RESET} API server running on localhost:8000")
                    return True
                else:
                    print(f"   {YELLOW}○{RESET} API server not responding")
                    return False
            except requests.exceptions.ConnectionError:
                print(f"   {YELLOW}○{RESET} API server not running")
                print(f"      Start with: python -m uvicorn backend.document_processing_api:app")
                self.warnings.append("API server not running")
                return False

        except ImportError:
            print(f"   {YELLOW}○{RESET} Requests library not installed")
            return False

    # ==================== Summary Methods ====================

    def print_summary(self):
        """Print overall system status summary."""
        print("\n" + "=" * 60)
        print(f"{BOLD}System Status Summary{RESET}")
        print("=" * 60)

        # Count scores
        total_checks = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        percentage = (passed / total_checks * 100) if total_checks > 0 else 0

        print(f"\n{BOLD}Overall: {passed}/{total_checks} checks passed ({percentage:.0f}%){RESET}\n")

        # Status indicators
        if percentage >= 90:
            print(f"{GREEN}{BOLD}✓ System is READY for use{RESET}")
        elif percentage >= 70:
            print(f"{YELLOW}{BOLD}⚠ System is FUNCTIONAL but has warnings{RESET}")
        else:
            print(f"{RED}{BOLD}✗ System needs attention{RESET}")

        # Print warnings if any
        if self.warnings:
            print(f"\n{YELLOW}{BOLD}⚠ Warnings:{RESET}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        # Print next steps
        print(f"\n{BLUE}{BOLD}Next Steps:{RESET}")
        print("   1. Install dependencies: pip install -r backend/requirements_simple.txt")
        print("   2. Download OCR/translation models (see QUICKSTART_API.md)")
        print("   3. Start API server: python -m uvicorn backend.document_processing_api:app")
        print("   4. Fine-tune translation: python backend/prepare_finetuning.py")
        print("   5. Try demo: python backend/document_processing_demo.py")

    def run_all_checks(self):
        """Run all verification checks."""
        print("\n" + "=" * 60)
        print(f"{BOLD}{BLUE}Document Processing Pipeline - System Verification{RESET}")
        print("=" * 60)

        # Run checks
        self.results["Python Version"] = self.check_python_version()
        self.results["Core Dependencies"] = self.check_core_dependencies()
        self.results["Optional Packages"] = self.check_optional_packages()
        self.results["Directories"] = self.check_directories()
        self.results["Required Files"] = self.check_files()
        self.results["ML Models"] = self.check_ml_models()
        self.results["Database"] = self.check_database()
        self.results["GPU / CUDA"] = self.check_cuda()
        self.results["API Server"] = self.check_api_server()

        # Summary
        self.print_summary()


def main():
    """Main execution."""
    verifier = SystemVerifier()
    verifier.run_all_checks()


if __name__ == "__main__":
    main()
