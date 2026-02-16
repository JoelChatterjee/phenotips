from src.analysis_engine import analyze_pedigree
from src.llm_chat import PedigreeChatEngine


def test_llm_fallback_produces_valid_payload():
    engine = PedigreeChatEngine(model_name="non-existent")
    response = engine.process_user_message([], "My mother and father are healthy, and me")
    assert "people" in response.pedigree
    assert isinstance(response.pedigree["people"], list)


def test_analysis_returns_risk_bucket():
    pedigree = {
        "people": [
            {"id": 1, "name": "P1", "gender": "F", "dob": "approx", "conditions": ["condition_a"]},
            {"id": 2, "name": "P2", "gender": "M", "dob": "approx", "conditions": []},
            {"id": 3, "name": "P3", "gender": "O", "dob": "approx", "conditions": ["condition_a"]},
        ],
        "relationships": [
            {"from": 1, "to": 2, "type": "spouse"},
            {"from": 1, "to": 3, "type": "parent"},
            {"from": 3, "to": 1, "type": "child"},
        ],
    }

    result = analyze_pedigree(pedigree)
    assert result.risk_level in {"Low", "Moderate", "High"}
    assert len(result.inheritance_flags) >= 1
