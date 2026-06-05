import pytest

from src.harness.extension_registry import ExtensionDescriptor, ExtensionRegistry, validate_extension_descriptor


def test_register_and_filter_enabled_extension():
    registry = ExtensionRegistry()
    descriptor = ExtensionDescriptor(
        extension_id="csv_channel",
        category="data_channel",
        entrypoint="src.extensions.csv_channel:CsvChannel",
        enabled=True,
    )
    registry.register(descriptor)
    assert registry.get("csv_channel") == descriptor
    assert registry.enabled() == [descriptor]
    assert registry.by_category("data_channel") == [descriptor]


def test_duplicate_registration_fails():
    registry = ExtensionRegistry()
    descriptor = ExtensionDescriptor("web_console", "interface", "apps.web_console")
    registry.register(descriptor)
    with pytest.raises(ValueError):
        registry.register(descriptor)


def test_high_risk_extension_requires_eval():
    descriptor = ExtensionDescriptor("mic_input", "data_channel", "src.extensions.mic", risk_level="high")
    errors = validate_extension_descriptor(descriptor)
    assert "high risk extensions require evals" in errors
