from collections import namedtuple
from six import string_types
from samtranslator.model.intrinsics import ref
from samtranslator.model.apigatewayv2 import ApiGatewayV2HttpApi, ApiGatewayV2Stage, ApiGatewayV2Authorizer
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.s3_utils.uri_parser import parse_s3_uri
from samtranslator.open_api.open_api import OpenApiEditor
from samtranslator.translator import logical_id_generator
from samtranslator.model.tags.resource_tagging import get_tag_list

AuthProperties = namedtuple("_AuthProperties", ["Authorizers", "DefaultAuthorizer"])
AuthProperties.__new__.__defaults__ = (None, None)
DefaultStageName = "$default"


class HttpApiGenerator(object):
    def __init__(
        self,
        logical_id,
        stage_variables,
        depends_on,
        definition_body,
        definition_uri,
        stage_name,
        tags=None,
        auth=None,
        access_log_settings=None,
        resource_attributes=None,
        passthrough_resource_attributes=None,
    ):
        """Constructs an API Generator class that generates API Gateway resources

        :param logical_id: Logical id of the SAM API Resource
        :param stage_variables: API Gateway Variables
        :param depends_on: Any resources that need to be depended on
        :param definition_body: API definition
        :param definition_uri: URI to API definition
        :param name: Name of the API Gateway resource
        :param stage_name: Name of the Stage
        :param tags: Stage and API Tags
        :param access_log_settings: Whether to send access logs and where for Stage
        :param resource_attributes: Resource attributes to add to API resources
        :param passthrough_resource_attributes: Attributes such as `Condition` that are added to derived resources
        """
        self.logical_id = logical_id
        self.stage_variables = stage_variables
        self.depends_on = depends_on
        self.definition_body = definition_body
        self.definition_uri = definition_uri
        self.stage_name = stage_name
        if not self.stage_name:
            self.stage_name = DefaultStageName
        self.auth = auth
        self.tags = tags
        self.access_log_settings = access_log_settings
        self.resource_attributes = resource_attributes
        self.passthrough_resource_attributes = passthrough_resource_attributes

    def _construct_http_api(self):
        """Constructs and returns the ApiGatewayV2 HttpApi.

        :returns: the HttpApi to which this SAM Api corresponds
        :rtype: model.apigatewayv2.ApiGatewayHttpApi
        """
        http_api = ApiGatewayV2HttpApi(self.logical_id, depends_on=self.depends_on, attributes=self.resource_attributes)

        if self.definition_uri and self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Specify either 'DefinitionUri' or 'DefinitionBody' property and not both"
            )

        self._add_auth()

        if self.definition_uri:
            http_api.BodyS3Location = self._construct_body_s3_dict()
        elif self.definition_body:
            http_api.Body = self.definition_body
        else:
            raise InvalidResourceException(
                self.logical_id,
                "'DefinitionUri' or 'DefinitionBody' are required properties of an "
                "'AWS::Serverless::HttpApi'. Add a value for one of these properties or "
                "add a 'HttpApi' event to an 'AWS::Serverless::Function'",
            )

        if self.tags is not None:
            http_api.Tags = get_tag_list(self.tags)

        return http_api

    def _add_auth(self):
        """
        Add Auth configuration to the OAS file, if necessary
        """
        if not self.auth:
            return

        if self.auth and not self.definition_body:
            raise InvalidResourceException(
                self.logical_id, "Auth works only with inline Swagger specified in " "'DefinitionBody' property"
            )

        # Make sure keys in the dict are recognized
        if not all(key in AuthProperties._fields for key in self.auth.keys()):
            raise InvalidResourceException(self.logical_id, "Invalid value for 'Auth' property")

        if not OpenApiEditor.is_valid(self.definition_body):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to add Auth configuration because " "'DefinitionBody' does not contain a valid Swagger",
            )
        open_api_editor = OpenApiEditor(self.definition_body)
        auth_properties = AuthProperties(**self.auth)
        authorizers = self._get_authorizers(auth_properties.Authorizers, auth_properties.DefaultAuthorizer)

        # authorizers is guaranteed to return a value or raise an exception
        open_api_editor.add_authorizers_security_definitions(authorizers)
        self._set_default_authorizer(
            open_api_editor, authorizers, auth_properties.DefaultAuthorizer, auth_properties.Authorizers
        )
        self.definition_body = open_api_editor.openapi

    def _set_default_authorizer(self, open_api_editor, authorizers, default_authorizer, api_authorizers):
        """
        Sets the default authorizer if one is given in the template
        :param open_api_editor: editor object that contains the OpenApi definition
        :param authorizers: authorizer definitions converted from the API auth section
        :param default_authorizer: name of the default authorizer
        :param api_authorizers: API auth section authorizer defintions
        """
        if not default_authorizer:
            return

        if not authorizers.get(default_authorizer):
            raise InvalidResourceException(
                self.logical_id,
                "Unable to set DefaultAuthorizer because '" + default_authorizer + "' was not defined in 'Authorizers'",
            )

        for path in open_api_editor.iter_on_path():
            open_api_editor.set_path_default_authorizer(
                path, default_authorizer, authorizers=authorizers, api_authorizers=api_authorizers
            )

    def _get_authorizers(self, authorizers_config, default_authorizer=None):
        """
        Returns all authorizers for an API as an ApiGatewayV2Authorizer object
        :param authorizers_config: authorizer configuration from the API Auth section
        :param default_authorizer: name of the default authorizer
        """
        authorizers = {}

        if not isinstance(authorizers_config, dict):
            raise InvalidResourceException(self.logical_id, "Authorizers must be a dictionary")

        for authorizer_name, authorizer in authorizers_config.items():
            if not isinstance(authorizer, dict):
                raise InvalidResourceException(
                    self.logical_id, "Authorizer %s must be a dictionary." % (authorizer_name)
                )

            authorizers[authorizer_name] = ApiGatewayV2Authorizer(
                api_logical_id=self.logical_id,
                name=authorizer_name,
                open_id_connect_url=authorizer.get("OpenIdConnectUrl"),
                authorization_scopes=authorizer.get("AuthorizationScopes"),
                jwt_configuration=authorizer.get("JwtConfiguration"),
                id_source=authorizer.get("IdentitySource"),
            )
        return authorizers

    def _construct_body_s3_dict(self):
        """
        Constructs the HttpApi's `BodyS3Location property`, from the SAM Api's DefinitionUri property.
        :returns: a BodyS3Location dict, containing the S3 Bucket, Key, and Version of the OpenApi definition
        :rtype: dict
        """
        if isinstance(self.definition_uri, dict):
            if not self.definition_uri.get("Bucket", None) or not self.definition_uri.get("Key", None):
                # DefinitionUri is a dictionary but does not contain Bucket or Key property
                raise InvalidResourceException(
                    self.logical_id, "'DefinitionUri' requires Bucket and Key properties to be specified"
                )
            s3_pointer = self.definition_uri

        else:
            # DefinitionUri is a string
            s3_pointer = parse_s3_uri(self.definition_uri)
            if s3_pointer is None:
                raise InvalidResourceException(
                    self.logical_id,
                    "'DefinitionUri' is not a valid S3 Uri of the form "
                    '"s3://bucket/key" with optional versionId query parameter.',
                )

        body_s3 = {"Bucket": s3_pointer["Bucket"], "Key": s3_pointer["Key"]}
        if "Version" in s3_pointer:
            body_s3["Version"] = s3_pointer["Version"]
        return body_s3

    def _construct_stage(self):
        """Constructs and returns the ApiGatewayV2 Stage.

        :returns: the Stage to which this SAM Api corresponds
        :rtype: model.apigatewayv2.ApiGatewayV2Stage
        """

        # If there are no special configurations, don't create a stage and use the default
        if not self.stage_name and not self.stage_variables and not self.access_log_settings:
            return

        # If StageName is some intrinsic function, then don't prefix the Stage's logical ID
        # This will NOT create duplicates because we allow only ONE stage per API resource
        stage_name_prefix = self.stage_name if isinstance(self.stage_name, string_types) else ""
        if stage_name_prefix.isalnum():
            stage_logical_id = self.logical_id + stage_name_prefix + "Stage"
        elif stage_name_prefix == DefaultStageName:
            stage_logical_id = self.logical_id + "ApiGatewayDefaultStage"
        else:
            generator = logical_id_generator.LogicalIdGenerator(self.logical_id + "Stage", stage_name_prefix)
            stage_logical_id = generator.gen()
        stage = ApiGatewayV2Stage(stage_logical_id, attributes=self.passthrough_resource_attributes)
        stage.ApiId = ref(self.logical_id)
        stage.StageName = self.stage_name
        stage.StageVariables = self.stage_variables
        stage.AccessLogSettings = self.access_log_settings
        stage.AutoDeploy = True

        if self.tags is not None:
            stage.Tags = get_tag_list(self.tags)

        return stage

    def to_cloudformation(self):
        """Generates CloudFormation resources from a SAM API resource

        :returns: a tuple containing the HttpApi and Stage for an empty Api.
        :rtype: tuple
        """
        http_api = self._construct_http_api()

        stage = self._construct_stage()

        return http_api, stage
