from tests_integ.helpers.base_test import BaseTest


class TestBasicLayerVersion(BaseTest):

    def test_basic_layer_version(self):
        self.create_and_verify_stack("basic_layer")

        layer_logical_id_1 = self.get_logical_id_by_type("AWS::Lambda::LayerVersion")

        self.set_template_resource_property("MyLayerVersion", "Description", "A basic layer")
        self.transform_template()
        self.deploy_stack()

        layer_logical_id_2 = self.get_logical_id_by_type("AWS::Lambda::LayerVersion")

        self.assertFalse(layer_logical_id_1 == layer_logical_id_2)

    def test_basic_layer_with_parameters(self):
        self.create_and_verify_stack("basic_layer_with_parameters")

        outputs = self.get_stack_outputs()
        layer_arn = outputs["MyLayerArn"]
        license = outputs["License"]
        description = outputs["Description"]

        layer_version_result = self.lambda_client.get_layer_version_by_arn(Arn=layer_arn)

        self.assertEqual(layer_version_result["LicenseInfo"], license)
        self.assertEqual(layer_version_result["Description"], description)

