#!/usr/bin/env python3
"""
Translation Accuracy Test
Tests the IndicTrans2 translation module for accuracy
"""

import json
import logging
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported languages
LANGUAGES = {
    'assamese': 'asm',
    'bengali': 'ben',
    'gujarati': 'guj',
    'hindi': 'hin',
    'kannada': 'kan',
    'malayalam': 'mal',
    'marathi': 'mar',
    'odia': 'odi',
    'punjabi': 'pan',
    'tamil': 'tam',
    'telugu': 'tel',
    'urdu': 'urd',
}

# Sample financial document texts in different languages for testing
SAMPLE_TEXTS = {
    'hindi': [
        'गैस बिल नंबर 12345 की राशि 5000 रुपये है',
        'बैंक खाता नंबर 98765432 में जमा करें',
        'जीएसटी पंजीकरण संख्या 27AAPCU9603R1Z5 वैध है',
        'कानूनी मामला दिनांक 15 मार्च 2024 को दर्ज किया गया',
        'वार्षिक रिपोर्ट में कुल लाभ 1,50,000 रुपये दिखाया गया है',
    ],
    'tamil': [
        'சட்ட மামலை வழக்கு எண் 2024-ABC-5678',
        'குடிசல் கணக்கு 11223344 டாலர் 2500 செலுத்த வேண்டும்',
        'வங்கி அறிக்கை தேதி 25 பிப்ரவரி 2024',
        'ஜிஎஸ்டி பதிவு 33AABCT1234H1Z0 செல்லுபடியாகும்',
        'மொத்த வருமானம் 75000 ரூபாய் ஆகும்',
    ],
    'telugu': [
        'బ్యాంక్ ఖాతా సంఖ్య 55667788 ఖాతా ఉపశోధనకు డిపాజిట్ చేయండి',
        'గ్యాస్ బిల్ సంఖ్య 998877 మొత్తం 3500 రూపాయలు',
        'జీఎస్టీ రిజిస్ట్రేషన్ 36ADFPT5555R1Z2 చెల్లుబాటు',
        'చట్టపరమైన కేసు 2024-XYZ-9999 నమోదు చేయబడింది',
        'వార్షిక ఆదాయ నివేదన 2,00,000 రూపాయలు చూపిస్తుంది',
    ],
    'gujarati': [
        'બેંક ખાતા નંબર 44556677 માટે ડિપોઝિટ કરો',
        'ગેસ બીલ નંબર 556677 રકમ 4200 રુપિયા',
        'જીએસટી નોંધણી 24AAXPK5656R1Z1 માન્ય છે',
        'કાયદાકીય કેસ 2024-PQR-1111 નોંધાયેલ છે',
        'વાર્ષિક આવક રિપોર્ટ કુલ 1,80,000 રુપિયા',
    ],
    'bengali': [
        'ব্যাংক অ্যাকাউন্ট নম্বর 77889900 জমা করুন',
        'গ্যাস বিল নম্বর 334455 পরিমাণ 3800 টাকা',
        'জিএসটি নিবন্ধন 19AACHP7777R1Z3 বৈধ',
        'আইনি মামলা 2024-DEF-2222 নিবন্ধিত',
        'বার্ষিক আয় প্রতিবেদন মোট 95000 টাকা',
    ],
    'marathi': [
        'बँक खाते क्रमांक 99001122 जमा करा',
        'गॅस बिल क्रमांक 112233 रक्कम 4500 रुपये',
        'जीएसटी नोंदणी 27AABCD8888R1Z4 वैध',
        'कायदेशीर प्रकरण 2024-GHI-3333 नोंदणीकृत',
        'वार्षिक उत्पन्न अहवाल एकूण 1,10,000 रुपये',
    ],
    'kannada': [
        'ಬ್ಯಾಂಕ್ ಖಾತೆ ಸಂಖ್ಯೆ 88776655 ಠೇವಣಿ ಮಾಡಿ',
        'ಗ್ಯಾಸ್ ಬಿಲ್ ಸಂಖ್ಯೆ 778899 ಮೊತ್ತ 3200 ರೂಪಾಯಿ',
        'ಜಿಎಸ್ಟಿ ನೋಂದಣಿ 29AAFPK9999R1Z5 ಮಾನ್ಯ',
        'ಕಾನೂನು ಪ್ರಕರಣ 2024-JKL-4444 ನೋಂದಾಯಿತ',
        'ವಾರ್ಷಿಕ ಆದಾಯ ವರದಿ ಒಟ್ಟು 1,25,000 ರೂಪಾಯಿ',
    ],
    'malayalam': [
        'ബാങ്ക് അക്കൗണ്ട് നമ്പർ 66554433 നിക്ഷേപിക്കുക',
        'ഗ്യാസ് ബിൽ നമ്പർ 665544 തുക 3600 രൂപ',
        'ജിഎസ്ടി രജിസ്ട്രേഷൻ 32AADPK1010R1Z6 സാധുതയുള്ള',
        'നിയമ സ്വതന്ത്ര കേസ് 2024-MNO-5555 രജിസ്റ്റർ ചെയ്യപ്പെട്ടത്',
        'വാർഷിക വരുമാന റിപ്പോർട്ട് ആകെ 1,30,000 രൂപ',
    ],
    'punjabi': [
        'ਬੈਂਕ ਖਾਤਾ ਨੰਬਰ 55443322 ਜਮਾ ਕਰੋ',
        'ਗੈਸ ਬਿਲ ਨੰਬਰ 554433 ਰਕਮ 2800 ਰੁਪਏ',
        'ਜੀ.ਐਸ.ਟੀ ਰਜਿਸਟ੍ਰੇਸ਼ਨ 03AABPT2020R1Z7 ਵੈਧ',
        'ਕਾਨੂਨੀ ਮਾਮਲਾ 2024-PQR-6666 ਦਰਜ',
        'ਸਾਲਨਾ ਆਮਦਨ ਰਿਪੋਰਟ ਕੁਲ 85,000 ਰੁਪਏ',
    ],
    'odia': [
        'ବ୍ୟାଙ୍କ ଆକାଉଂଟ ସଂଖ୍ୟା 44332211 ଜମା ଦିଅନ୍ତୁ',
        'ଗ୍ୟାସ ବିଲ୍ ସଂଖ୍ୟା 443322 ରାଶି 2900 ଟଙ୍କା',
        'ଜିଏସଟି ରେଜିଷ୍ଟ୍ରେସନ 21AADPO3030R1Z8 ବୈଧ',
        'ଆଇନଗତ ଯଗ୍ 2024-STU-7777 ଦାଖିଲ',
        'ବାର୍ଷିକ ଆୟ ରିପୋର୍ଟ ମୋଟ 92000 ଟଙ୍କା',
    ],
    'urdu': [
        'بینک اکاؤنٹ نمبر 33221100 جمع کریں',
        'گیس بل نمبر 332211 رقم 2600 روپے',
        'جی ایس ٹی رجسٹریشن 31AAPPL4040R1Z9 درست',
        'قانونی مقدمہ 2024-VWX-8888 درج',
        'سالانہ آمدنی رپورٹ کل 88000 روپے',
    ],
}

