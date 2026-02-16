from src.pedigree_builder import load_json_payload, to_gedcom, validate_pedigree


def test_validate_pedigree_success():
    payload = {
        "people": [
            {"id": 1, "name": "A", "gender": "F", "dob": "approx", "conditions": []},
            {"id": 2, "name": "B", "gender": "M", "dob": "1980-01-01", "conditions": ["x"]},
        ],
        "relationships": [{"from": 1, "to": 2, "type": "spouse"}],
    }

    ok, err = validate_pedigree(payload)
    assert ok and err is None


def test_load_json_payload_normalizes_relationship_fields():
    text = '{"people":[{"id":1,"name":"A","gender":"F","dob":"approx","conditions":[]}],"relationships":[]}'
    loaded = load_json_payload(text)
    assert loaded["people"][0]["id"] == 1


def test_gedcom_export_contains_header_and_trailer():
    payload = {
        "people": [{"id": 1, "name": "A", "gender": "F", "dob": "approx", "conditions": []}],
        "relationships": [],
    }
    ged = to_gedcom(payload)
    assert "0 HEAD" in ged
    assert "0 TRLR" in ged
