from integration.helpers.base_test import BaseTest


class TestFunctionWithIntrinsicsResourceAttributes(BaseTest):
    def test_function_with_intrinsics_resource_attributes(self):
        # simply verify the stack is deployed successfully is enough
        self.create_and_verify_stack("combination/function_with_intrinsics_resource_attribute")

        stack_outputs = self.get_stack_outputs()
        id_dev_stack = stack_outputs["IsDevStack"]
        self.assertEqual(id_dev_stack, "true")
