from collections import namedtuple
from six import string_types

from samtranslator.model.intrinsics import ref
from samtranslator.model.apigateway import (ApiGatewayDeployment, ApiGatewayRestApi,
                                            ApiGatewayStage)
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.s3_utils.uri_parser import parse_s3_uri
from samtranslator.region_configuration import RegionConfiguration
from samtranslator.swagger.swagger import SwaggerEditor
from samtranslator.model.intrinsics import is_instrinsic

_CORS_WILDCARD = "'*'"
CorsProperties = namedtuple("_CorsProperties", ["AllowMethods", "AllowHeaders", "AllowOrigin", "MaxAge"])
# Default the Cors Properties to '*' wildcard. Other properties are actually Optional
CorsProperties.__new__.__defaults__ = (None, None, _CORS_WILDCARD, None)

class ApiGenerator(object):

    def __init__(self, logical_id, cache_cluster_enabled, cache_cluster_size, variables, depends_on, definition_body, definition_uri, name, stage_name, endpoint_configuration=None, method_settings=None, binary_media=None, cors=None):
        """Constructs an API Generator class that generates API Gateway resources

        :param logical_id: Logical id of the SAM API Resource
        :param cache_cluster_enabled: Whether cache cluster is enabled
        :param cache_cluster_size: Size of the cache cluster
        :param variables: API Gateway Variables
        :param depends_on: Any resources that need to be depended on
        :param definition_body: API definition
        :param definition_uri: URI to API definition
        :param name: Name of the API Gateway resource
        :param stage_name: Name of the Stage
        """
        self.logical_id = logical_id
        self.cache_cluster_enabled = cache_cluster_enabled
        self.cache_cluster_size = cache_cluster_size
        self.variables = variables
        self.depends_on = depends_on
        self.definition_body = definition_body
        self.definition_uri = definition_uri
        self.name = name
        self.stage_name = stage_name
        self.endpoint_configuration = endpoint_configuration
        self.method_settings = method_settings
        self.binary_media = binary_media
        self.cors = cors

    def _construct_rest_api(self):
        """Constructs and returns the ApiGateway RestApi.

        :returns: the RestApi to which this SAM Api corresponds
        :rtype: model.apigateway.ApiGatewayRestApi
        """
        rest_api = ApiGatewayRestApi(self.logical_id, depends_on=self.depends_on)
        rest_api.BinaryMediaTypes = self.binary_media

        if self.endpoint_configuration:
            self._set_endpoint_configuration(rest_api, self.endpoint_configuration)

        elif not RegionConfiguration.is_apigw_edge_configuration_supported():
            # Since this region does not support EDGE configuration, we explicitly set the endpoint type
            # to Regional which is the only supported config.
            self._set_endpoint_configuration(rest_api, "REGIONAL")


        if self.definition_uri and self.definition_body:
            raise InvalidResourceException(self.logical_id,
                                           "Specify either 'DefinitionUri' or 'DefinitionBody' property and not both")

        self._add_cors()

        if self.definition_uri:
            rest_api.BodyS3Location = self._construct_body_s3_dict()
        elif self.definition_body:
            rest_api.Body = self.definition_body
        else:
            raise InvalidResourceException(self.logical_id,
                                           "Either 'DefinitionUri' or 'DefinitionBody' property is required")

        if self.name:
            rest_api.Name = self.name

        return rest_api

    def _construct_body_s3_dict(self):
        """Constructs the RestApi's `BodyS3Location property`_, from the SAM Api's DefinitionUri property.

        :returns: a BodyS3Location dict, containing the S3 Bucket, Key, and Version of the Swagger definition
        :rtype: dict
        """
        if isinstance(self.definition_uri, dict):
            if not self.definition_uri.get("Bucket", None) or not self.definition_uri.get("Key", None):
                # DefinitionUri is a dictionary but does not contain Bucket or Key property
                raise InvalidResourceException(self.logical_id,
                                               "'DefinitionUri' requires Bucket and Key properties to be specified")
            s3_pointer = self.definition_uri

        else:

            # DefinitionUri is a string
            s3_pointer = parse_s3_uri(self.definition_uri)
            if s3_pointer is None:
                raise InvalidResourceException(self.logical_id,
                                               '\'DefinitionUri\' is not a valid S3 Uri of the form '
                                               '"s3://bucket/key" with optional versionId query parameter.')

        body_s3 = {
            'Bucket': s3_pointer['Bucket'],
            'Key': s3_pointer['Key']
        }
        if 'Version' in s3_pointer:
            body_s3['Version'] = s3_pointer['Version']
        return body_s3

    def _construct_deployment(self, rest_api):
        """Constructs and returns the ApiGateway Deployment.

        :param model.apigateway.ApiGatewayRestApi rest_api: the RestApi for this Deployment
        :returns: the Deployment to which this SAM Api corresponds
        :rtype: model.apigateway.ApiGatewayDeployment
        """
        deployment = ApiGatewayDeployment(self.logical_id + 'Deployment')
        deployment.RestApiId = rest_api.get_runtime_attr('rest_api_id')
        deployment.StageName = 'Stage'

        return deployment

    def _construct_stage(self, deployment, swagger):
        """Constructs and returns the ApiGateway Stage.

        :param model.apigateway.ApiGatewayDeployment deployment: the Deployment for this Stage
        :returns: the Stage to which this SAM Api corresponds
        :rtype: model.apigateway.ApiGatewayStage
        """

        # If StageName is some intrinsic function, then don't prefix the Stage's logical ID
        # This will NOT create duplicates because we allow only ONE stage per API resource
        stage_name_prefix = self.stage_name if isinstance(self.stage_name, string_types) else ""

        stage = ApiGatewayStage(self.logical_id + stage_name_prefix + 'Stage')
        stage.RestApiId = ref(self.logical_id)
        stage.update_deployment_ref(deployment.logical_id)
        stage.StageName = self.stage_name
        stage.CacheClusterEnabled = self.cache_cluster_enabled
        stage.CacheClusterSize = self.cache_cluster_size
        stage.Variables = self.variables
        stage.MethodSettings = self.method_settings

        if swagger is not None:
            deployment.make_auto_deployable(stage, swagger)

        return stage

    def to_cloudformation(self):
        """Generates CloudFormation resources from a SAM API resource

        :returns: a tuple containing the RestApi, Deployment, and Stage for an empty Api.
        :rtype: tuple
        """

        rest_api = self._construct_rest_api()
        deployment = self._construct_deployment(rest_api)

        swagger = None
        if rest_api.Body is not None:
            swagger = rest_api.Body
        elif rest_api.BodyS3Location is not None:
            swagger = rest_api.BodyS3Location

        stage = self._construct_stage(deployment, swagger)

        return rest_api, deployment, stage

    def _add_cors(self):
        """
        Add CORS configuration to the Swagger file, if necessary
        """

        INVALID_ERROR = "Invalid value for 'Cors' property"

        if not self.cors:
            return

        if self.cors and not self.definition_body:
            raise InvalidResourceException(self.logical_id,
                                           "Cors works only with inline Swagger specified in "
                                           "'DefinitionBody' property")

        if isinstance(self.cors, string_types) or is_instrinsic(self.cors):
            # Just set Origin property. Others will be defaults
            properties = CorsProperties(AllowOrigin=self.cors)
        elif isinstance(self.cors, dict):

            # Make sure keys in the dict are recognized
            if not all(key in CorsProperties._fields for key in self.cors.keys()):
                raise InvalidResourceException(self.logical_id, INVALID_ERROR)

            properties = CorsProperties(**self.cors)

        else:
            raise InvalidResourceException(self.logical_id, INVALID_ERROR)

        if not SwaggerEditor.is_valid(self.definition_body):
            raise InvalidResourceException(self.logical_id, "Unable to add Cors configuration because "
                                                            "'DefinitionBody' does not contain a valid Swagger")

        editor = SwaggerEditor(self.definition_body)
        for path in editor.iter_on_path():
            editor.add_cors(path,  properties.AllowOrigin, properties.AllowHeaders, properties.AllowMethods,
                            max_age=properties.MaxAge)

        # Assign the Swagger back to template
        self.definition_body = editor.swagger

    def _set_endpoint_configuration(self, rest_api, value):
        """
        Sets endpoint configuration property of AWS::ApiGateway::RestApi resource
        :param rest_api: RestApi resource
        :param string/dict value: Value to be set
        """

        rest_api.EndpointConfiguration = {"Types": [value]}
        rest_api.Parameters = {"endpointConfigurationTypes": value}
