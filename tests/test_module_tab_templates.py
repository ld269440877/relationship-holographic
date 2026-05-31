from pathlib import Path

from tools.validate_module_tab_templates import validate_template


def test_module_tab_templates_are_worldclass_complete():
    errors = validate_template(Path("docs/tasks/module_tab_templates.json"))
    assert errors == []
