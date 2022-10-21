### Issue #, if available

### Description of changes

### Description of how you validated changes

### Checklist

- [ ] Add/update [unit tests](https://github.com/aws/serverless-application-model/blob/develop/DEVELOPMENT_GUIDE.md#unit-testing-with-multiple-python-versions) using:
    - [ ] Correct values
    - [ ] Bad/wrong values (None, empty, wrong type, length, etc.)
    - [ ] [Intrinsic Functions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html)
- [ ] Add/update [integration tests](https://github.com/aws/serverless-application-model/blob/develop/INTEGRATION_TESTS.md)
- [ ] Update documentation
- [ ] Verify transformed template deploys and application functions as expected
- [ ] Do these changes include any template validations?
    - [ ] Did the newly validated properties support intrinsics prior to adding the validations? (If unsure, please review [Intrinsic Functions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html) before proceeding).
        - [ ] Does the pull request ensure that intrinsics remain functional with the new validations?

### Examples?

Please reach out in the comments, if you want to add an example. Examples will be 
added to `sam init` through https://github.com/awslabs/aws-sam-cli-app-templates/

By submitting this pull request, I confirm that my contribution is made under the terms of the Apache 2.0 license.
