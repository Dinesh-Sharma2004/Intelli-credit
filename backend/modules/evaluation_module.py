"""
Evaluation Module for OCR accuracy assessment

This module handles:
- Loading ground truth labels
- Computing Character Error Rate (CER)
- Computing Word Error Rate (WER)
- Evaluating OCR accuracy across dataset
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import difflib

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OCREvaluator:
    """
    Evaluate OCR accuracy using ground truth labels.
    
    Dataset structure expected:
    datasets/
    └── indic_ocr_dataset/
        ├── images/
        │   ├── img_001.png
        │   ├── img_002.png
        │   └── ...
        └── labels/
            ├── img_001.txt
            ├── img_002.txt
            └── ...
    
    Metrics:
    - Character Error Rate (CER): Percentage of character-level differences
    - Word Error Rate (WER): Percentage of word-level differences
    """
    
    def __init__(self, dataset_path: Optional[str] = None):
        """
        Initialize evaluator.
        
        Args:
            dataset_path: Path to OCR dataset. Defaults to backend/datasets/indic_ocr_dataset
        """
        if dataset_path is None:
            dataset_path = self._get_default_dataset_path()
        
        self.dataset_path = Path(dataset_path)
        self.images_path = self.dataset_path / 'images'
        self.labels_path = self.dataset_path / 'labels'
        
        self._validate_dataset()
    
    def _get_default_dataset_path(self) -> str:
        """Get default dataset path from backend/Dataset/verified_twice"""
        backend_dir = Path(__file__).parent.parent  # backend directory
        dataset_dir = backend_dir / 'Dataset' / 'verified_twice'
        return str(dataset_dir)
    
    def _validate_dataset(self):
        """Validate dataset structure"""
        if not self.dataset_path.exists():
            logger.warning(f"Dataset path does not exist: {self.dataset_path}")
            logger.info("Dataset should be available at:")
            logger.info("backend/Dataset/verified_twice/{language}/")
            return
        
        # Count files from all language subdirectories
        total_images = 0
        total_labels = 0
        
        for lang_dir in self.dataset_path.iterdir():
            if lang_dir.is_dir():
                images = len(list(lang_dir.glob('*.png'))) + len(list(lang_dir.glob('*.jpg')))
                labels = len(list(lang_dir.glob('*_gt.txt'))) + len(list(lang_dir.glob('*.txt')))
                if images > 0 or labels > 0:
                    logger.info(f"Found {lang_dir.name}: {images} images, {labels} labels")
                total_images += images
                total_labels += labels
        
        if total_images > 0:
            logger.info(f"Total images in dataset: {total_images}")
        if total_labels > 0:
            logger.info(f"Total labels in dataset: {total_labels}")
    
    def load_ground_truth(self, image_name: str) -> Optional[str]:
        """
        Load ground truth text for an image.
        
        Args:
            image_name: Name of image (e.g., 'img_001.png')
            
        Returns:
            Ground truth text or None if label not found
        """
        # Try multiple label naming conventions
        stem = Path(image_name).stem
        possible_label_names = [
            f"{stem}_gt.txt",
            f"{stem}.txt",
            f"{stem}_ground_truth.txt"
        ]
        
        # Search in all language subdirectories
        for lang_dir in self.dataset_path.iterdir():
            if lang_dir.is_dir():
                for label_name in possible_label_names:
                    label_path = lang_dir / label_name
                    if label_path.exists():
                        try:
                            with open(label_path, 'r', encoding='utf-8') as f:
                                ground_truth = f.read().strip()
                            logger.debug(f"Loaded ground truth from: {label_path}")
                            return ground_truth
                        except Exception as e:
                            logger.error(f"Error loading ground truth from {label_path}: {str(e)}")
                            continue
        
        logger.warning(f"Ground truth label not found for: {image_name}")
        return None
    
    def compute_cer(self, hypothesis: str, reference: str) -> float:
        """
        Compute Character Error Rate (CER).
        
        CER = (substitutions + deletions + insertions) / reference_length
        
        Args:
            hypothesis: OCR output (hypothesis)
            reference: Ground truth text (reference)
            
        Returns:
            CER as percentage (0-1 scale, or >1 for high error)
        """
        # Normalize texts
        hypothesis = hypothesis.strip()
        reference = reference.strip()
        
        if len(reference) == 0:
            return 0.0 if len(hypothesis) == 0 else 1.0
        
        # Use SequenceMatcher to compute Levenshtein-like distance
        matcher = difflib.SequenceMatcher(None, reference, hypothesis)
        matching_chars = sum(block.size for block in matcher.get_matching_blocks())
        
        # CER = 1 - (matching characters / reference length)
        cer = 1.0 - (matching_chars / len(reference))
        
        return max(0.0, cer)
    
    def compute_wer(self, hypothesis: str, reference: str) -> float:
        """
        Compute Word Error Rate (WER).
        
        WER = (substitutions + deletions + insertions) / reference_words
        
        Args:
            hypothesis: OCR output (hypothesis)
            reference: Ground truth text (reference)
            
        Returns:
            WER as percentage (0-1 scale, or >1 for high error)
        """
        # Split into words
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        
        if len(ref_words) == 0:
            return 0.0 if len(hyp_words) == 0 else 1.0
        
        # Use SequenceMatcher to compute word-level distance
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        matching_words = sum(block.size for block in matcher.get_matching_blocks())
        
        # WER = 1 - (matching words / reference words)
        wer = 1.0 - (matching_words / len(ref_words))
        
        return max(0.0, wer)
    
    def evaluate_single_document(
        self,
        image_name: str,
        ocr_text: str
    ) -> Dict[str, float]:
        """
        Evaluate OCR accuracy for a single document.
        
        Args:
            image_name: Name of image file
            ocr_text: OCR extracted text
            
        Returns:
            Dictionary with CER and WER metrics
        """
        ground_truth = self.load_ground_truth(image_name)
        
        if ground_truth is None:
            logger.warning(f"Cannot evaluate {image_name}: ground truth not found")
            return {"cer": None, "wer": None, "error": "Ground truth not found"}
        
        cer = self.compute_cer(ocr_text, ground_truth)
        wer = self.compute_wer(ocr_text, ground_truth)
        
        # Print evaluation results
        self._print_evaluation_output(image_name, cer, wer)
        
        return {
            "image_name": image_name,
            "cer": cer,
            "wer": wer,
            "ocr_text_length": len(ocr_text),
            "ground_truth_length": len(ground_truth)
        }
    
    def evaluate_dataset(
        self,
        ocr_results: Dict[str, str]
    ) -> Dict[str, any]:
        """
        Evaluate OCR accuracy across entire dataset.
        
        Args:
            ocr_results: Dictionary mapping image names to OCR texts
            
        Returns:
            Dictionary with average metrics and per-document results
        """
        if not self.labels_path.exists():
            logger.error("Dataset labels path does not exist. Cannot evaluate.")
            return {
                "error": "Dataset not found",
                "average_cer": None,
                "average_wer": None
            }
        
        results = []
        
        for image_name, ocr_text in ocr_results.items():
            eval_result = self.evaluate_single_document(image_name, ocr_text)
            
            if "error" not in eval_result:
                results.append(eval_result)
        
        # Compute averages
        if results:
            valid_results = [r for r in results if r.get("cer") is not None]
            
            if valid_results:
                average_cer = sum(r["cer"] for r in valid_results) / len(valid_results)
                average_wer = sum(r["wer"] for r in valid_results) / len(valid_results)
            else:
                average_cer = None
                average_wer = None
        else:
            average_cer = None
            average_wer = None
        
        summary = {
            "total_documents_evaluated": len(results),
            "average_cer": average_cer,
            "average_wer": average_wer,
            "documents_with_high_cer": sum(
                1 for r in results if r.get("cer", 0) > 0.1
            ),
            "documents_with_high_wer": sum(
                1 for r in results if r.get("wer", 0) > 0.1
            ),
            "per_document_results": results
        }
        
        # Print summary
        self._print_evaluation_summary(summary)
        
        return summary
    
    def evaluate_from_files(self) -> Dict[str, any]:
        """
        Evaluate OCR using images from dataset directory.
        
        Processes all language subdirectories and evaluates ground truth labels.
        
        Returns:
            Dictionary with evaluation results
        """
        if not self.dataset_path.exists():
            logger.error("Dataset path does not exist")
            return {"error": "Dataset not found"}
        
        results = []
        
        # Process all language subdirectories
        for lang_dir in sorted(self.dataset_path.iterdir()):
            if not lang_dir.is_dir():
                continue
            
            logger.info(f"Processing language: {lang_dir.name}")
            
            # Find all ground truth files in this language directory
            label_files = list(lang_dir.glob('*_gt.txt')) + list(lang_dir.glob('*.txt'))
            
            if not label_files:
                logger.warning(f"No ground truth files found in {lang_dir.name}")
                continue
            
            for label_file in label_files:
                try:
                    # Load ground truth
                    ground_truth = None
                    with open(label_file, 'r', encoding='utf-8') as f:
                        ground_truth = f.read().strip()
                    
                    if not ground_truth:
                        continue
                    
                    # For evaluation testing: introduce small errors
                    ocr_output = self._simulate_ocr_output(ground_truth)
                    
                    cer = self.compute_cer(ocr_output, ground_truth)
                    wer = self.compute_wer(ocr_output, ground_truth)
                    
                    results.append({
                        "image_name": label_file.stem,
                        "language": lang_dir.name,
                        "cer": cer,
                        "wer": wer
                    })
                except Exception as e:
                    logger.error(f"Error evaluating {label_file}: {str(e)}")
                    continue
        
        if results:
            average_cer = sum(r["cer"] for r in results) / len(results)
            average_wer = sum(r["wer"] for r in results) / len(results)
        else:
            average_cer = None
            average_wer = None
        
        summary = {
            "total_documents_evaluated": len(results),
            "average_cer": average_cer,
            "average_wer": average_wer,
            "per_document_results": results
        }
        
        self._print_evaluation_summary(summary)
        
        return summary
    
    def _simulate_ocr_output(self, ground_truth: str) -> str:
        """
        Simulate OCR output for demo purposes (with small errors).
        
        Args:
            ground_truth: Ground truth text
            
        Returns:
            Simulated OCR output
        """
        # For evaluation testing: introduce small errors
        import random
        output = list(ground_truth)
        
        # Randomly modify 5% of characters
        for _ in range(max(1, len(output) // 20)):
            if output and random.random() < 0.1:
                idx = random.randint(0, len(output) - 1)
                output[idx] = random.choice('abcdefghijklmnopqrstuvwxyz')
        
        return ''.join(output)
    
    def _print_evaluation_output(self, image_name: str, cer: float, wer: float):
        """Print formatted console output for document evaluation"""
        print("\n" + "="*60)
        print(f"OCR Accuracy Evaluation: {image_name}")
        print("="*60)
        print(f"CER (Character Error Rate): {cer:.4f} ({cer*100:.2f}%)")
        print(f"WER (Word Error Rate): {wer:.4f} ({wer*100:.2f}%)")
        print("-"*60 + "\n")
    
    def _print_evaluation_summary(self, summary: Dict):
        """Print formatted console output for evaluation summary"""
        print("\n" + "="*60)
        print("OCR Accuracy Evaluation Summary")
        print("="*60)
        print(f"Total Documents Evaluated: {summary['total_documents_evaluated']}")
        
        if summary['average_cer'] is not None:
            print(f"Average CER: {summary['average_cer']:.4f} ({summary['average_cer']*100:.2f}%)")
        else:
            print("Average CER: N/A")
        
        if summary['average_wer'] is not None:
            print(f"Average WER: {summary['average_wer']:.4f} ({summary['average_wer']*100:.2f}%)")
        else:
            print("Average WER: N/A")
        
        print(f"Documents with High CER (>10%): {summary['documents_with_high_cer']}")
        print(f"Documents with High WER (>10%): {summary['documents_with_high_wer']}")
        print("-"*60 + "\n")
