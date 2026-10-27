import json

import pytest

from app.services.research_service import CONNECTORS, ResearchService, name_match, risk_severity, split_sentences


def write_corpus(path, docs):
    path.write_text("\n".join(json.dumps({"id": f"D{i}", **doc}) for i, doc in enumerate(docs)), encoding="utf-8")
    return path


@pytest.fixture
def corpus(tmp_path):
    return write_corpus(tmp_path / "corpus.jsonl", [
        {"source": "e-Courts", "entity": "Acme Foods Private Limited", "date": "2024-06-01",
         "title": "NCLT admits insolvency petition against Acme Foods",
         "text": "The NCLT admitted a section 9 insolvency petition against Acme Foods Pvt Ltd. Creditors claim unpaid dues."},
        {"source": "e-Courts", "entity": "Acme Pharma Limited", "date": "2024-06-02",
         "title": "Acme Pharma declared wilful defaulter",
         "text": "A bank declared Acme Pharma Limited a wilful defaulter after a forensic audit found fraud."},
        {"source": "News", "entity": "Acme Foods Private Limited", "date": "2022-01-01",
         "title": "Acme Foods wins order",
         "text": "Acme Foods announced an order win and robust demand for its products this quarter."},
        {"source": "RBI", "sector": "food processing", "date": "2024-05-01",
         "title": "RBI tightens risk weights for food processing loans",
         "text": "RBI announced tightening of risk weights and curbs on unsecured loans to food processing units."},
        {"source": "RBI", "sector": "all", "date": "2024-05-03",
         "title": "Policy rate unchanged", "text": "The repo rate was kept unchanged and liquidity remains stable."},
    ])


@pytest.fixture
def agent(corpus):
    return ResearchService(workers=2, timeout_seconds=5, corpus_path=corpus)


def by_source(findings):
    return {f["source_name"]: f for f in findings}


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("Acme Foods Pvt Ltd", "Acme Foods Private Limited", 1.0),
        ("ACME FOODS LIMITED", "acme foods", 1.0),
        ("Acme Pharma Limited", "Acme Foods Private Limited", 1 / 3),
        ("", "Acme", 0.0),
    ],
)
def test_name_match_ignores_legal_suffixes(a, b, expected):
    assert name_match(a, b) == pytest.approx(expected)


def test_sentence_split_keeps_abbreviations_together():
    text = "Dues of Rs. 6.2 crore are unpaid. Acme Pvt. Ltd. disputes it! Mr. Rao said no. Next sentence here."
    assert split_sentences(text) == [
        "Dues of Rs. 6.2 crore are unpaid.",
        "Acme Pvt. Ltd. disputes it!",
        "Mr. Rao said no.",
        "Next sentence here.",
    ]


def test_risk_severity_orders_signals():
    assert risk_severity("NCLT admitted an insolvency petition") > risk_severity("a penalty was levied")
    assert risk_severity("a penalty was levied") > risk_severity("order win and robust demand")
    assert risk_severity("nothing notable happened") == pytest.approx(0.05)
    assert 0.0 <= risk_severity("wilful defaulter fraud NCLT liquidation") <= 1.0


def test_entity_connectors_only_use_the_borrowers_records(agent):
    findings = by_source(agent.run_parallel_research("Acme Foods Pvt Ltd", "food processing"))
    courts = findings["e-Courts"]
    evidence_titles = [e["title"] for e in courts["payload"]["evidence"]]
    assert evidence_titles == ["NCLT admits insolvency petition against Acme Foods"]   # not Acme Pharma
    assert courts["finding_type"] == "litigation"
    assert courts["severity"] == "high"
    assert courts["payload"]["litigation_severity_index"] >= 0.8


def test_summary_is_extractive_with_citations(agent):
    courts = by_source(agent.run_parallel_research("Acme Foods Private Limited", "food processing"))["e-Courts"]
    assert "[E1]" in courts["summary"]
    assert "insolvency petition" in courts["summary"]
    assert courts["payload"]["retrieval_method"] == "tfidf"


def test_positive_old_news_is_low_risk(agent):
    news = by_source(agent.run_parallel_research("Acme Foods", "food processing"))["News"]
    assert news["payload"]["promoter_risk_score"] < 0.1
    assert news["severity"] == "low"


def test_sector_connectors_include_general_and_sector_notes(agent):
    rbi = by_source(agent.run_parallel_research("Acme Foods", "food processing"))["RBI"]
    titles = {e["title"] for e in rbi["payload"]["evidence"]}
    assert titles == {"RBI tightens risk weights for food processing loans", "Policy rate unchanged"}
    assert rbi["payload"]["sector_headwind_score"] > 0.3


def test_missing_records_produce_no_signal_not_invented_scores(agent):
    findings = by_source(agent.run_parallel_research("Unknown Borrower Limited", "shipping"))
    assert findings["e-Courts"]["finding_type"] == "no_public_signal"
    assert findings["e-Courts"]["payload"]["litigation_severity_index"] == 0.0
    graph = agent.build_research_graph(list(findings.values()))
    assert graph["litigation_risk"] == 0.0 and graph["promoter_risk"] == 0.0


def test_missing_corpus_is_handled(tmp_path):
    agent = ResearchService(corpus_path=tmp_path / "nope.jsonl")
    findings = agent.run_parallel_research("Acme Foods", "food processing")
    assert agent.corpus_size == 0 and agent.retrieval_method == "none"
    assert len(findings) == len(CONNECTORS)
    assert {f["finding_type"] for f in findings} == {"no_public_signal"}


def test_connector_failure_degrades_to_fallback(agent, monkeypatch):
    original = agent.run_connector

    def flaky(connector, borrower, sector):
        if connector.key == "news":
            raise RuntimeError("upstream unavailable")
        return original(connector, borrower, sector)

    monkeypatch.setattr(agent, "run_connector", flaky)
    findings = by_source(agent.run_parallel_research("Acme Foods", "food processing"))
    assert findings["News"]["finding_type"] == "fallback"
    assert findings["e-Courts"]["finding_type"] == "litigation"
    assert [f["source_name"] for f in agent.run_parallel_research("Acme Foods", "food")] == [c.source_name for c in CONNECTORS]


def test_recency_decay_is_relative_to_newest_signal(agent):
    assert agent.as_of.isoformat() == "2024-06-02"
    assert agent._recency(agent.as_of) == 1.0
    assert agent._recency(agent.as_of.replace(year=2022)) < 0.5


def test_research_is_deterministic(agent):
    strip = lambda findings: [{k: v for k, v in f.items() if k != "payload"} for f in findings]
    assert strip(agent.run_parallel_research("Acme Foods", "food processing")) == strip(
        agent.run_parallel_research("Acme Foods", "food processing")
    )


def test_research_graph_aggregates_maxima(agent):
    graph = agent.build_research_graph([
        {"payload": {"litigation_severity_index": 0.4, "regulatory_alerts": ["b", "a"]}},
        {"payload": {"litigation_severity_index": 0.9, "sector_headwind_score": 0.65, "regulatory_alerts": ["a"]}},
    ])
    assert graph == {"promoter_risk": 0.0, "litigation_risk": 0.9, "sector_headwind": 0.65,
                     "sector_outlook": "negative", "regulatory_alerts": ["a", "b"]}
