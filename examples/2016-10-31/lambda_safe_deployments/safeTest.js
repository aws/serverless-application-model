'use strict';


exports.handler = (event, context, callback) => {
	console.log("Function loaded! " + context.functionName  +  ":"  +  context.functionVersion);

	callback(null, "Success");
}