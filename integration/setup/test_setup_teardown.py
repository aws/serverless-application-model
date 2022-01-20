import pytest


@pytest.mark.setup
def test_setup(setup_companion_stack_once):
    assert True


@pytest.mark.teardown
def test_teardown(delete_companion_stack_once):
    assert True
