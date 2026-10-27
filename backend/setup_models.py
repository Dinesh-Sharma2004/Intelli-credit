#!/usr/bin/env python3
"""
Model Setup and Download Script
Downloads IndicTrOCR and IndicTrans2 models from HuggingFace
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Models to download
MODELS_TO_DOWNLOAD = {
    'OCR Models (IndicTrOCR)': [
        'ai4bharat/IndicTrOCR-Assamese_v0',
        'ai4bharat/IndicTrOCR-Bengali_v0',
        'ai4bharat/IndicTrOCR-Gujarati_v0',
        'ai4bharat/IndicTrOCR-Hindi_v0',
        'ai4bharat/IndicTrOCR-Kannada_v0',
        'ai4bharat/IndicTrOCR-Malayalam_v0',
        'ai4bharat/IndicTrOCR-Marathi_v0',
        'ai4bharat/IndicTrOCR-Odia_v0',
        'ai4bharat/IndicTrOCR-Punjabi_v0',
        'ai4bharat/IndicTrOCR-Tamil_v0',
        'ai4bharat/IndicTrOCR-Telugu_v0',
        'ai4bharat/IndicTrOCR-Urdu_v0',
        'ai4bharat/IndicTrOCR-English_v0',
    ],
    'Translation Models (IndicTrans2)': [
        'ai4bharat/indic-trans-v2_en_hi',
        'ai4bharat/indic-trans-v2_en_ta',
        'ai4bharat/indic-trans-v2_en_te',
        'ai4bharat/indic-trans-v2_hi_en',
        'ai4bharat/indic-trans-v2_ta_en',
        'ai4bharat/indic-trans-v2_te_en',
        'ai4bharat/indic-trans-v2_kn_en',
        'ai4bharat/indic-trans-v2_ml_en',
        'ai4bharat/indic-trans-v2_bn_en',
        'ai4bharat/indic-trans-v2_gu_en',
        'ai4bharat/indic-trans-v2_mr_en',
        'ai4bharat/indic-trans-v2_or_en',
    ]
}


def download_models(models_list: List[str], category: str = "Models"):
    """Download models from HuggingFace"""
    try:
        from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer, ViTImageProcessor
        from huggingface_hub import hf_hub_download
    except ImportError:
        logger.error("Please install transformers and huggingface_hub:")
        logger.error("pip install transformers huggingface_hub")
        return False
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Downloading {category}")
    logger.info(f"{'='*60}")
    
    successful = 0
    failed = 0
    
    for model_id in models_list:
        try:
            logger.info(f"\nDownloading: {model_id}")
            
            # Try to load model (will download if not cached)
            if 'IndicTrOCR' in model_id:
                # OCR model
                from transformers import VisionEncoderDecoderModel
                model = VisionEncoderDecoderModel.from_pretrained(
                    model_id, 
                    trust_remote_code=True,
                    cache_dir=None  # Uses default cache
                )
            else:
                # Translation model
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    cache_dir=None
                )
            
            # Also download tokenizer/processor
            if 'IndicTrOCR' in model_id:
                processor = ViTImageProcessor.from_pretrained(model_id, trust_remote_code=True)
                logger.info(f"✓ Downloaded {model_id} (model + processor)")
            else:
                tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
                logger.info(f"✓ Downloaded {model_id} (model + tokenizer)")
            
            successful += 1
            
        except Exception as e:
            logger.error(f"✗ Failed to download {model_id}: {e}")
            failed += 1
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Downloaded: {successful} models")
    if failed > 0:
        logger.warning(f"Failed: {failed} models")
    logger.info(f"{'='*60}\n")
    
    return failed == 0


def setup_project_directories():
    """Create necessary project directories"""
    base_dir = Path(__file__).parent.parent
    directories = [
        base_dir / "models" / "indic_trocr",
        base_dir / "models" / "indictrans2",
        base_dir / "uploads",
        base_dir / "cache" / "ocr",
        base_dir / "cache" / "translation"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def check_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'torch': 'torch',
        'torchvision': 'torchvision',
        'transformers': 'transformers',
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pdf2image': 'pdf2image',
    }
    
    missing = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            logger.info(f"✓ {package} is installed")
        except ImportError:
            logger.warning(f"✗ {package} is NOT installed")
            missing.append(package)
    
    if missing:
        logger.error(f"\nMissing packages: {', '.join(missing)}")
        logger.error("\nInstall with:")
        logger.error(f"pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Main setup function"""
    logger.info("\n" + "="*60)
    logger.info("IndicTrOCR + IndicTrans2 Model Setup")
    logger.info("="*60)
    
    # Check dependencies
    logger.info("\n[1/3] Checking dependencies...")
    if not check_dependencies():
        logger.error("\nPlease install missing dependencies and try again.")
        return False
    logger.info("✓ All dependencies satisfied")
    
    # Create directories
    logger.info("\n[2/3] Creating project directories...")
    setup_project_directories()
    logger.info("✓ Directories created")
    
    # Download models
    logger.info("\n[3/3] Downloading models...")
    
    all_success = True
    for category, models in MODELS_TO_DOWNLOAD.items():
        if not download_models(models, category):
            all_success = False
    
    if all_success:
        logger.info("\n" + "="*60)
        logger.info("✓ Setup completed successfully!")
        logger.info("="*60)
        logger.info("\nYou can now use the OCR and Translation services.")
        logger.info("Example:")
        logger.info("  from services.indic_ocr_service import get_ocr_service")
        logger.info("  ocr = get_ocr_service()")
        logger.info("  result = ocr.extract_text_from_image('image.jpg', 'hindi')")
        logger.info("")
        return True
    else:
        logger.error("\n" + "="*60)
        logger.error("✗ Some models failed to download")
        logger.error("Please check the errors above and try again")
        logger.error("="*60 + "\n")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
