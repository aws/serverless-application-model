from unittest.case import skipIf

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestBasicLayerVersion(BaseTest):
    """
    Basic AWS::Lambda::LayerVersion tests
    """

    @skipIf(current_region_does_not_support(["Layers"]), "Layers is not supported in this testing region")
    def test_basic_layer_version(self):
        """
        Creates a basic lambda layer version
        """
        self.create_and_verify_stack("basic_layer")

        layer_logical_id_1 = self.get_logical_id_by_type("AWS::Lambda::LayerVersion")

        self.set_template_resource_property("MyLayerVersion", "Description", "A basic layer")
        self.transform_template()
        self.deploy_stack()

        layer_logical_id_2 = self.get_logical_id_by_type("AWS::Lambda::LayerVersion")

        self.assertFalse(layer_logical_id_1 == layer_logical_id_2)

    @skipIf(current_region_does_not_support(["Layers"]), "Layers is not supported in this testing region")
    def test_basic_layer_with_parameters(self):
        """
        Creates a basic lambda layer version with parameters
        """
        self.create_and_verify_stack("basic_layer_with_parameters")

        outputs = self.get_stack_outputs()
        layer_arn = outputs["MyLayerArn"]
        license = outputs["License"]
        layer_name = outputs["LayerName"]
        description = outputs["Description"]

        layer_version_result = self.client_provider.lambda_client.get_layer_version_by_arn(Arn=layer_arn)
        self.client_provider.lambda_client.delete_layer_version(
            LayerName=layer_name, VersionNumber=layer_version_result["Version"]
        )

        self.assertEqual(layer_version_result["LicenseInfo"], license)
        self.assertEqual(layer_version_result["Description"], description)
