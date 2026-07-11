from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMES_PATH = BASE_DIR / "data" / "schemes.json"
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")


def is_official_indian_government_url(url: str) -> bool:
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.endswith(OFFICIAL_SUFFIXES)


def load_schemes() -> list[dict]:
    with SCHEMES_PATH.open(encoding="utf-8") as file:
        schemes = json.load(file)

    return [
        scheme
        for scheme in schemes
        if is_official_indian_government_url(str(scheme.get("official_source_url", "")))
    ]


def search_government_schemes(
    query: str,
    state: str | None = None,
    age: str | int | None = None,
    occupation: str | None = None,
    gender: str | None = None,
    annual_income: str | None = None,
    student_status: str | None = None,
    farmer_status: str | None = None,
    disability_status: str | None = None,
) -> str:
    """Search the local official-source-only schemes dataset."""

    profile_terms = [
        query,
        state,
        str(age) if age is not None else None,
        occupation,
        gender,
        annual_income,
        student_status,
        farmer_status,
        disability_status,
    ]
    terms = {
        word.lower()
        for value in profile_terms
        if value
        for word in str(value).replace("-", " ").replace("/", " ").split()
        if len(word) > 2
    }

    results: list[tuple[int, dict]] = []
    for scheme in load_schemes():
        searchable = " ".join(
            str(scheme.get(field, ""))
            for field in (
                "scheme_name",
                "short_description",
                "target_users",
                "eligibility_summary",
                "benefits",
                "keywords",
            )
        ).lower()
        score = sum(1 for term in terms if term in searchable)
        if score > 0:
            results.append((score, scheme))

    results.sort(key=lambda item: item[0], reverse=True)
    selected = [scheme for _, scheme in results[:5]]

    if not selected:
        return json.dumps(
            {
                "message": "No matching local scheme record was found from the official-source dataset.",
                "schemes": [],
            }
        )

    return json.dumps({"schemes": selected}, ensure_ascii=False)
