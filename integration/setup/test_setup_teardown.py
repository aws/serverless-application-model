import pytest
from integration.helpers.resource import read_test_config_file


@pytest.mark.setup
def test_setup(setup_companion_stack_once, upload_resources, get_s3):
    assert s3_upload_successful()


@pytest.mark.teardown
def test_teardown(delete_companion_stack_once):
    assert True


def s3_upload_successful():
    modified_map = read_test_config_file("file_to_s3_map_modified.json")
    for _, file_info in modified_map.items():
        if not file_info["uri"]:
            return False
    return True
