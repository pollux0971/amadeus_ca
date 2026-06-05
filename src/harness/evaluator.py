from __future__ import annotations


def evaluate_criteria(criteria: list[str], evidence: dict[str, bool]) -> list[dict]:
    results = []
    for criterion in criteria:
        results.append({
            "criterion": criterion,
            "passed": bool(evidence.get(criterion, False)),
            "evidence_ref": None,
            "note": "auto-evaluated from evidence map",
        })
    return results


def compute_task_success(criteria_results: list[dict], forbidden_results: list[dict]) -> bool:
    if any(item.get("triggered") for item in forbidden_results):
        return False
    return all(item.get("passed") for item in criteria_results)
