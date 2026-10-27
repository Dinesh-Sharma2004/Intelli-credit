import random

import pytest

from app.services.ner_service import (
    FinancialNERService,
    GSTIN_CHARSET,
    gstin_check_digit,
    is_valid_gstin,
    is_valid_pan,
    normalize_money,
    pan_from_gstin,
    repair_gstin,
)


@pytest.fixture(scope="module")
def ner():
    return FinancialNERService()


def random_gstin(rng: random.Random) -> str:
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    pan = "".join(rng.choice(letters) for _ in range(3)) + rng.choice("CPFT") + rng.choice(letters) + f"{rng.randint(0, 9999):04d}" + rng.choice(letters)
    first14 = f"{rng.randint(1, 37):02d}{pan}{rng.choice('123456789')}Z"
    return first14 + gstin_check_digit(first14)


def labels(entities, label):
    return [e for e in entities if e.label == label]


def test_published_sample_gstin_has_valid_check_digit():
    assert gstin_check_digit("27AAPFU0939F1Z") == "V"
    assert is_valid_gstin("27AAPFU0939F1ZV")


@pytest.mark.parametrize("seed", range(25))
def test_generated_gstins_validate_and_any_check_digit_change_is_rejected(seed):
    rng = random.Random(seed)
    for _ in range(20):
        gstin = random_gstin(rng)
        assert is_valid_gstin(gstin)
        wrong = next(c for c in GSTIN_CHARSET if c != gstin[14])
        assert not is_valid_gstin(gstin[:14] + wrong)


@pytest.mark.parametrize("value", ["", "27AAPFU0939F1Z", "27AAPFU0939F1ZVX", "99AAPFU0939F1AV", "27aapfu0939f1zv!"])
def test_malformed_gstins_are_invalid(value):
    assert not is_valid_gstin(value)


def test_pan_validation_and_gstin_embedding():
    assert is_valid_pan("AAPFU0939F")
    assert not is_valid_pan("AAPXU0939F")       # X is not a valid holder-type character
    assert pan_from_gstin("27AAPFU0939F1ZV") == "AAPFU0939F"


@pytest.mark.parametrize(
    "ocr_text, expected",
    [
        ("27AAPFU0939F1ZV", "27AAPFU0939F1ZV"),     # already valid
        ("27AAPFUO939F1ZV", "27AAPFU0939F1ZV"),     # letter O in a digit slot
        ("Z7AAPFU0939F1ZV", "27AAPFU0939F1ZV"),     # Z read for 2 in the state code
        ("27AAPFU0939F12V", "27AAPFU0939F1ZV"),     # fixed 'Z' read as '2'
        ("27AAPFU0939FIZV", "27AAPFU0939F1ZV"),     # entity number 1 read as I
        ("33AXUCM500651ZH", "33AXUCM5006S1ZH"),     # S read as 5 in a letter slot
        ("27LENCS1791C1Z0", "27LENCS1791C1ZO"),     # check character O read as 0 (seen in real OCR output)
    ],
)
def test_repair_gstin_fixes_ocr_confusions(ocr_text, expected):
    assert repair_gstin(ocr_text) == expected


def test_repair_returns_none_when_no_valid_reading():
    assert repair_gstin("27AAPFU0939F1ZQ") is None
    assert repair_gstin("short") is None


def test_ocr_misread_gstin_is_repaired_and_marked(ner):
    entity = labels(ner.extract("Company: Sunrise Agro Foods\nGSTIN:27LENCS1791C1Z0"), "GSTIN")[0]
    assert entity.normalized == "27LENCS1791C1ZO"
    assert entity.valid and entity.attributes["ocr_corrected"]
    assert entity.attributes["embedded_pan"] == "LENCS1791C"


def test_unrepairable_loose_match_is_dropped(ner):
    assert labels(ner.extract("Reference ZOOOOOOOOOOOZ2O0 noted"), "GSTIN") == []


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Revenue of Rs. 12.5 crore", 125_000_000),
        ("a cheque of ₹3,50,000 was issued", 350_000),
        ("INR 45 lakh sanctioned", 4_500_000),
        ("turnover of 182.40 crore", 1_824_000_000),
        ("USD-free amount Rs 1,200", 1_200),
        ("valued at 2.5 billion", 2_500_000_000),
    ],
)
def test_money_is_normalised_to_inr(ner, text, expected):
    money = labels(ner.extract(text), "MONEY")
    assert money and money[0].normalized == pytest.approx(expected)


def test_normalize_money_rejects_garbage():
    assert normalize_money("1,2,3.x", None) is None


def test_identifiers_ratings_people_and_orgs(ner):
    text = (
        "Meridian Steel Components Limited (CIN U28910TN1999PLC123456, PAN AXUCM5006S, "
        "IFSC HDFC0001234) is rated CRiSIL BB+ (Negative). Directors: Mr. Raghavan Iyer and Ms. Neha Kulkarni. "
        "FY2023-24 results were adopted on 31 March 2024; margin 7.1%."
    )
    entities = ner.extract(text)
    assert labels(entities, "CIN")[0].attributes == {"listing_status": "unlisted", "state": "TN", "incorporation_year": 1999}
    assert labels(entities, "PAN")[0].attributes["holder_type"] == "company"
    assert labels(entities, "IFSC")[0].attributes["bank_code"] == "HDFC"
    rating = labels(entities, "RATING")[0]
    assert rating.normalized == "BB+" and rating.attributes["outlook"] == "Negative"
    assert {e.normalized for e in labels(entities, "PERSON")} == {"Raghavan Iyer", "Neha Kulkarni"}
    assert "Meridian Steel Components Limited" in {e.normalized for e in labels(entities, "ORG")}
    assert labels(entities, "PERCENT")[0].normalized == 7.1
    assert labels(entities, "FISCAL_YEAR") and labels(entities, "DATE")


def test_overlapping_spans_resolve_to_highest_priority_label(ner):
    entities = ner.extract("GSTIN 27AAPFU0939F1ZV")
    assert [e.label for e in entities] == ["GSTIN"]       # the embedded PAN is not double-counted


def test_summary_reports_first_valid_identifiers_and_invalid_ones(ner):
    valid = "27AAPFU0939F1ZV"
    entities = ner.extract(f"Seller {valid}. Buyer 27AAPFU0939F1ZQ. PAN AAPFU0939F")
    summary = ner.summarize(entities)
    assert summary["gstin"] == valid
    assert summary["pan"] == "AAPFU0939F"
    assert summary["invalid_identifiers"] == ["27AAPFU0939F1ZQ"]


def test_empty_text_returns_no_entities(ner):
    assert ner.extract("") == []
    assert ner.summarize([])["entity_counts"] == {}
