from unittest.case import skipIf

from integration.config.service_names import ARM, LAYERS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([LAYERS]), "Layers is not supported in this testing region")
class TestBasicLayerVersion(BaseTest):
    """
    Basic AWS::Lambda::LayerVersion tests
    """

    def test_basic_layer_version(self):
        """
        Creates a basic lambda layer version
        """
        self.create_and_verify_stack("single/basic_layer")

        layer_logical_id_1 = self.get_logical_id_by_type("AWS::Lambda::LayerVersion")

        self.set_template_resource_property("MyLayerVersion", "Description", "A basic layer")

        self.update_stack()

        layer_logical_id_2 = self.get_logical_id_by_type("AWS::Lambda::LayerVersion")

        self.assertFalse(layer_logical_id_1 == layer_logical_id_2)

    def test_basic_layer_with_parameters(self):
        """
        Creates a basic lambda layer version with parameters
        """
        self.create_and_verify_stack("single/basic_layer_with_parameters")

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

    @skipIf(current_region_does_not_support([ARM]), "ARM is not supported in this testing region")
    def test_basic_layer_with_architecture(self):
        """
        Creates a basic lambda layer version specifying compatible architecture
        """
        self.create_and_verify_stack("single/basic_layer_with_compatible_architecture")

        outputs = self.get_stack_outputs()
        layer_arn = outputs["MyLayerArn"]
        layer_name = outputs["LayerName"]

        layer_version_result = self.client_provider.lambda_client.get_layer_version_by_arn(Arn=layer_arn)
        self.client_provider.lambda_client.delete_layer_version(
            LayerName=layer_name, VersionNumber=layer_version_result["Version"]
        )
        self.assertEqual(layer_version_result["CompatibleArchitectures"], ["x86_64", "arm64"])
