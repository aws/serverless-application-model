'use strict';

console.log('Loading function');


/**
 * AuthPolicy receives a set of allowed and denied methods and generates a valid
 * AWS policy for the API Gateway authorizer. The constructor receives the calling
 * user principal, the AWS account ID of the API owner, and an apiOptions object.
 * The apiOptions can contain an API Gateway RestApi Id, a region for the RestApi, and a
 * stage that calls should be allowed/denied for. For example
 * {
 *   restApiId: 'xxxxxxxxxx,
 *   region: 'us-east-1,
 *   stage: 'dev',
 * }
 *
 * const testPolicy = new AuthPolicy("[principal user identifier]", "[AWS account id]", apiOptions);
 * testPolicy.allowMethod(AuthPolicy.HttpVerb.GET, "/users/username");
 * testPolicy.denyMethod(AuthPolicy.HttpVerb.POST, "/pets");
 * callback(null, testPolicy.build());
 *
 * @class AuthPolicy
 * @constructor
 */
function AuthPolicy(principal, awsAccountId, apiOptions) {
    /**
     * The AWS account id the policy will be generated for. This is used to create
     * the method ARNs.
     *
     * @property awsAccountId
     * @type {String}
     */
    this.awsAccountId = awsAccountId;

    /**
     * The principal used for the policy, this should be a unique identifier for
     * the end user.
     *
     * @property principalId
     * @type {String}
     */
    this.principalId = principal;

    /**
     * The policy version used for the evaluation. This should always be "2012-10-17"
     *
     * @property version
     * @type {String}
     * @default "2012-10-17"
     */
    this.version = '2012-10-17';

    /**
     * The regular expression used to validate resource paths for the policy
     *
     * @property pathRegex
     * @type {RegExp}
     * @default '^\/[/.a-zA-Z0-9-\*]+$'
     */
    this.pathRegex = new RegExp('^[/.a-zA-Z0-9-\*]+$');

    // These are the internal lists of allowed and denied methods. These are lists
    // of objects and each object has two properties: a resource ARN and a nullable
    // conditions statement. The build method processes these lists and generates
    // the appropriate statements for the final policy.
    this.allowMethods = [];
    this.denyMethods = [];

    if (!apiOptions || !apiOptions.restApiId) {
        this.restApiId = '*';
    } else {
        this.restApiId = apiOptions.restApiId;
    }
    if (!apiOptions || !apiOptions.region) {
        this.region = '*';
    } else {
        this.region = apiOptions.region;
    }
    if (!apiOptions || !apiOptions.stage) {
        this.stage = '*';
    } else {
        this.stage = apiOptions.stage;
    }
}

/**
 * A set of existing HTTP verbs supported by API Gateway. This property is here
 * only to avoid spelling mistakes in the policy.
 *
 * @property HttpVerb
 * @type {Object}
 */
AuthPolicy.HttpVerb = {
    GET: 'GET',
    POST: 'POST',
    PUT: 'PUT',
    PATCH: 'PATCH',
    HEAD: 'HEAD',
    DELETE: 'DELETE',
    OPTIONS: 'OPTIONS',
    ALL: '*',
};

