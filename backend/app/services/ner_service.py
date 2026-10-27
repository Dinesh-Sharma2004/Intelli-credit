from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# 4th character of a PAN encodes the holder type
PAN_HOLDER_TYPES = {
    "A": "association_of_persons",
    "B": "body_of_individuals",
    "C": "company",
    "F": "firm_llp",
    "G": "government",
    "H": "hindu_undivided_family",
    "J": "artificial_juridical_person",
    "L": "local_authority",
    "P": "individual",
    "T": "trust",
    "K": "krish",
}
UNIT_MULTIPLIERS = {
    "crore": 1e7, "crores": 1e7, "cr": 1e7, "cr.": 1e7,
    "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5,
    "million": 1e6, "mn": 1e6,
    "billion": 1e9, "bn": 1e9,
    "thousand": 1e3,
}
MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
_UNIT = r"(crores?|cr\.?|lakhs?|lacs?|million|mn|billion|bn|thousand)\b"

# OCR commonly confuses these glyphs; used to repair identifiers by position type.
OCR_TO_DIGIT = {"O": "0", "D": "0", "Q": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6"}
OCR_TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G"}
GSTIN_DIGIT_POSITIONS = (0, 1, 7, 8, 9, 10)
GSTIN_LETTER_POSITIONS = (2, 3, 4, 5, 6, 11)

GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
PAN_RE = re.compile(r"\b[A-Z]{3}[ABCFGHLJPTK][A-Z]\d{4}[A-Z]\b")

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("GSTIN", GSTIN_RE),
    # loose shape for OCR output; only kept if repair yields a valid check digit
    ("GSTIN", re.compile(r"\b[0-9ODQILZSBG]{2}[A-Z0-9]{5}[0-9ODQILZSBG]{4}[A-Z0-9][0-9A-Z][Z2][0-9A-Z]\b")),
    ("CIN", re.compile(r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b")),
    ("PAN", PAN_RE),
    ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    ("RATING", re.compile(
        r"\b((?i:CRISIL|ICRA|CARE|India Ratings|Brickwork|Acuite))\s+(AAA|AA|A|BBB|BB|B|C|D)([+-])?"
        r"(?:\s*\((Stable|Negative|Positive|Developing)\))?",
    )),
    ("MONEY", re.compile(r"(?:Rs\.?|INR|₹)\s?(\d[\d,]*(?:\.\d+)?)(?:\s*" + _UNIT + r")?", re.IGNORECASE)),
    ("MONEY", re.compile(r"\b(\d[\d,]*(?:\.\d+)?)\s*" + _UNIT, re.IGNORECASE)),
    ("PERCENT", re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s?%")),
    ("DATE", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-](?:\d{4}|\d{2})\b")),
    ("DATE", re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:" + MONTHS + r")[a-z]*,?\s+\d{4}\b")),
    ("FISCAL_YEAR", re.compile(r"\bFY\s?'?(\d{2}|\d{4})(?:\s?[-–/]\s?(\d{2}|\d{4}))?\b")),
    ("PERSON", re.compile(r"\b(?:Mr|Mrs|Ms|Shri|Smt|Dr)\.?\s+([A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+){0,3})")),
    ("ORG", re.compile(
        r"\b((?:[A-Z][A-Za-z0-9&'\-]*\.?\s+){1,6}"
        r"(?:Private Limited|Pvt\.?\s?Ltd\.?|Limited|Ltd\.?|LLP|Bank|Corporation|Industries|Enterprises))(?![A-Za-z])"
    )),
]
# When spans overlap, the earlier label in this list wins
LABEL_PRIORITY = ["GSTIN", "CIN", "PAN", "IFSC", "RATING", "MONEY", "PERCENT", "DATE", "FISCAL_YEAR", "PERSON", "ORG"]


@dataclass
class Entity:
    label: str
    text: str
    start: int
    end: int
    normalized: Any = None
    valid: bool | None = None
    attributes: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def gstin_check_digit(first14: str) -> str:
    """Mod-36 check digit used by GSTN for the 15th GSTIN character."""
    total = 0
    for index, char in enumerate(first14.upper()):
        value = GSTIN_CHARSET.index(char)
        product = value * (2 if index % 2 else 1)
        total += product // 36 + product % 36
    return GSTIN_CHARSET[(36 - total % 36) % 36]


def is_valid_gstin(gstin: str) -> bool:
    gstin = gstin.strip().upper()
    if not GSTIN_RE.fullmatch(gstin):
        return False
    if not 1 <= int(gstin[:2]) <= 38 and gstin[:2] not in {"97", "99"}:
        return False
    return gstin_check_digit(gstin[:14]) == gstin[14]


def repair_gstin(raw: str) -> str | None:
    """Fix OCR glyph confusions using GSTIN's positional structure; None if no valid reading exists."""
    chars = list(raw.strip().upper())
    if len(chars) != 15:
        return None
    for position in GSTIN_DIGIT_POSITIONS:
        chars[position] = OCR_TO_DIGIT.get(chars[position], chars[position])
    for position in GSTIN_LETTER_POSITIONS:
        chars[position] = OCR_TO_LETTER.get(chars[position], chars[position])
    if chars[13] == "2":
        chars[13] = "Z"
    candidates = ["".join(chars)]
    for position in (12, 14):            # alphanumeric positions: try both readings
        expanded = []
        for candidate in candidates:
            expanded.append(candidate)
            alternative = OCR_TO_DIGIT.get(candidate[position]) or OCR_TO_LETTER.get(candidate[position])
            if alternative:
                expanded.append(candidate[:position] + alternative + candidate[position + 1:])
        candidates = expanded
    return next((candidate for candidate in candidates if is_valid_gstin(candidate)), None)


def is_valid_pan(pan: str) -> bool:
    return bool(PAN_RE.fullmatch(pan.strip().upper()))


def pan_from_gstin(gstin: str) -> str:
    return gstin.strip().upper()[2:12]


def normalize_money(amount: str, unit: str | None) -> float | None:
    try:
        value = float(amount.replace(",", ""))
    except ValueError:
        return None
    if unit:
        value *= UNIT_MULTIPLIERS.get(unit.lower().rstrip("."), UNIT_MULTIPLIERS.get(unit.lower(), 1.0))
    return round(value, 2)


class FinancialNERService:
    """Rule-based named-entity recognition tuned for Indian credit documents.

    Recognises statutory identifiers (validated), monetary amounts normalised to INR
    from lakh/crore notation, percentages, dates, fiscal years, credit ratings,
    organisations and persons. An optional Hugging Face token-classification model can
    add generic PER/ORG/LOC entities when it is available locally.
    """

    def __init__(self, transformer_model: str | None = None):
        self.transformer_model = transformer_model
        self._hf_pipeline = None

    def extract(self, text: str, max_entities: int = 400) -> list[Entity]:
        if not text:
            return []
        candidates: list[Entity] = []
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                entity = self._build_entity(label, match)
                if entity is not None:
                    candidates.append(entity)
        candidates.extend(self._transformer_entities(text))
        return self._resolve_overlaps(candidates)[:max_entities]

    def summarize(self, entities: list[Entity]) -> dict:
        counts: dict[str, int] = {}
        for entity in entities:
            counts[entity.label] = counts.get(entity.label, 0) + 1
        first_valid = lambda label: next((e.normalized for e in entities if e.label == label and e.valid), None)
        return {
            "entity_counts": counts,
            "pan": first_valid("PAN"),
            "gstin": first_valid("GSTIN"),
            "cin": first_valid("CIN"),
            "invalid_identifiers": [e.text for e in entities if e.label in {"GSTIN", "PAN", "CIN"} and e.valid is False],
            "organisations": sorted({e.normalized for e in entities if e.label == "ORG"})[:15],
            "persons": sorted({e.normalized for e in entities if e.label == "PERSON"})[:15],
            "ratings": [e.normalized for e in entities if e.label == "RATING"][:10],
            "monetary_amounts_inr": [e.normalized for e in entities if e.label == "MONEY" and e.normalized is not None][:40],
        }

    def _build_entity(self, label: str, match: re.Match) -> Entity | None:
        text = match.group(0).strip()
        start, end = match.start(), match.start() + len(text)
        if label == "GSTIN":
            gstin = text.upper()
            valid = is_valid_gstin(gstin)
            corrected = False
            if not valid:
                repaired = repair_gstin(gstin)
                if repaired:
                    gstin, valid, corrected = repaired, True, True
                elif not GSTIN_RE.fullmatch(gstin):
                    return None          # loose OCR-shaped match that is not a GSTIN
            embedded_pan = pan_from_gstin(gstin)
            return Entity(label, text, start, end, gstin, valid, {
                "state_code": gstin[:2],
                "embedded_pan": embedded_pan,
                "pan_format_valid": is_valid_pan(embedded_pan),
                "ocr_corrected": corrected,
            })
        if label == "PAN":
            return Entity(label, text, start, end, text.upper(), True, {"holder_type": PAN_HOLDER_TYPES.get(text[3], "unknown")})
        if label == "CIN":
            return Entity(label, text, start, end, text, True, {
                "listing_status": "listed" if text[0] == "L" else "unlisted",
                "state": text[6:8],
                "incorporation_year": int(text[8:12]),
            })
        if label == "IFSC":
            return Entity(label, text, start, end, text, True, {"bank_code": text[:4]})
        if label == "RATING":
            agency, grade, modifier, outlook = match.group(1), match.group(2), match.group(3) or "", match.group(4)
            return Entity(label, text, start, end, f"{grade}{modifier}", True, {"agency": agency, "outlook": outlook})
        if label == "MONEY":
            groups = [g for g in match.groups()]
            amount, unit = groups[0], groups[1] if len(groups) > 1 else None
            value = normalize_money(amount, unit)
            if value is None:
                return None
            return Entity(label, text, start, end, value, True, {"unit": (unit or "rupees").lower()})
        if label == "PERCENT":
            value = float(match.group(1))
            return Entity(label, text, start, end, value, value <= 100)
        if label == "PERSON":
            return Entity(label, text, start, end, match.group(1).strip(), True)
        if label == "ORG":
            name = " ".join(match.group(1).split())
            if name.split()[0] in {"The", "This", "Our", "Its"} and len(name.split()) > 2:
                name = " ".join(name.split()[1:])
            return Entity(label, text, start, end, name, True)
        return Entity(label, text, start, end, text, True)

    def _resolve_overlaps(self, candidates: list[Entity]) -> list[Entity]:
        rank = {label: index for index, label in enumerate(LABEL_PRIORITY)}
        ordered = sorted(candidates, key=lambda e: (rank.get(e.label, 99), -(e.end - e.start), e.start))
        taken: list[tuple[int, int]] = []
        kept: list[Entity] = []
        for entity in ordered:
            if any(entity.start < end and start < entity.end for start, end in taken):
                continue
            taken.append((entity.start, entity.end))
            kept.append(entity)
        return sorted(kept, key=lambda e: e.start)

    def _transformer_entities(self, text: str) -> list[Entity]:
        if not self.transformer_model:
            return []
        try:
            if self._hf_pipeline is None:
                from transformers import pipeline

                self._hf_pipeline = pipeline(
                    "token-classification", model=self.transformer_model, aggregation_strategy="simple"
                )
            results = self._hf_pipeline(text[:4000])
        except Exception:
            return []
        label_map = {"PER": "PERSON", "ORG": "ORG", "LOC": "LOCATION"}
        return [
            Entity(label_map.get(item["entity_group"], item["entity_group"]), item["word"], int(item["start"]),
                   int(item["end"]), item["word"], True, {"score": round(float(item["score"]), 4), "source": "transformer"})
            for item in results
            if item.get("score", 0) >= 0.85
        ]