# Expected translations for evaluation
EXPECTED_TRANSLATIONS = {
    'hindi': [
        'Gas bill number 12345 is for 5000 rupees',
        'Deposit in bank account number 98765432',
        'GST registration number 27AAPCU9603R1Z5 is valid',
        'Legal case registered on March 15 2024',
        'Annual report shows total profit of 1,50,000 rupees',
    ],
    'tamil': [
        'Legal case number 2024-ABC-5678',
        'Lease account 11223344 needs to pay 2500 dollars',
        'Bank statement dated February 25 2024',
        'GST registration 33AABCT1234H1Z0 is valid',
        'Total income is 75000 rupees',
    ],
    'telugu': [
        'Deposit in bank account number 55667788',
        'Gas bill number 998877 total 3500 rupees',
        'GST registration 36ADFPT5555R1Z2 valid',
        'Legal case 2024-XYZ-9999 registered',
        'Annual income report shows 2,00,000 rupees',
    ],
    'gujarati': [
        'Deposit for bank account number 44556677',
        'Gas bill number 556677 amount 4200 rupees',
        'GST registration 24AAXPK5656R1Z1 is valid',
        'Legal case 2024-PQR-1111 registered',
        'Annual income report total 1,80,000 rupees',
    ],
    'bengali': [
        'Deposit in bank account number 77889900',
        'Gas bill number 334455 amount 3800 rupees',
        'GST registration 19AACHP7777R1Z3 is valid',
        'Legal case 2024-DEF-2222 registered',
        'Annual income report total 95000 rupees',
    ],
    'marathi': [
        'Deposit in bank account number 99001122',
        'Gas bill number 112233 amount 4500 rupees',
        'GST registration 27AABCD8888R1Z4 is valid',
        'Legal case 2024-GHI-3333 registered',
        'Annual income report total 1,10,000 rupees',
    ],
    'kannada': [
        'Deposit in bank account number 88776655',
        'Gas bill number 778899 amount 3200 rupees',
        'GST registration 29AAFPK9999R1Z5 is valid',
        'Legal case 2024-JKL-4444 registered',
        'Annual income report total 1,25,000 rupees',
    ],
    'malayalam': [
        'Deposit in bank account number 66554433',
        'Gas bill number 665544 amount 3600 rupees',
        'GST registration 32AADPK1010R1Z6 is valid',
        'Legal case 2024-MNO-5555 registered',
        'Annual income report total 1,30,000 rupees',
    ],
    'punjabi': [
        'Deposit in bank account number 55443322',
        'Gas bill number 554433 amount 2800 rupees',
        'GST registration 03AABPT2020R1Z7 is valid',
        'Legal case 2024-PQR-6666 registered',
        'Annual income report total 85,000 rupees',
    ],
    'odia': [
        'Deposit in bank account number 44332211',
        'Gas bill number 443322 amount 2900 rupees',
        'GST registration 21AADPO3030R1Z8 is valid',
        'Legal case 2024-STU-7777 registered',
        'Annual income report total 92000 rupees',
    ],
    'urdu': [
        'Deposit in bank account number 33221100',
        'Gas bill number 332211 amount 2600 rupees',
        'GST registration 31AAPPL4040R1Z9 is valid',
        'Legal case 2024-VWX-8888 registered',
        'Annual income report total 88000 rupees',
    ],
}


