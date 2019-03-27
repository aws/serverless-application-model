import boto3
import json
from botocore.exceptions import ClientError, EndpointConnectionError
import logging
from time import sleep, time
import copy

from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.plugins import BasePlugin
from samtranslator.plugins.exceptions import InvalidPluginException
from samtranslator.public.sdk.resource import SamResourceType
from samtranslator.public.sdk.template import SamTemplate
from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.intrinsics.actions import FindInMapAction


class ServerlessAppPlugin(BasePlugin):
    """
    Resolves all of the ApplicationId and Semantic Version pairs
    for AWS::Serverless::Application to template URLs.

    To retrieve a template from the Serverless Application Repository (SAR),
    this plugin needs to call the CreateCloudFormationTemplate API, which
    initiates the process of creating and copying the application template and
    all of its assets from the region it is in to the current region. This
    API returns a pre-signed S3 url that can be passed to CFN. When the template
    reaches ACTIVE status, all assets have been successfully copied and are
    ready to be deployed. This plugin verfies that applications are in an
    ACTIVE state by calling the GetCloudFormation API from SAR.
    """

    SUPPORTED_RESOURCE_TYPE = "AWS::Serverless::Application"
    SLEEP_TIME_SECONDS = 2
    # CloudFormation times out on transforms after 2 minutes, so setting this
    # timeout below that to leave some buffer
    TEMPLATE_WAIT_TIMEOUT_SECONDS = 105
    APPLICATION_ID_KEY = 'ApplicationId'
    SEMANTIC_VERSION_KEY = 'SemanticVersion'
    LOCATION_KEY = 'Location'
    TEMPLATE_URL_KEY = 'TemplateUrl'

    def __init__(self, sar_client=None, wait_for_template_active_status=False, validate_only=False, parameters={}):
        """
        Initialize the plugin.

        Explain that Validate_only uses a different API call, and does not produce a valid template.
        :param boto3.client sar_client: The boto3 client to use to access the Serverless Application Repository
        :param bool wait_for_template_active_status: Flag to wait for all templates to become active
        :param bool validate_only: Flag to only validate application access (uses get_application API instead)
        """
        super(ServerlessAppPlugin, self).__init__(ServerlessAppPlugin.__name__)
        self._applications = {}
        self._in_progress_templates = []
        self._sar_client = sar_client
        self._wait_for_template_active_status = wait_for_template_active_status
        self._validate_only = validate_only
        self._parameters = parameters

        # make sure the flag combination makes sense
        if self._validate_only is True and self._wait_for_template_active_status is True:
            message = "Cannot set both validate_only and wait_for_template_active_status flags to True."
            raise InvalidPluginException(ServerlessAppPlugin.__name__, message)

    def on_before_transform_template(self, template_dict):
        """
        Hook method that gets called before the SAM template is processed.
        The template has passed the validation and is guaranteed to contain a non-empty "Resources" section.

        This plugin needs to run as soon as possible to allow some time for templates to become available.
        This verifies that the user has access to all specified applications.

        :param dict template_dict: Dictionary of the SAM template
        :return: Nothing
        """
        template = SamTemplate(template_dict)
        intrinsic_resolvers = self._get_intrinsic_resolvers(template_dict.get('Mappings', {}))

        service_call = None
        if self._validate_only:
            service_call = self._handle_get_application_request
        else:
            service_call = self._handle_create_cfn_template_request
        for logical_id, app in template.iterate(SamResourceType.Application.value):
            if not self._can_process_application(app):
                # Handle these cases in the on_before_transform_resource event
                continue

            app_id = self._replace_value(app.properties[self.LOCATION_KEY],
                                         self.APPLICATION_ID_KEY, intrinsic_resolvers)

            semver = self._replace_value(app.properties[self.LOCATION_KEY],
                                         self.SEMANTIC_VERSION_KEY, intrinsic_resolvers)

            if isinstance(app_id, dict) or isinstance(semver, dict):
                key = (json.dumps(app_id), json.dumps(semver))
                self._applications[key] = False
                continue

            key = (app_id, semver)

            if key not in self._applications:
                try:
                    # Lazy initialization of the client- create it when it is needed
                    if not self._sar_client:
                        self._sar_client = boto3.client('serverlessrepo')
                    service_call(app_id, semver, key, logical_id)
                except InvalidResourceException as e:
                    # Catch all InvalidResourceExceptions, raise those in the before_resource_transform target.
                    self._applications[key] = e

    def _replace_value(self, input_dict, key, intrinsic_resolvers):
        value = self._resolve_location_value(input_dict.get(key), intrinsic_resolvers)
        input_dict[key] = value
        return value

    def _get_intrinsic_resolvers(self, mappings):
        return [IntrinsicsResolver(self._parameters),
                IntrinsicsResolver(mappings, {FindInMapAction.intrinsic_name: FindInMapAction()})]

    def _resolve_location_value(self, value, intrinsic_resolvers):
        resolved_value = copy.deepcopy(value)
        for intrinsic_resolver in intrinsic_resolvers:
            resolved_value = intrinsic_resolver.resolve_parameter_refs(resolved_value)
        return resolved_value

    def _can_process_application(self, app):
        """
        Determines whether or not the on_before_transform_template event can process this application

        :param dict app: the application and its properties
        """
        return (self.LOCATION_KEY in app.properties and
                isinstance(app.properties[self.LOCATION_KEY], dict) and
                self.APPLICATION_ID_KEY in app.properties[self.LOCATION_KEY] and
                self.SEMANTIC_VERSION_KEY in app.properties[self.LOCATION_KEY])

    def _handle_get_application_request(self, app_id, semver, key, logical_id):
        """
        Method that handles the get_application API call to the serverless application repo

        This method puts something in the `_applications` dictionary because the plugin expects
        something there in a later event.

        :param string app_id: ApplicationId
        :param string semver: SemanticVersion
        :param string key: The dictionary key consisting of (ApplicationId, SemanticVersion)
        :param string logical_id: the logical_id of this application resource
        """
        get_application = (lambda app_id, semver: self._sar_client.get_application(
                                   ApplicationId=self._sanitize_sar_str_param(app_id),
                                   SemanticVersion=self._sanitize_sar_str_param(semver)))
        try:
            self._sar_service_call(get_application, logical_id, app_id, semver)
            self._applications[key] = {'Available'}
        except EndpointConnectionError as e:
            # No internet connection. Don't break verification, but do show a warning.
            warning_message = "{}. Unable to verify access to {}/{}.".format(e, app_id, semver)
            logging.warning(warning_message)
            self._applications[key] = {'Unable to verify'}

    def _handle_create_cfn_template_request(self, app_id, semver, key, logical_id):
        """
        Method that handles the create_cloud_formation_template API call to the serverless application repo

        :param string app_id: ApplicationId
        :param string semver: SemanticVersion
        :param string key: The dictionary key consisting of (ApplicationId, SemanticVersion)
        :param string logical_id: the logical_id of this application resource
        """
        create_cfn_template = (lambda app_id, semver: self._sar_client.create_cloud_formation_template(
            ApplicationId=self._sanitize_sar_str_param(app_id),
            SemanticVersion=self._sanitize_sar_str_param(semver)
        ))
        response = self._sar_service_call(create_cfn_template, logical_id, app_id, semver)
        self._applications[key] = response[self.TEMPLATE_URL_KEY]
        if response['Status'] != "ACTIVE":
            self._in_progress_templates.append((response[self.APPLICATION_ID_KEY], response['TemplateId']))

    def _sanitize_sar_str_param(self, param):
        """
        Sanitize SAR API parameter expected to be a string.

        If customer passes something like 1.0 as SemanticVersion, python
        converts it to a float instead of a basestring, so need to explicitly
        convert it for API calls to SAR that expect a string input.

        :param object param: Parameter to sanitize
        """
        if param is None:
            # str(None) returns 'None' so need to explicitly handle this case
            return None
        return str(param)

    def on_before_transform_resource(self, logical_id, resource_type, resource_properties):
        """
        Hook method that gets called before "each" SAM resource gets processed

        Replaces the ApplicationId and Semantic Version pairs with a TemplateUrl.

        :param string logical_id: Logical ID of the resource being processed
        :param string resource_type: Type of the resource being processed
        :param dict resource_properties: Properties of the resource
        :return: Nothing
        """

        if not self._resource_is_supported(resource_type):
            return

        # Sanitize properties
        self._check_for_dictionary_key(logical_id, resource_properties, [self.LOCATION_KEY])

        # If location isn't a dictionary, don't modify the resource.
        if not isinstance(resource_properties[self.LOCATION_KEY], dict):
            resource_properties[self.TEMPLATE_URL_KEY] = resource_properties[self.LOCATION_KEY]
            return

        # If it is a dictionary, check for other required parameters
        self._check_for_dictionary_key(logical_id, resource_properties[self.LOCATION_KEY],
                                       [self.APPLICATION_ID_KEY, self.SEMANTIC_VERSION_KEY])

        app_id = resource_properties[self.LOCATION_KEY].get(self.APPLICATION_ID_KEY)

        if not app_id:
            raise InvalidResourceException(logical_id, "Property 'ApplicationId' cannot be blank.")

        if isinstance(app_id, dict):
            raise InvalidResourceException(logical_id, "Property 'ApplicationId' cannot be resolved. Only FindInMap "
                                                       "and Ref intrinsic functions are supported.")

        semver = resource_properties[self.LOCATION_KEY].get(self.SEMANTIC_VERSION_KEY)

        if not semver:
            raise InvalidResourceException(logical_id, "Property 'SemanticVersion' cannot be blank.")

        if isinstance(semver, dict):
            raise InvalidResourceException(logical_id, "Property 'SemanticVersion' cannot be resolved. Only FindInMap "
                                                       "and Ref intrinsic functions are supported.")

        key = (app_id, semver)

        # Throw any resource exceptions saved from the before_transform_template event
        if isinstance(self._applications[key], InvalidResourceException):
            raise self._applications[key]

        # validation does not resolve an actual template url
        if not self._validate_only:
            resource_properties[self.TEMPLATE_URL_KEY] = self._applications[key]

    def _check_for_dictionary_key(self, logical_id, dictionary, keys):
        """
        Checks a dictionary to make sure it has a specific key. If it does not, an
        InvalidResourceException is thrown.

        :param string logical_id: logical id of this resource
        :param dict dictionary: the dictionary to check
        :param list keys: list of keys that should exist in the dictionary
        """
        for key in keys:
            if key not in dictionary:
                raise InvalidResourceException(logical_id, 'Resource is missing the required [{}] '
                                                           'property.'.format(key))

    def on_after_transform_template(self, template):
        """
        Hook method that gets called after the template is processed

        Go through all the stored applications and make sure they're all ACTIVE.

        :param dict template: Dictionary of the SAM template
        :return: Nothing
        """
        if self._wait_for_template_active_status and not self._validate_only:
            start_time = time()
            while (time() - start_time) < self.TEMPLATE_WAIT_TIMEOUT_SECONDS:
                temp = self._in_progress_templates
                self._in_progress_templates = []

                # Check each resource to make sure it's active
                for application_id, template_id in temp:
                    get_cfn_template = (lambda application_id, template_id:
                                        self._sar_client.get_cloud_formation_template(
                                            ApplicationId=self._sanitize_sar_str_param(application_id),
                                            TemplateId=self._sanitize_sar_str_param(template_id)))
                    response = self._sar_service_call(get_cfn_template, application_id, application_id, template_id)
                    self._handle_get_cfn_template_response(response, application_id, template_id)

                # Don't sleep if there are no more templates with PREPARING status
                if len(self._in_progress_templates) == 0:
                    break

                # Sleep a little so we don't spam service calls
                sleep(self.SLEEP_TIME_SECONDS)

            # Not all templates reached active status
            if len(self._in_progress_templates) != 0:
                application_ids = [items[0] for items in self._in_progress_templates]
                raise InvalidResourceException(application_ids, "Timed out waiting for nested stack templates "
                                                                "to reach ACTIVE status.")

    def _handle_get_cfn_template_response(self, response, application_id, template_id):
        """
        Handles the response from the SAR service call

        :param dict response: the response dictionary from the app repo
        :param string application_id: the ApplicationId
        :param string template_id: the unique TemplateId for this application
        """
        status = response['Status']
        if status != "ACTIVE":
            # Other options are PREPARING and EXPIRED.
            if status == 'EXPIRED':
                message = ("Template for {} with id {} returned status: {}. Cannot access an expired "
                           "template.".format(application_id, template_id, status))
                raise InvalidResourceException(application_id, message)
            self._in_progress_templates.append((application_id, template_id))

    def _sar_service_call(self, service_call_lambda, logical_id, *args):
        """
        Handles service calls and exception management for service calls
        to the Serverless Application Repository.

        :param lambda service_call_lambda: lambda function that contains the service call
        :param string logical_id: Logical ID of the resource being processed
        :param list *args: arguments for the service call lambda
        """
        try:
            response = service_call_lambda(*args)
            logging.info(response)
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ('AccessDeniedException', 'NotFoundException'):
                raise InvalidResourceException(logical_id, e.response['Error']['Message'])

            # 'ForbiddenException'- SAR rejects connection
            logging.exception(e)
            raise e

    def _resource_is_supported(self, resource_type):
        """
        Is this resource supported by this plugin?

        :param string resource_type: Type of the resource
        :return: True, if this plugin supports this resource. False otherwise
        """
        return resource_type == self.SUPPORTED_RESOURCE_TYPE
