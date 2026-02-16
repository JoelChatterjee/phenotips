"""Pedigree data structures and validation helpers."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

ALLOWED_GENDERS = {"M", "F", "O"}
ALLOWED_RELATIONSHIP_TYPES = {"parent", "child", "sibling", "spouse", "adopted", "uncle", "aunt", "cousin"}


@dataclass
class Person:
    """A single person node in the pedigree graph."""

    id: int
    name: str
    gender: str = "O"
    dob: str = "approx"
    conditions: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    """Directed edge connecting two people with a typed relationship."""

    from_id: int
    to_id: int
    type: str


class PedigreeValidationError(ValueError):
    """Raised when pedigree JSON doesn't match required schema."""


def _is_valid_dob(value: str) -> bool:
    if value == "approx":
        return True
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _normalize_relationship(raw: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "from": raw.get("from", raw.get("from_id")),
        "to": raw.get("to", raw.get("to_id")),
        "type": raw.get("type", "").lower().strip(),
    }
    return normalized


def default_pedigree() -> Dict[str, Any]:
    """Return an empty pedigree payload with required keys."""
    return {"people": [], "relationships": []}


def ensure_unique_ids(people: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Repair duplicate/missing IDs by assigning sequential IDs from 1."""
    repaired = []
    for index, person in enumerate(people, start=1):
        person_copy = copy.deepcopy(person)
        person_copy["id"] = index
        repaired.append(person_copy)
    return repaired


def normalize_pedigree(pedigree: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize field names and formats for downstream processing."""
    normalized = default_pedigree()
    normalized["people"] = ensure_unique_ids(pedigree.get("people", []))

    normalized_relationships = []
    for relationship in pedigree.get("relationships", []):
        normalized_relationship = _normalize_relationship(relationship)
        normalized_relationships.append(normalized_relationship)

    normalized["relationships"] = normalized_relationships
    return normalized


def validate_pedigree(pedigree: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate pedigree payload against the MVP schema."""
    if not isinstance(pedigree, dict):
        return False, "Pedigree must be a JSON object"

    if "people" not in pedigree or "relationships" not in pedigree:
        return False, "Pedigree must include 'people' and 'relationships'"

    person_ids = set()
    for person in pedigree["people"]:
        if not isinstance(person, dict):
            return False, "Each person must be an object"

        required_keys = {"id", "name", "gender", "dob", "conditions"}
        if not required_keys.issubset(person.keys()):
            return False, f"Person missing required keys: {required_keys - set(person.keys())}"

        if not isinstance(person["id"], int):
            return False, "Person id must be an integer"
        person_ids.add(person["id"])

        if person["gender"] not in ALLOWED_GENDERS:
            return False, f"Unsupported gender value: {person['gender']}"

        if not _is_valid_dob(person["dob"]):
            return False, f"Invalid dob: {person['dob']}"

        if not isinstance(person["conditions"], list):
            return False, "conditions must be a list"

    for rel in pedigree["relationships"]:
        normalized_rel = _normalize_relationship(rel)
        if normalized_rel["from"] not in person_ids or normalized_rel["to"] not in person_ids:
            return False, "Relationship references unknown person id"

        if normalized_rel["type"] not in ALLOWED_RELATIONSHIP_TYPES:
            return False, f"Unsupported relationship type: {normalized_rel['type']}"

    return True, None


def load_json_payload(payload: str) -> Dict[str, Any]:
    """Deserialize and validate JSON payload from chat/extraction."""
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise PedigreeValidationError(f"Invalid JSON payload: {exc}") from exc

    normalized = normalize_pedigree(parsed)
    is_valid, error = validate_pedigree(normalized)
    if not is_valid:
        raise PedigreeValidationError(error or "Unknown validation error")
    return normalized


def to_gedcom(pedigree: Dict[str, Any]) -> str:
    """Generate a minimal GEDCOM 5.5 representation from pedigree JSON."""
    lines = ["0 HEAD", "1 GEDC", "2 VERS 5.5"]

    for person in pedigree.get("people", []):
        lines.append(f"0 @I{person['id']}@ INDI")
        lines.append(f"1 NAME {person['name']}")
        sex = person.get("gender", "O")
        lines.append(f"1 SEX {sex if sex in {'M', 'F'} else 'U'}")
        lines.append(f"1 BIRT")
        lines.append(f"2 DATE {person.get('dob', 'approx')}")
        for condition in person.get("conditions", []):
            lines.append("1 NOTE")
            lines.append(f"2 CONT Condition: {condition}")

    family_index = 1
    for rel in pedigree.get("relationships", []):
        rel_type = rel.get("type", "")
        if rel_type in {"spouse", "parent", "child"}:
            lines.append(f"0 @F{family_index}@ FAM")
            if rel_type == "spouse":
                lines.append(f"1 HUSB @I{rel['from']}@")
                lines.append(f"1 WIFE @I{rel['to']}@")
            elif rel_type == "parent":
                lines.append(f"1 HUSB @I{rel['from']}@")
                lines.append(f"1 CHIL @I{rel['to']}@")
            elif rel_type == "child":
                lines.append(f"1 CHIL @I{rel['from']}@")
                lines.append(f"1 HUSB @I{rel['to']}@")
            family_index += 1

    lines.append("0 TRLR")
    return "\n".join(lines)