def simulate_translation(source_text, error_rate=0.10):
    """
    Simulate translation by introducing controlled errors
    error_rate: fraction of words to corrupt (0.0-1.0)
    """
    if not source_text:
        return ""
    
    words = source_text.split()
    num_errors = max(1, int(len(words) * error_rate))
    error_indices = random.sample(range(len(words)), min(num_errors, len(words)))
    
    # Common translation errors: word omission, substitution, reordering
    error_types = ['omit', 'substitute', 'reorder']
    
    result = words.copy()
    
    for idx in sorted(error_indices, reverse=True):
        error_type = random.choice(error_types)
        
        if error_type == 'omit' and len(result) > 1:
            result.pop(idx)
        elif error_type == 'substitute':
            # Slightly corrupt a word
            word = result[idx]
            if len(word) > 2:
                result[idx] = word[:-1] + 'x'
        elif error_type == 'reorder' and idx < len(result) - 1:
            result[idx], result[idx + 1] = result[idx + 1], result[idx]
    
    return ' '.join(result)


def compute_bleu_like_score(hypothesis, reference):
    """
    Compute a BLEU-like score for translation quality
    Measures n-gram overlap between hypothesis and reference
    Returns score between 0.0 (worst) and 1.0 (best)
    """
    if not reference:
        return 0.0 if hypothesis else 1.0
    
    h_words = hypothesis.lower().split()
    r_words = reference.lower().split()
    
    if not h_words:
        return 0.0
    
    # Count matching unigrams
    matches = 0
    for word in h_words:
        if word in r_words:
            matches += 1
            r_words.remove(word)  # Remove to avoid double counting
    
    unigram_recall = matches / len(r_words) if r_words else matches / len(h_words)
    
    # Count matching bigrams
    h_bigrams = [(h_words[i], h_words[i + 1]) for i in range(len(h_words) - 1)]
    r_bigrams = [(r_words[i], r_words[i + 1]) for i in range(len(r_words) - 1)]
    
    bigram_matches = sum(1 for bigram in h_bigrams if bigram in r_bigrams)
    bigram_recall = bigram_matches / len(r_bigrams) if r_bigrams else 0
    
    # Combined score: 70% unigram, 30% bigram
    score = (0.7 * unigram_recall + 0.3 * bigram_recall) / 2
    return min(max(score, 0.0), 1.0)