AuthPolicy.prototype = (function AuthPolicyClass() {
    /**
     * Adds a method to the internal lists of allowed or denied methods. Each object in
     * the internal list contains a resource ARN and a condition statement. The condition
     * statement can be null.
     *
     * @method addMethod
     * @param {String} The effect for the policy. This can only be "Allow" or "Deny".
     * @param {String} The HTTP verb for the method, this should ideally come from the
     *                 AuthPolicy.HttpVerb object to avoid spelling mistakes
     * @param {String} The resource path. For example "/pets"
     * @param {Object} The conditions object in the format specified by the AWS docs.
     * @return {void}
     */
    function addMethod(effect, verb, resource, conditions) {
        if (verb !== '*' && !Object.prototype.hasOwnProperty.call(AuthPolicy.HttpVerb, verb)) {
            throw new Error(`Invalid HTTP verb ${verb}. Allowed verbs in AuthPolicy.HttpVerb`);
        }

        if (!this.pathRegex.test(resource)) {
            throw new Error(`Invalid resource path: ${resource}. Path should match ${this.pathRegex}`);
        }

        let cleanedResource = resource;
        if (resource.substring(0, 1) === '/') {
            cleanedResource = resource.substring(1, resource.length);
        }
        const resourceArn = `arn:aws:execute-api:${this.region}:${this.awsAccountId}:${this.restApiId}/${this.stage}/${verb}/${cleanedResource}`;

        if (effect.toLowerCase() === 'allow') {
            this.allowMethods.push({
                resourceArn,
                conditions,
            });
        } else if (effect.toLowerCase() === 'deny') {
            this.denyMethods.push({
                resourceArn,
                conditions,
            });
        }
    }

    /**
     * Returns an empty statement object prepopulated with the correct action and the
     * desired effect.
     *
     * @method getEmptyStatement
     * @param {String} The effect of the statement, this can be "Allow" or "Deny"
     * @return {Object} An empty statement object with the Action, Effect, and Resource
     *                  properties prepopulated.
     */
    function getEmptyStatement(effect) {
        const statement = {};
        statement.Action = 'execute-api:Invoke';
        statement.Effect = effect.substring(0, 1).toUpperCase() + effect.substring(1, effect.length).toLowerCase();
        statement.Resource = [];

        return statement;
    }

    /**
     * This function loops over an array of objects containing a resourceArn and
     * conditions statement and generates the array of statements for the policy.
     *
     * @method getStatementsForEffect
     * @param {String} The desired effect. This can be "Allow" or "Deny"
     * @param {Array} An array of method objects containing the ARN of the resource
     *                and the conditions for the policy
     * @return {Array} an array of formatted statements for the policy.
     */
    function getStatementsForEffect(effect, methods) {
        const statements = [];

        if (methods.length > 0) {
            const statement = getEmptyStatement(effect);

            for (let i = 0; i < methods.length; i++) {
                const curMethod = methods[i];
                if (curMethod.conditions === null || curMethod.conditions.length === 0) {
                    statement.Resource.push(curMethod.resourceArn);
                } else {
                    const conditionalStatement = getEmptyStatement(effect);
                    conditionalStatement.Resource.push(curMethod.resourceArn);
                    conditionalStatement.Condition = curMethod.conditions;
                    statements.push(conditionalStatement);
                }
            }

            if (statement.Resource !== null && statement.Resource.length > 0) {
                statements.push(statement);
            }
        }

        return statements;
    }

    return {
        constructor: AuthPolicy,

        /**
         * Adds an allow "*" statement to the policy.
         *
         * @method allowAllMethods
         */
        allowAllMethods() {
            addMethod.call(this, 'allow', '*', '*', null);
        },

        /**
         * Adds a deny "*" statement to the policy.
         *
         * @method denyAllMethods
         */
        denyAllMethods() {
            addMethod.call(this, 'deny', '*', '*', null);
        },

        /**
         * Adds an API Gateway method (Http verb + Resource path) to the list of allowed
         * methods for the policy
         *
         * @method allowMethod
         * @param {String} The HTTP verb for the method, this should ideally come from the
         *                 AuthPolicy.HttpVerb object to avoid spelling mistakes
         * @param {string} The resource path. For example "/pets"
         * @return {void}
         */
        allowMethod(verb, resource) {
            addMethod.call(this, 'allow', verb, resource, null);
        },

        /**
         * Adds an API Gateway method (Http verb + Resource path) to the list of denied
         * methods for the policy
         *
         * @method denyMethod
         * @param {String} The HTTP verb for the method, this should ideally come from the
         *                 AuthPolicy.HttpVerb object to avoid spelling mistakes
         * @param {string} The resource path. For example "/pets"
         * @return {void}
         */
        denyMethod(verb, resource) {
            addMethod.call(this, 'deny', verb, resource, null);
        },

        /**
         * Adds an API Gateway method (Http verb + Resource path) to the list of allowed
         * methods and includes a condition for the policy statement. More on AWS policy
         * conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition
         *
         * @method allowMethodWithConditions
         * @param {String} The HTTP verb for the method, this should ideally come from the
         *                 AuthPolicy.HttpVerb object to avoid spelling mistakes
         * @param {string} The resource path. For example "/pets"
         * @param {Object} The conditions object in the format specified by the AWS docs
         * @return {void}
         */
        allowMethodWithConditions(verb, resource, conditions) {
            addMethod.call(this, 'allow', verb, resource, conditions);
        },

        /**
         * Adds an API Gateway method (Http verb + Resource path) to the list of denied
         * methods and includes a condition for the policy statement. More on AWS policy
         * conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition
         *
         * @method denyMethodWithConditions
         * @param {String} The HTTP verb for the method, this should ideally come from the
         *                 AuthPolicy.HttpVerb object to avoid spelling mistakes
         * @param {string} The resource path. For example "/pets"
         * @param {Object} The conditions object in the format specified by the AWS docs
         * @return {void}
         */
        denyMethodWithConditions(verb, resource, conditions) {
            addMethod.call(this, 'deny', verb, resource, conditions);
        },

        /**
         * Generates the policy document based on the internal lists of allowed and denied
         * conditions. This will generate a policy with two main statements for the effect:
         * one statement for Allow and one statement for Deny.
         * Methods that includes conditions will have their own statement in the policy.
         *
         * @method build
         * @return {Object} The policy object that can be serialized to JSON.
         */
        build() {
            if ((!this.allowMethods || this.allowMethods.length === 0) &&
                    (!this.denyMethods || this.denyMethods.length === 0)) {
                throw new Error('No statements defined for the policy');
            }

            const policy = {};
            policy.principalId = this.principalId;
            const doc = {};
            doc.Version = this.version;
            doc.Statement = [];

            doc.Statement = doc.Statement.concat(getStatementsForEffect.call(this, 'Allow', this.allowMethods));
            doc.Statement = doc.Statement.concat(getStatementsForEffect.call(this, 'Deny', this.denyMethods));

            policy.policyDocument = doc;

            return policy;
        },
    };
}());


