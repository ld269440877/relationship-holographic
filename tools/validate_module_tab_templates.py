"""Validate the world-class module tab template blueprint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "tasks" / "module_tab_templates.json"
REQUIRED_TAB_FIELDS = {
    "id",
    "label",
    "summary",
    "jobToBeDone",
    "primaryContent",
    "primaryAction",
    "emptyState",
    "qualityGate",
    "fiveW2H",
    "scenarioTemplate",
    "caseStoryTemplate",
    "dialogueTemplate",
    "comparisonTemplate",
    "emotionFlowTemplate",
    "expressionMoves",
    "dataContract",
}
REQUIRED_5W2H = {"why", "what", "who", "when", "where", "how", "howMuch"}
REQUIRED_DIALOGUE = {"theirWords", "weakResponse", "betterResponse"}
REQUIRED_DATA_CONTRACT = {"tables", "requiredFields", "sourcePolicy"}


def validate_template(path: Path = TEMPLATE_PATH) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    modules = data.get("modules")
    if not isinstance(modules, list) or not modules:
        return ["modules must be a non-empty list"]

    for module in modules:
        module_name = str(module.get("name") or module.get("route") or "<unknown>")
        for field in ("route", "name", "responsibility", "uniqueDesign", "tabs"):
            if not module.get(field):
                errors.append(f"{module_name}: missing module field {field}")
        tabs = module.get("tabs")
        if not isinstance(tabs, list) or not tabs:
            errors.append(f"{module_name}: tabs must be non-empty")
            continue
        for tab in tabs:
            tab_name = f"{module_name}/{tab.get('id', '<missing-id>')}"
            missing = sorted(field for field in REQUIRED_TAB_FIELDS if field not in tab or tab.get(field) in (None, "", []))
            if missing:
                errors.append(f"{tab_name}: missing tab fields {', '.join(missing)}")
            _validate_map(tab_name, "fiveW2H", tab.get("fiveW2H"), REQUIRED_5W2H, errors)
            _validate_map(tab_name, "dialogueTemplate", tab.get("dialogueTemplate"), REQUIRED_DIALOGUE, errors)
            _validate_map(tab_name, "dataContract", tab.get("dataContract"), REQUIRED_DATA_CONTRACT, errors)
            if not isinstance(tab.get("expressionMoves"), list) or not tab.get("expressionMoves"):
                errors.append(f"{tab_name}: expressionMoves must be a non-empty list")
    return errors


def _validate_map(name: str, field: str, value: Any, required: set[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name}: {field} must be an object")
        return
    missing = sorted(key for key in required if key not in value or value.get(key) in (None, "", []))
    if missing:
        errors.append(f"{name}: {field} missing {', '.join(missing)}")


def main() -> None:
    errors = validate_template()
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"module tab template ok: {TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
