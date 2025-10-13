"""Tests for template entrypoint."""


def test_placeholder_function():
    """Test a function in the entrypoint is callable."""
    from ab_core.template.placeholder import placeholder_func

    assert placeholder_func() is True