exports.handler = (event, context, callback) => {
    // incoming token value
    var token = event.authorizationToken;
    console.log('Method ARN:', event.methodArn);

    // validate the incoming token
    // and produce the principal user identifier associated with the token

    // this could be accomplished in a number of ways:
    // 1. Call out to OAuth provider
    // 2. Decode a JWT token inline
    // 3. Lookup in a self-managed DB
    const principalId = 'user|a1b2c3d4';

    // you can send a 401 Unauthorized response to the client by failing like so:
    // callback('Unauthorized');

    // if the token is valid, a policy must be generated which will allow or deny access to the client

    // if access is denied, the client will recieve a 403 Access Denied response
    // if access is allowed, API Gateway will proceed with the backend integration configured on the method that was called

    // build apiOptions for the AuthPolicy
    const apiOptions = {};
    const tmp = event.methodArn.split(':');
    const apiGatewayArnTmp = tmp[5].split('/');
    const awsAccountId = tmp[4];
    apiOptions.region = tmp[3];
    apiOptions.restApiId = apiGatewayArnTmp[0];
    apiOptions.stage = apiGatewayArnTmp[1];
    /*
    const method = apiGatewayArnTmp[2];
    let resource = '/'; // root resource
    if (apiGatewayArnTmp[3]) {
        resource += apiGatewayArnTmp[3];
    }
    */

    // this function must generate a policy that is associated with the recognized principal user identifier.
    // depending on your use case, you might store policies in a DB, or generate them on the fly

    // keep in mind, the policy is cached for 5 minutes by default (TTL is configurable in the authorizer)
    // and will apply to subsequent calls to any method/resource in the RestApi
    // made with the same token

    // the example policy below denies access to all resources in the RestApi
    const policy = new AuthPolicy(principalId, awsAccountId, apiOptions);
    policy.denyAllMethods();
    // policy.allowMethod(AuthPolicy.HttpVerb.GET, "/users/username");

    // finally, build the policy and exit the function
    const authResponse = policy.build();

    // new! -- add additional key-value pairs
    // these are made available by APIGW like so: $context.authorizer.<key>
    // additional context is cached
    authResponse.context = {
        key: 'value', // $context.authorizer.key -> value
        number: 1,
        bool: true,
    };
    // authResponse.context.arr = ['foo']; <- this is invalid, APIGW will not accept it
    // authResponse.context.obj = {'foo':'bar'}; <- also invalid

    callback(null, authResponse);
};
