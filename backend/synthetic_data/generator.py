"""Generate synthetic borrower document packs for demos and tests.

Usage (from backend/):
    python -m synthetic_data.generator                       # writes data/synthetic/
    python -m synthetic_data.generator --out some/dir --training-csv

Three personas with deliberately different risk profiles:
  * sunrise-agro       healthy food processor: clean GST, bank credits match turnover, no litigation
  * meridian-steel     stressed auto-components maker: falling EBITDA, late GST filings, recovery suit
  * vertex-tradelinks  fraud-like commodity trader: GSTR-1/3B gap, excess ITC, round-tripping, NCLT petition

Every pack contains a text annual report PDF, a scanned (image-only) rating report PDF that
needs OCR, 12 months of GST returns (CSV), a bank statement (CSV) and application.json.
All identifiers are syntactically valid (GSTIN check digit included) but fictitious.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic"
FY_MONTHS = [(2023, m) for m in range(4, 13)] + [(2024, m) for m in range(1, 4)]
SEASONALITY = [0.92, 0.95, 0.98, 1.0, 1.02, 1.05, 1.12, 1.08, 1.0, 0.96, 0.94, 0.98]


@dataclass
class Persona:
    slug: str
    name: str
    short_name: str
    sector: str
    state_code: str
    state_abbr: str
    industry_code: str
    incorporated: int
    revenue_cr: float
    prior_revenue_cr: float
    ebitda_margin: float
    prior_ebitda_margin: float
    borrowings_cr: float
    outward_gap: float
    itc_excess: float
    bank_coverage: float
    round_trips_per_month: int
    late_months: int
    spike_months: list[int]
    requested_amount: float
    tenor_months: int
    rating: str
    rating_outlook: str
    auditor_opinion: str
    narrative: list[str]
    officer_input: dict
    related_parties: list[str] = field(default_factory=list)
    directors: list[str] = field(default_factory=list)
    pan: str = ""
    gstin: str = ""
    cin: str = ""


PERSONAS: list[Persona] = [
    Persona(
        slug="sunrise-agro", name="Sunrise Agro Foods Private Limited", short_name="Sunrise Agro Foods",
        sector="FMCG food processing", state_code="27", state_abbr="MH", industry_code="15490", incorporated=2008,
        revenue_cr=142.0, prior_revenue_cr=128.4, ebitda_margin=0.141, prior_ebitda_margin=0.136, borrowings_cr=21.5,
        outward_gap=0.004, itc_excess=0.0, bank_coverage=1.03, round_trips_per_month=0, late_months=0, spike_months=[],
        requested_amount=18_00_00_000, tenor_months=48, rating="A-", rating_outlook="Stable",
        auditor_opinion="In our opinion the financial statements give a true and fair view. Unmodified opinion.",
        narrative=[
            "Revenue grew 10.6% supported by strong distribution and export orders.",
            "Operating cash flow remained healthy and collections were disciplined, with debtor days of 38.",
            "The audit committee and board met quarterly; the company maintains an ESG policy and compliance calendar.",
            "Management continued strategic initiatives in packaging automation with stable margins.",
        ],
        officer_input={"capacity_utilization_pct": 82, "governance_score": 0.82, "management_quality": 8,
                       "inventory_observation": 8, "customer_concentration": 22,
                       "notes": "Plant visit: stable operations, healthy inventory, efficient dispatch. Capacity utilization 82%."},
        directors=["Mr. Arvind Kulkarni", "Ms. Neha Kulkarni"],
    ),
    Persona(
        slug="meridian-steel", name="Meridian Steel Components Limited", short_name="Meridian Steel Components",
        sector="steel engineering components", state_code="33", state_abbr="TN", industry_code="28910", incorporated=1999,
        revenue_cr=268.0, prior_revenue_cr=284.5, ebitda_margin=0.071, prior_ebitda_margin=0.104, borrowings_cr=96.0,
        outward_gap=0.035, itc_excess=0.06, bank_coverage=0.84, round_trips_per_month=0, late_months=4, spike_months=[8],
        requested_amount=40_00_00_000, tenor_months=36, rating="BB+", rating_outlook="Negative",
        auditor_opinion="Without qualifying our opinion, we draw attention to the emphasis of matter on overdue trade receivables.",
        narrative=[
            "Revenue declined 5.8% due to weak demand from automotive customers; EBITDA decline reflected margin pressure from steel prices.",
            "Receivable days rose to 96 as collections delayed from two large customers.",
            "The company availed restructuring of a working capital term loan and debt increased.",
            "A recovery suit was filed by a vendor and a legal notice under section 138 was received.",
        ],
        officer_input={"capacity_utilization_pct": 58, "governance_score": 0.6, "management_quality": 6,
                       "inventory_observation": 5, "customer_concentration": 48,
                       "notes": "Factory visit: two lines idle, labour issue at night shift, delay in collections. Utilization 58%."},
        directors=["Mr. Raghavan Iyer", "Mr. Suresh Pillai"],
    ),
    Persona(
        slug="vertex-tradelinks", name="Vertex Tradelinks Private Limited", short_name="Vertex Tradelinks",
        sector="commodity trading", state_code="24", state_abbr="GJ", industry_code="51909", incorporated=2017,
        revenue_cr=182.4, prior_revenue_cr=132.1, ebitda_margin=0.028, prior_ebitda_margin=0.031, borrowings_cr=74.0,
        outward_gap=0.17, itc_excess=0.27, bank_coverage=0.47, round_trips_per_month=3, late_months=7, spike_months=[3, 9],
        requested_amount=35_00_00_000, tenor_months=24, rating="B", rating_outlook="Negative",
        auditor_opinion="Qualified opinion: we were unable to obtain sufficient evidence for related party balances. Material uncertainty related to going concern.",
        narrative=[
            "Revenue grew 38% driven by high-volume trading with group entities and related party sales.",
            "Significant related party transactions with Arcadia Metals Private Limited and Krish Impex Private Limited.",
            "Overdue payables to banks were reported and the account was classified as SMA-2 during the year.",
            "Same day receipts and payments were routed through group entities for trade settlement.",
        ],
        officer_input={"capacity_utilization_pct": 40, "governance_score": 0.45, "management_quality": 4,
                       "inventory_observation": 3, "customer_concentration": 71,
                       "notes": "Site visit: warehouse mostly empty, weak records, governance issue with related party routing. Utilization 40%."},
        related_parties=["Arcadia Metals Private Limited", "Krish Impex Private Limited"],
        directors=["Mr. Kunal Shah", "Mrs. Rekha Shah"],
    ),
]


# ---------------------------------------------------------------------- identifiers
def make_identifiers(persona: Persona, rng: random.Random) -> None:
    from app.services.ner_service import gstin_check_digit

    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    pan = "".join(rng.choice(letters) for _ in range(3)) + "C" + persona.name[0] + f"{rng.randint(1000, 9999)}" + rng.choice(letters)
    gst14 = f"{persona.state_code}{pan}1Z"
    persona.pan = pan
    persona.gstin = gst14 + gstin_check_digit(gst14)
    persona.cin = f"U{persona.industry_code}{persona.state_abbr}{persona.incorporated}PTC{rng.randint(100000, 999999)}"
    if persona.name.endswith("Limited") and "Private" not in persona.name:
        persona.cin = persona.cin.replace("PTC", "PLC")


# ---------------------------------------------------------------------- GST + bank
def gst_rows(persona: Persona, rng: random.Random) -> list[dict]:
    rows = []
    monthly = persona.revenue_cr * 1e7 / 12
    late = set(rng.sample(range(12), persona.late_months)) if persona.late_months else set()
    for index, (year, month) in enumerate(FY_MONTHS):
        taxable = monthly * SEASONALITY[index] * rng.uniform(0.97, 1.03)
        gap = persona.outward_gap * rng.uniform(0.6, 1.4)
        itc_excess = persona.itc_excess * rng.uniform(0.6, 1.4)
        if index in persona.spike_months:
            gap, itc_excess = gap + 0.35, itc_excess + 0.4
        itc_available = taxable * 0.62 * 0.18
        due = date(year + (month == 12), month % 12 + 1, 20)
        filed = due + timedelta(days=rng.randint(9, 48)) if index in late else due - timedelta(days=rng.randint(0, 4))
        rows.append({
            "period": f"{year}-{month:02d}",
            "gstin": persona.gstin,
            "gstr1_taxable_value": round(taxable, 2),
            "gstr3b_taxable_value": round(taxable * (1 - gap), 2),
            "gstr3b_tax_paid": round(taxable * (1 - gap) * 0.18, 2),
            "itc_available_2b": round(itc_available, 2),
            "itc_claimed_3b": round(itc_available * (1 + itc_excess), 2),
            "due_date_3b": due.isoformat(),
            "filing_date_3b": filed.isoformat(),
        })
    return rows


def bank_rows(persona: Persona, gst: list[dict], rng: random.Random) -> list[dict]:
    customers = [f"{persona.short_name.split()[0]} Customer {c}" for c in "ABCDEFGH"]
    vendors = ["Bharat Packaging Supplies", "Western Logistics", "Coastal Raw Materials", "Metro Power Utilities"]
    txns: list[dict] = []
    for index, (year, month) in enumerate(FY_MONTHS):
        receipts_total = gst[index]["gstr3b_taxable_value"] * 1.18 * persona.bank_coverage * rng.uniform(0.95, 1.05)
        parts = rng.randint(8, 12)
        weights = [rng.uniform(0.5, 1.5) for _ in range(parts)]
        for share in weights:
            day = rng.randint(1, 28)
            txns.append({"date": date(year, month, day).isoformat(), "description": "NEFT receipt",
                         "counterparty": rng.choice(customers), "debit": "", "credit": round(receipts_total * share / sum(weights), 2)})
        for vendor in vendors:
            txns.append({"date": date(year, month, rng.randint(1, 28)).isoformat(), "description": "RTGS payment",
                         "counterparty": vendor, "debit": round(receipts_total * rng.uniform(0.12, 0.2), 2), "credit": ""})
        txns.append({"date": date(year, month, 20).isoformat(), "description": "GST payment", "counterparty": "GSTN",
                     "debit": round(gst[index]["gstr3b_tax_paid"], 2), "credit": ""})
        for _ in range(persona.round_trips_per_month):
            party = rng.choice(persona.related_parties)
            day = rng.randint(1, 24)
            amount = round(rng.uniform(1.5, 4.0) * 1e7, 2)
            txns.append({"date": date(year, month, day).isoformat(), "description": "Inward transfer",
                         "counterparty": party, "debit": "", "credit": amount})
            txns.append({"date": date(year, month, day + rng.randint(0, 2)).isoformat(), "description": "Outward transfer",
                         "counterparty": party, "debit": round(amount * rng.uniform(0.995, 1.005), 2), "credit": ""})
    txns.sort(key=lambda t: (t["date"], t["description"]))
    balance = 2.5e7
    for txn in txns:
        balance += float(txn["credit"] or 0) - float(txn["debit"] or 0)
        txn["balance"] = round(balance, 2)
    return txns


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------- PDFs
def write_annual_report(path: Path, persona: Persona) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    ebitda = persona.revenue_cr * persona.ebitda_margin
    prior_ebitda = persona.prior_revenue_cr * persona.prior_ebitda_margin
    story = [
        Paragraph(f"{persona.name}", styles["Title"]),
        Paragraph("Annual Report FY2023-24", styles["Heading2"]),
        Paragraph(
            f"CIN: {persona.cin} | PAN: {persona.pan} | GSTIN: {persona.gstin}. "
            f"Sector: {persona.sector}. Incorporated in {persona.incorporated}.", styles["Normal"]),
        Spacer(1, 8),
        Paragraph("Directors' Report", styles["Heading3"]),
        Paragraph(
            f"The Board of {persona.name} presents the annual report for the year ended 31 March 2024. "
            f"Revenue from operations was Rs. {persona.revenue_cr:.2f} crore against Rs. {persona.prior_revenue_cr:.2f} crore in FY2022-23. "
            f"EBITDA was Rs. {ebitda:.2f} crore with an EBITDA margin of {persona.ebitda_margin:.1%}. "
            f"Total borrowings stood at Rs. {persona.borrowings_cr:.2f} crore.", styles["Normal"]),
    ]
    story += [Paragraph(line, styles["Normal"]) for line in persona.narrative]
    story += [
        Paragraph("Board of Directors: " + ", ".join(persona.directors) + ".", styles["Normal"]),
        Spacer(1, 8),
        Paragraph("Key financials (Rs. crore)", styles["Heading3"]),
    ]
    table = Table([
        ["Particulars", "FY2022-23", "FY2023-24"],
        ["Revenue from operations", f"{persona.prior_revenue_cr:.2f}", f"{persona.revenue_cr:.2f}"],
        ["EBITDA", f"{prior_ebitda:.2f}", f"{ebitda:.2f}"],
        ["EBITDA margin", f"{persona.prior_ebitda_margin:.1%}", f"{persona.ebitda_margin:.1%}"],
        ["Total borrowings", f"{persona.borrowings_cr * 0.9:.2f}", f"{persona.borrowings_cr:.2f}"],
    ])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    story += [table, Spacer(1, 8), Paragraph("Independent Auditor's Report", styles["Heading3"]),
              Paragraph(persona.auditor_opinion, styles["Normal"])]
    if persona.related_parties:
        story.append(Paragraph(
            "Related party disclosure: balances with " + " and ".join(persona.related_parties) +
            " aggregated Rs. 41.60 crore at year end.", styles["Normal"]))
    SimpleDocTemplate(str(path), pagesize=A4, title=f"{persona.short_name} Annual Report FY24").build(story)


def write_scanned_rating_report(path: Path, persona: Persona) -> None:
    """Image-only PDF (no text layer), like a scanned rating letter, so ingestion must OCR it."""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1654, 2339), "white")
    draw = ImageDraw.Draw(image)
    title, body = ImageFont.load_default(size=46), ImageFont.load_default(size=36)
    lines = [
        (title, "CRISIL Ratings - Rating Rationale"),
        (body, f"Company: {persona.short_name}"),
        (body, f"GSTIN: {persona.gstin}"),
        (body, f"Long Term Rating: CRISIL {persona.rating} ({persona.rating_outlook})"),
        (body, "Key financials       FY23        FY24"),
        (body, f"Revenue Rs crore     {persona.prior_revenue_cr:.1f}       {persona.revenue_cr:.1f}"),
        (body, f"EBITDA margin %      {persona.prior_ebitda_margin * 100:.1f}         {persona.ebitda_margin * 100:.1f}"),
    ]
    if persona.rating_outlook == "Negative":
        lines.append((body, "Outlook revised to negative; rating downgrade reflects stress."))
    else:
        lines.append((body, "Outlook stable; healthy liquidity and low leverage."))
    y = 160
    for font, text in lines:
        draw.text((120, y), text, fill="black", font=font)
        y += 110
    image.save(path, "PDF", resolution=200.0)


# ---------------------------------------------------------------------- research corpus
def research_corpus(personas: dict[str, Persona]) -> list[dict]:
    s, m, v = personas["sunrise-agro"], personas["meridian-steel"], personas["vertex-tradelinks"]
    docs = [
        # Sunrise Agro Foods: clean record, positive news
        {"source": "MCA", "entity": s.name, "date": "2024-08-30", "title": f"{s.short_name}: annual return and financial statements filed on time",
         "text": f"{s.name} filed form AOC-4 and MGT-7 for FY2023-24 within the due date. No charge modification or director change was recorded. The company is active and compliant."},
        {"source": "News", "entity": s.name, "date": "2024-06-12", "title": f"{s.short_name} wins export order from Middle East retailer",
         "text": f"{s.short_name} secured an order win worth Rs. 22 crore for packaged snacks. Promoters said record demand and robust distribution support expansion."},
        # Meridian Steel Components: stress signals
        {"source": "e-Courts", "entity": m.name, "date": "2024-07-18", "title": f"Recovery suit against {m.short_name} by vendor",
         "text": f"A commercial court in Chennai admitted a recovery suit of Rs. 3.8 crore filed by a raw material vendor against {m.name}. A separate complaint under section 138 for cheque dishonour is pending.",
         "tags": ["recovery suit", "cheque dishonour"]},
        {"source": "MCA", "entity": m.name, "date": "2024-05-02", "title": f"Independent director resigned at {m.short_name}",
         "text": f"An independent director of {m.name} resigned citing pre-occupation. The annual return for FY2022-23 was filed with a delay of 41 days."},
        {"source": "News", "entity": m.name, "date": "2024-09-05", "title": f"{m.short_name} cuts shifts amid auto slowdown",
         "text": f"{m.short_name} cut night shifts at its Hosur plant as automotive demand slowed. Workers staged a brief strike over delayed wages; margins remain under price pressure."},
        # Vertex Tradelinks: severe signals
        {"source": "e-Courts", "entity": v.name, "date": "2024-08-21", "title": f"NCLT admits insolvency petition against {v.short_name}",
         "text": f"The NCLT Ahmedabad bench admitted a section 9 petition by an operational creditor against {v.name} for unpaid dues of Rs. 6.2 crore, initiating CIRP proceedings.",
         "tags": ["NCLT", "IBC section 9", "CIRP"]},
        {"source": "e-Courts", "entity": v.name, "date": "2024-03-14", "title": f"DRT recovery application by bank against {v.short_name}",
         "text": f"A public sector bank filed a debt recovery application at DRT against {v.name} and its guarantors after the account turned NPA."},
        {"source": "News", "entity": v.name, "date": "2024-09-28", "title": f"Enforcement Directorate searches premises linked to {v.short_name} promoters",
         "text": f"The Enforcement Directorate searched premises of the promoters of {v.short_name} in a fake GST invoice and money laundering probe. Officials alleged circular trading through group companies."},
        {"source": "MCA", "entity": v.name, "date": "2024-07-01", "title": f"Statutory auditor of {v.short_name} resigned",
         "text": f"The statutory auditor of {v.name} resigned mid-term. Charge satisfaction filings were overdue and the company paid additional fees for late filing."},
        # Distractors with similar names: must NOT be attributed to the borrowers
        {"source": "News", "entity": "Sunrise Pharma Limited", "date": "2024-09-10", "title": "Sunrise Pharma promoters arrested in fraud case",
         "text": "Promoters of Sunrise Pharma Limited were arrested by the CBI in a bank fraud and money laundering case."},
        {"source": "e-Courts", "entity": "Vertex Logistics Limited", "date": "2024-04-04", "title": "Winding up petition against Vertex Logistics",
         "text": "A winding up petition and insolvency application were filed against Vertex Logistics Limited by lenders."},
        {"source": "e-Courts", "entity": "Meridian Textiles Private Limited", "date": "2024-02-20", "title": "Wilful defaulter tag for Meridian Textiles",
         "text": "A bank declared Meridian Textiles Private Limited a wilful defaulter after a forensic audit."},
        # RBI / regulator notes
        {"source": "RBI", "sector": "all", "date": "2024-08-08", "title": "RBI keeps repo rate unchanged; liquidity conditions stable",
         "text": "The monetary policy committee kept the repo rate unchanged. System liquidity remained stable and credit growth robust."},
        {"source": "RBI", "sector": "commodity trading", "date": "2024-07-25", "title": "RBI cautions banks on trade finance fraud in commodity trading",
         "text": "RBI asked banks to tighten monitoring of trade finance to commodity trading entities after cases of fraud, fake invoices and circular trading. Banks must verify GST invoices and end-use."},
        {"source": "RBI", "sector": "steel engineering components", "date": "2024-04-18", "title": "RBI flags rising stress in MSME auto component loans",
         "text": "RBI noted rising stress and delayed repayments in MSME loans to auto component and steel engineering firms amid demand slowdown."},
        # Sector intelligence
        {"source": "Sector Intelligence", "sector": "FMCG food processing", "date": "2024-09-15", "title": "Food processing: stable outlook on robust rural demand",
         "text": "Packaged food processing companies report robust demand and stable outlook as input prices ease. Margins are expected to improve."},
        {"source": "Sector Intelligence", "sector": "steel engineering components", "date": "2024-09-20", "title": "Steel components: slowdown and price pressure from imports",
         "text": "Steel engineering component makers face slowdown in automotive orders and price pressure from cheap imports, with stress on working capital."},
        {"source": "Sector Intelligence", "sector": "commodity trading", "date": "2024-09-25", "title": "Commodity trading: GST fake invoice crackdown raises stress",
         "text": "The GST fake invoice crackdown and tighter bank curbs on trade finance raise stress for small commodity traders; several entities face default and liquidation."},
    ]
    for index, doc in enumerate(docs, start=1):
        doc["id"] = f"PRS-{index:03d}"
        doc.setdefault("entity", None)
        doc.setdefault("sector", None)
        doc.setdefault("tags", [])
        doc["url"] = f"https://example.org/public-signals/{doc['id'].lower()}"
    return docs


# ---------------------------------------------------------------------- orchestration
def generate_all(out_dir: Path = DEFAULT_OUT, seed: int = 7) -> dict:
    out_dir = Path(out_dir)
    rng = random.Random(seed)
    personas = {persona.slug: Persona(**asdict(persona)) for persona in PERSONAS}
    manifest = {"seed": seed, "borrowers": {}}
    for persona in personas.values():
        make_identifiers(persona, rng)
        folder = out_dir / "borrowers" / persona.slug
        folder.mkdir(parents=True, exist_ok=True)
        gst = gst_rows(persona, rng)
        bank = bank_rows(persona, gst, rng)
        files = {
            "annual_report": folder / f"annual-report-fy24-{persona.slug}.pdf",
            "rating_report": folder / f"rating-report-scanned-{persona.slug}.pdf",
            "gst_returns": folder / f"gstr-returns-fy24-{persona.slug}.csv",
            "bank_statement": folder / f"bank-statement-fy24-{persona.slug}.csv",
        }
        write_annual_report(files["annual_report"], persona)
        write_scanned_rating_report(files["rating_report"], persona)
        write_csv(files["gst_returns"], gst)
        write_csv(files["bank_statement"], bank)
        application = {
            "borrower_name": persona.name,
            "borrower_pan": persona.pan,
            "borrower_gstin": persona.gstin,
            "cin": persona.cin,
            "sector": persona.sector,
            "requested_amount": persona.requested_amount,
            "requested_tenor_months": persona.tenor_months,
            "notes": f"Synthetic borrower ({persona.slug})",
        }
        (folder / "application.json").write_text(
            json.dumps({"application": application, "officer_input": persona.officer_input}, indent=2), encoding="utf-8"
        )
        manifest["borrowers"][persona.slug] = {
            "application": application,
            "officer_input": persona.officer_input,
            "files": {key: str(path) for key, path in files.items()},
        }
    corpus_path = out_dir / "research_corpus.jsonl"
    corpus_path.write_text("\n".join(json.dumps(doc) for doc in research_corpus(personas)) + "\n", encoding="utf-8")
    manifest["research_corpus"] = str(corpus_path)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--training-csv", action="store_true", help="also export the PD training population")
    args = parser.parse_args()
    manifest = generate_all(args.out, args.seed)
    if args.training_csv:
        from app.ml.train_pd_model import train

        train(out_dir=Path(__file__).resolve().parents[1] / "app" / "ml" / "artifacts",
              export_csv=args.out / "pd_training.csv")
    print(json.dumps({slug: info["application"]["borrower_name"] for slug, info in manifest["borrowers"].items()}, indent=2))
    print(f"research corpus: {manifest['research_corpus']}")


if __name__ == "__main__":
    main()
