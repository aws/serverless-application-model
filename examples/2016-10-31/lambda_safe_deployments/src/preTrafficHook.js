'use strict';

const aws = require('aws-sdk');
const codedeploy = new aws.CodeDeploy({apiVersion: '2014-10-06'});

exports.handler = (event, context, callback) => {

	console.log("Entering PreTraffic Hook!");
	console.log(JSON.stringify(event));
	
	//Read the DeploymentId from the event payload.
    var deploymentId = event.DeploymentId;
	console.log(deploymentId);

    //Read the LifecycleEventHookExecutionId from the event payload
	var lifecycleEventHookExecutionId = event.LifecycleEventHookExecutionId;
	console.log(lifecycleEventHookExecutionId);

	/*
		[Perform validation or prewarming steps here]
	*/
	
	// Prepare the validation test results with the deploymentId and
    // the lifecycleEventHookExecutionId for AWS CodeDeploy.
    var params = {
        deploymentId: deploymentId,
        lifecycleEventHookExecutionId: lifecycleEventHookExecutionId,
        status: 'Succeeded' // status can be 'Succeeded' or 'Failed'
    };
	
	// Pass AWS CodeDeploy the prepared validation test results.
    codedeploy.putLifecycleEventHookExecutionStatus(params, function(err, data) {
        if (err) {
			// Validation failed.
			console.log('Validation test failed');
			console.log(err);
			console.log(data);
            callback('Validation test failed');
        } else {
			// Validation succeeded.
			console.log('Validation test succeeded');
            callback(null, 'Validation test succeeded');
        }
	});
}

// See more: https://docs.aws.amazon.com/codedeploy/latest/userguide/reference-appspec-file-structure-hooks.html#reference-appspec-file-structure-hooks-section-structure-lambda-sample-function