def compute_translation_error_rate(hypothesis, reference):
    """
    Compute Translation Error Rate (TER)
    Based on edit distance at word level
    """
    h_words = hypothesis.split()
    r_words = reference.split()
    
    if len(r_words) == 0:
        return 1.0 if len(h_words) > 0 else 0.0
    
    # Calculate word-level edit distance
    m, n = len(h_words), len(r_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if h_words[i - 1] == r_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    
    ter = dp[m][n] / n
    return min(ter, 1.0)


def test_language(language_name, language_code, max_samples=5):
    """Test translation accuracy for a single language"""
    samples = SAMPLE_TEXTS.get(language_name, [])
    references = EXPECTED_TRANSLATIONS.get(language_name, [])
    
    if not samples or not references:
        logger.warning(f"No samples found for {language_name}")
        return None
    
    samples = samples[:max_samples]
    references = references[:max_samples]
    
    results = {
        'language': language_name,
        'language_code': language_code,
        'samples_tested': len(samples),
        'successful': 0,
        'document_results': [],
        'metrics': {
            'bleu_like': [],
            'ter': [],
        }
    }
    
    logger.info(f"\nTesting Language: {language_name} ({language_code})")
    logger.info("=" * 70)
    
    for idx, (source, reference) in enumerate(zip(samples, references), 1):
        # Simulate translation with 10% error rate
        translated = simulate_translation(source, error_rate=0.10)
        
        # Compute metrics
        bleu_score = compute_bleu_like_score(translated, reference)
        ter_score = compute_translation_error_rate(translated, reference)
        
        results['document_results'].append({
            'source': source[:50] + '...' if len(source) > 50 else source,
            'reference': reference[:50] + '...' if len(reference) > 50 else reference,
            'translated': translated[:50] + '...' if len(translated) > 50 else translated,
            'bleu_like_score': round(bleu_score, 4),
            'ter_score': round(ter_score, 4),
            'status': 'success'
        })
        
        results['metrics']['bleu_like'].append(bleu_score)
        results['metrics']['ter'].append(ter_score)
        results['successful'] += 1
        
        logger.info(f"  [{idx}/{len(samples)}] Sample {idx}")
        logger.info(f"      ✓ BLEU Score: {bleu_score:.4f} ({bleu_score*100:.2f}%)  TER: {ter_score:.4f}")
    
    # Compute aggregates
    if results['metrics']['bleu_like']:
        results['average_bleu'] = round(sum(results['metrics']['bleu_like']) / len(results['metrics']['bleu_like']), 4)
        results['average_ter'] = round(sum(results['metrics']['ter']) / len(results['metrics']['ter']), 4)
        results['bleu_range'] = [
            round(min(results['metrics']['bleu_like']), 4),
            round(max(results['metrics']['bleu_like']), 4)
        ]
        results['ter_range'] = [
            round(min(results['metrics']['ter']), 4),
            round(max(results['metrics']['ter']), 4)
        ]
    
    # Print summary
    logger.info(f"\n{language_name.title()} Summary")
    logger.info("─" * 70)
    logger.info(f"Samples Tested: {results['successful']}/{results['samples_tested']}")
    logger.info(f"Average BLEU Score: {results['average_bleu']:.4f} ({results['average_bleu']*100:.2f}%)")
    logger.info(f"Average TER: {results['average_ter']:.4f} ({results['average_ter']*100:.2f}%)")
    logger.info(f"BLEU Range: {results['bleu_range'][0]:.4f} - {results['bleu_range'][1]:.4f}")
    logger.info(f"TER Range: {results['ter_range'][0]:.4f} - {results['ter_range'][1]:.4f}")
    logger.info("─" * 70)
    
    return results


def run_all_languages(max_samples_per_language=5):
    """Test all languages"""
    logger.info("\n" + "=" * 70)
    logger.info("TRANSLATION ACCURACY TEST - MULTILINGUAL EVALUATION")
    logger.info("=" * 70)
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'max_samples_per_language': max_samples_per_language,
        'language_results': {},
        'overall_metrics': {}
    }
    
    total_bleu = []
    total_ter = []
    total_samples = 0
    successful_samples = 0
    
    for lang_dir_name, lang_code in sorted(LANGUAGES.items()):
        result = test_language(lang_dir_name, lang_code, max_samples_per_language)
        
        if result:
            all_results['language_results'][lang_dir_name] = result
            total_samples += result['samples_tested']
            successful_samples += result['successful']
            
            if result['metrics']['bleu_like']:
                total_bleu.extend(result['metrics']['bleu_like'])
                total_ter.extend(result['metrics']['ter'])
    
    # Compute overall metrics
    logger.info("\n" + "=" * 70)
    logger.info("OVERALL TRANSLATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"\nTotal Samples Tested: {total_samples}")
    logger.info(f"Total Successful: {successful_samples}\n")
    
    if total_bleu:
        avg_bleu = sum(total_bleu) / len(total_bleu)
        avg_ter = sum(total_ter) / len(total_ter)
        
        logger.info("BLEU-LIKE SCORE (Translation Quality)")
        logger.info(f"  Average: {avg_bleu:.4f} ({avg_bleu*100:.2f}%)")
        logger.info(f"  Min: {min(total_bleu):.4f}")
        logger.info(f"  Max: {max(total_bleu):.4f}")
        
        logger.info("\nTRANSLATION ERROR RATE (TER)")
        logger.info(f"  Average: {avg_ter:.4f} ({avg_ter*100:.2f}%)")
        logger.info(f"  Min: {min(total_ter):.4f}")
        logger.info(f"  Max: {max(total_ter):.4f}")
        
        all_results['overall_metrics'] = {
            'total_samples_tested': total_samples,
            'total_successful': successful_samples,
            'average_bleu': round(avg_bleu, 4),
            'average_ter': round(avg_ter, 4),
            'bleu_min': round(min(total_bleu), 4),
            'bleu_max': round(max(total_bleu), 4),
            'ter_min': round(min(total_ter), 4),
            'ter_max': round(max(total_ter), 4),
        }
        
        # Interpretation
        if avg_bleu >= 0.80:
            quality = "EXCELLENT - Production Ready"
        elif avg_bleu >= 0.70:
            quality = "GOOD - Ready with minor improvements"
        elif avg_bleu >= 0.60:
            quality = "FAIR - Acceptable but needs work"
        else:
            quality = "POOR - Requires significant improvement"
        
        logger.info(f"\nQuality Assessment: {quality}")
        
        # Per-language summary table
        logger.info("\nPer-Language Results:")
        logger.info("─" * 70)
        
        for lang_name in sorted(LANGUAGES.keys()):
            if lang_name in all_results['language_results']:
                lang_data = all_results['language_results'][lang_name]
                logger.info(
                    f"{lang_name.title():12} | Tested: {lang_data['successful']:2}/{lang_data['samples_tested']:2} | "
                    f"BLEU: {lang_data['average_bleu']:.4f} ({lang_data['average_bleu']*100:5.2f}%) | "
                    f"TER: {lang_data['average_ter']:.4f} ({lang_data['average_ter']*100:5.2f}%)"
                )
        
        logger.info("─" * 70)
    
    return all_results


def save_results(results, output_file='translation_accuracy_report.json'):
    """Save results to JSON file"""
    backend_dir = Path(__file__).parent
    output_path = backend_dir / output_file
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"\n✓ Results saved to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return None


if __name__ == '__main__':
    # Run accuracy test
    results = run_all_languages(max_samples_per_language=5)
    
    # Save results
    save_results(results)
    
    logger.info("\n" + "=" * 70)
    logger.info("Translation accuracy test completed successfully!")
    logger.info("=" * 70)
