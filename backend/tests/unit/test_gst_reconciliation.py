from datetime import date, timedelta

import pytest

from app.services.gst_reconciliation import GSTReconciliationService, robust_z_scores

MONTHS = [f"2023-{m:02d}" for m in range(4, 13)] + [f"2024-{m:02d}" for m in range(1, 4)]


def gst_month(period, value=1_00_00_000.0, gap=0.0, itc_excess=0.0, delay_days=-2):
    year, month = map(int, period.split("-"))
    due = date(year + (month == 12), month % 12 + 1, 20)
    itc = value * 0.62 * 0.18
    return {
        "period": period,
        "gstr1_taxable_value": value,
        "gstr3b_taxable_value": value * (1 - gap),
        "itc_available_2b": itc,
        "itc_claimed_3b": itc * (1 + itc_excess),
        "due_date_3b": due.isoformat(),
        "filing_date_3b": (due + timedelta(days=delay_days)).isoformat(),
    }


def bank_credits(coverage=1.0, value=1_00_00_000.0):
    return [{"date": f"{p}-10", "counterparty": "Customer A", "credit": value * 1.18 * coverage, "debit": ""} for p in MONTHS]


@pytest.fixture
def service():
    return GSTReconciliationService()


def test_clean_borrower_has_no_flags_and_negligible_risk(service):
    rows = [gst_month(p, value=1e7 * (1 + 0.02 * (i % 3))) for i, p in enumerate(MONTHS)]
    result = service.reconcile(rows, bank_credits())
    assert result["flags"] == []
    assert result["anomalous_periods"] == []          # IsolationForest must not invent outliers
    assert result["risk_score"] < 0.05
    assert result["summary"]["periods_analysed"] == 12


def test_outward_gap_and_itc_excess_are_flagged(service):
    rows = [gst_month(p, gap=0.15, itc_excess=0.3) for p in MONTHS]
    result = service.reconcile(rows, bank_credits(0.85))
    summary = result["summary"]
    assert summary["months_outward_gap_breach"] == 12
    assert summary["months_itc_excess_breach"] == 12
    assert summary["mean_itc_excess_pct"] == pytest.approx(0.3, abs=1e-3)
    assert any("GSTR-1 vs GSTR-3B" in flag for flag in result["flags"])
    assert any("ITC claimed" in flag for flag in result["flags"])
    assert result["risk_score"] > 0.4


def test_bank_coverage_below_threshold_signals_inflated_sales(service):
    result = service.reconcile([gst_month(p) for p in MONTHS], bank_credits(coverage=0.4))
    assert result["summary"]["median_bank_coverage_ratio"] == pytest.approx(0.4, abs=1e-3)
    assert any("possible inflated sales" in flag for flag in result["flags"])


def test_bank_coverage_far_above_turnover_signals_unreported_sales(service):
    result = service.reconcile([gst_month(p) for p in MONTHS], bank_credits(coverage=2.0))
    assert any("unreported sales" in flag for flag in result["flags"])


def test_late_filings_are_counted(service):
    rows = [gst_month(p, delay_days=15 if i < 3 else -1) for i, p in enumerate(MONTHS)]
    result = service.reconcile(rows, bank_credits())
    assert result["summary"]["late_filings"] == 3
    assert result["summary"]["max_filing_delay_days"] == 15
    assert any("filed late in 3" in flag for flag in result["flags"])


@pytest.mark.parametrize(
    "debit_date, debit_amount, debit_party, expected_pairs",
    [
        ("2024-01-11", 50_00_000, "Arcadia Metals", 1),     # next day, same amount, same party
        ("2024-01-10", 50_50_000, "Arcadia Metals", 1),     # same day, within 2%
        ("2024-01-15", 50_00_000, "Arcadia Metals", 0),     # outside the 3-day window
        ("2024-01-11", 55_00_000, "Arcadia Metals", 0),     # amount differs by 10%
        ("2024-01-11", 50_00_000, "Someone Else", 0),       # different counterparty
        ("2024-01-09", 50_00_000, "Arcadia Metals", 0),     # money went out before it came in
    ],
)
def test_round_trip_detection(service, debit_date, debit_amount, debit_party, expected_pairs):
    txns = [
        {"date": "2024-01-10", "counterparty": "Arcadia Metals", "credit": 50_00_000, "debit": ""},
        {"date": debit_date, "counterparty": debit_party, "credit": "", "debit": debit_amount},
    ]
    assert len(service.detect_round_trips(txns)) == expected_pairs


def test_each_debit_is_matched_at_most_once(service):
    txns = [
        {"date": "2024-01-10", "counterparty": "X", "credit": 1000, "debit": ""},
        {"date": "2024-01-10", "counterparty": "X", "credit": 1000, "debit": ""},
        {"date": "2024-01-11", "counterparty": "X", "credit": "", "debit": 1000},
    ]
    assert len(service.detect_round_trips(txns)) == 1


def test_spike_month_is_reported_as_anomalous(service):
    rows = [gst_month(p, gap=0.01) for p in MONTHS]
    rows[5] = gst_month(MONTHS[5], gap=0.45)
    result = service.reconcile(rows, bank_credits())
    periods = [p["period"] for p in result["anomalous_periods"]]
    assert periods == [MONTHS[5]]
    assert result["anomalous_periods"][0]["signals"][0]["metric"] == "outward_gap_pct"


def test_robust_z_scores():
    scores = robust_z_scores([1.0, 1.1, 0.9, 1.0, 1.05, 9.0])
    assert abs(scores[-1]) > 3.5 and all(abs(s) < 3.5 for s in scores[:-1])
    assert robust_z_scores([2.0, 2.0, 2.0]) == [0.0, 0.0, 0.0]
    assert robust_z_scores([1.0]) == [0.0]


def test_risk_score_is_bounded_and_monotone_in_itc_excess(service):
    scores = [service.reconcile([gst_month(p, itc_excess=x) for p in MONTHS], bank_credits())["risk_score"] for x in (0, 0.1, 0.2, 0.5, 2.0)]
    assert scores == sorted(scores)
    assert 0.0 <= scores[0] and scores[-1] <= 1.0


def test_tolerates_missing_and_malformed_values(service):
    rows = [{"period": "2023-04", "gstr1_taxable_value": "1,00,000", "gstr3b_taxable_value": "", "itc_available_2b": "abc"}]
    result = service.reconcile(rows, [])
    assert result["summary"]["periods_analysed"] == 1
    assert result["monthly"][0]["itc_excess_pct"] is None
    assert result["summary"]["median_bank_coverage_ratio"] is None
